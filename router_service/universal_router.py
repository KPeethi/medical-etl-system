#!/usr/bin/env python3
"""
Medical ETL Universal Router
Enterprise-Lite MVP - File routing service with audit logging
"""

import argparse
import sys
import yaml
import platform
import uuid
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from lib.identity import PatientIdentity
from lib.modules import ModuleResolver
from lib.dedupe import DuplicateDetector
from lib.copier import SafeCopier
from lib.logger import ETLLogger
from lib.security import SecurityManager

VERSION = "1.0.0"

class UniversalRouter:
    def __init__(self, config_path: str, args: argparse.Namespace):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.args = args
        self.run_id = str(uuid.uuid4())
        self.session_key = hashlib.md5(f"{self.run_id}{datetime.utcnow()}".encode()).hexdigest()
        
        self.src_root = Path(args.src).resolve()
        self.dst_root = Path(args.dst).resolve()
        self.log_dir = Path(args.log).resolve() if args.log else Path('./logs')
        
        roster_path = self.config.get('identity', {}).get('roster', {}).get('path')
        self.identity_resolver = PatientIdentity(roster_path=roster_path, config=self.config)
        self.module_resolver = ModuleResolver(config=self.config)
        self.dedupe_detector = DuplicateDetector(policy=self.config.get('dedupe_policy', 'same_size_same_module'))
        self.copier = SafeCopier()
        self.security = SecurityManager()
        
        db_url = self.args.db_url if hasattr(self.args, 'db_url') else None
        self.logger = ETLLogger(
            csv_dir=str(self.log_dir),
            run_id=self.run_id,
            session_key=self.session_key,
            db_url=db_url,
            enable_redaction=self.config.get('logging', {}).get('redaction', True)
        )
        
        self.config_hash = hashlib.sha256(str(self.config).encode()).hexdigest()[:16]
        self.stats = {'processed': 0, 'copied': 0, 'skipped': 0, 'unmapped': 0, 'errors': 0}
    
    def discover_files(self, root_path: Path, max_depth: int = 12) -> List[Path]:
        """Recursively discover files"""
        files = []
        include_exts = set(self.config.get('include_exts', []))
        exclude_exts = set(self.config.get('exclude_exts', []))
        
        def scan_dir(path: Path, depth: int):
            if depth > max_depth:
                return
            
            try:
                for item in path.iterdir():
                    if item.is_file():
                        ext = item.suffix.lower()
                        if (not include_exts or ext in include_exts) and ext not in exclude_exts:
                            files.append(item)
                    elif item.is_dir():
                        scan_dir(item, depth + 1)
            except PermissionError:
                pass
        
        scan_dir(root_path, 0)
        return files
    
    def process_file(self, file_path: Path, nested_level: int):
        """Process a single file"""
        self.stats['processed'] += 1
        
        try:
            rel_path = file_path.relative_to(self.src_root)
            folder_path = str(file_path.parent)
            
            patient = None
            patient = self.identity_resolver.identify_from_filename(file_path.name, folder_path)
            
            if patient:
                roster_match = self.identity_resolver.match_to_roster(
                    patient.get('last', ''),
                    patient.get('first', ''),
                    patient.get('dob')
                )
                if roster_match:
                    patient = roster_match
            
            if not patient:
                self._log_unmapped(file_path, rel_path, nested_level, "No patient identity found")
                return
            
            if not patient.get('dob') or patient['dob'] == '1900-01-01':
                self._log_bad_dob(file_path, rel_path, patient, nested_level)
                return
            
            module = self.module_resolver.resolve_module(str(file_path), folder_path)
            
            file_size = file_path.stat().st_size
            quick_hash, full_hash = self.security.compute_file_hash(
                str(file_path),
                self.config.get('performance', {}).get('quick_hash_bytes')
            )
            
            patient_key = f"{patient['last']}_{patient['first']}_{patient.get('dob', '')}"
            is_dup, dup_reason = self.dedupe_detector.check_duplicate(
                str(file_path), patient_key, module, file_size, quick_hash, full_hash
            )
            
            if is_dup:
                self._log_event(file_path, rel_path, patient, module, file_size, full_hash,
                               nested_level, 'SKIP_DUP', dup_reason, None)
                self.stats['skipped'] += 1
                return
            
            patient_folder = self.identity_resolver.format_patient_folder(patient)
            dst_patient_dir = self.dst_root / patient_folder / module
            
            success, dst_path, message = self.copier.safe_copy(
                str(file_path),
                str(dst_patient_dir),
                dry_run=self.args.dry_run
            )
            
            if success:
                self._log_event(file_path, rel_path, patient, module, file_size, full_hash,
                               nested_level, 'COPY', message, dst_path)
                self.stats['copied'] += 1
            else:
                self._log_event(file_path, rel_path, patient, module, file_size, full_hash,
                               nested_level, 'ERROR', message, None)
                self.stats['errors'] += 1
        
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Error processing {file_path}: {e}")
    
    def _log_event(self, file_path, rel_path, patient, module, file_size, full_hash, 
                   nested_level, action, reason, dst_path):
        """Log a processing event"""
        event = {
            'invoked_by_user': self.args.user if hasattr(self.args, 'user') else 'system',
            'host_platform': platform.system(),
            'python_version': platform.python_version(),
            'script_version': VERSION,
            'mode': 'DRY_RUN' if self.args.dry_run else 'REAL',
            'practice_id': self.config.get('practice_id'),
            'src_root': str(self.src_root),
            'dst_root': str(self.dst_root),
            'src_path': str(file_path),
            'rel_path': str(rel_path),
            'dst_path': dst_path or '',
            'nested_level': nested_level,
            'action': action,
            'reason': reason,
            'last': patient.get('last', ''),
            'first': patient.get('first', ''),
            'dob': patient.get('dob', ''),
            'module': module,
            'file_ext': file_path.suffix,
            'file_size_bytes': file_size,
            'sha256_full': full_hash,
            'provenance_id': str(uuid.uuid4()),
            'config_hash': self.config_hash
        }
        self.logger.log_event(event)
    
    def _log_unmapped(self, file_path, rel_path, nested_level, reason):
        """Log unmapped file"""
        event = {
            'invoked_by_user': self.args.user if hasattr(self.args, 'user') else 'system',
            'host_platform': platform.system(),
            'python_version': platform.python_version(),
            'script_version': VERSION,
            'mode': 'DRY_RUN' if self.args.dry_run else 'REAL',
            'practice_id': self.config.get('practice_id'),
            'src_root': str(self.src_root),
            'dst_root': str(self.dst_root),
            'src_path': str(file_path),
            'rel_path': str(rel_path),
            'nested_level': nested_level,
            'action': 'MOVE_TO_UNMAPPED',
            'reason': reason,
            'file_ext': file_path.suffix,
            'file_size_bytes': file_path.stat().st_size,
            'provenance_id': str(uuid.uuid4()),
            'config_hash': self.config_hash
        }
        self.logger.log_event(event)
        self.stats['unmapped'] += 1
    
    def _log_bad_dob(self, file_path, rel_path, patient, nested_level):
        """Log file with bad DOB"""
        event = {
            'invoked_by_user': self.args.user if hasattr(self.args, 'user') else 'system',
            'host_platform': platform.system(),
            'python_version': platform.python_version(),
            'script_version': VERSION,
            'mode': 'DRY_RUN' if self.args.dry_run else 'REAL',
            'practice_id': self.config.get('practice_id'),
            'src_root': str(self.src_root),
            'dst_root': str(self.dst_root),
            'src_path': str(file_path),
            'rel_path': str(rel_path),
            'nested_level': nested_level,
            'action': 'MOVE_TO_BAD_DOB',
            'reason': f"Invalid DOB: {patient.get('dob')}",
            'last': patient.get('last', ''),
            'first': patient.get('first', ''),
            'file_ext': file_path.suffix,
            'file_size_bytes': file_path.stat().st_size,
            'provenance_id': str(uuid.uuid4()),
            'config_hash': self.config_hash
        }
        self.logger.log_event(event)
        self.stats['unmapped'] += 1
    
    def run(self):
        """Main execution"""
        print(f"=== Medical ETL Universal Router v{VERSION} ===")
        print(f"Run ID: {self.run_id}")
        print(f"Session: {self.session_key}")
        print(f"Mode: {'DRY RUN' if self.args.dry_run else 'REAL RUN'}")
        print(f"Source: {self.src_root}")
        print(f"Destination: {self.dst_root}")
        print(f"Practice: {self.config.get('practice_id')}")
        print()
        
        print("Discovering files...")
        files = self.discover_files(self.src_root, self.config.get('max_depth', 12))
        
        total_files = len(files)
        if self.args.canary and self.args.canary < total_files:
            files = files[:self.args.canary]
            print(f"CANARY MODE: Processing first {len(files)} of {total_files} files")
        else:
            print(f"Found {total_files} files to process")
        
        print()
        for idx, file_path in enumerate(files, 1):
            if idx % 100 == 0:
                print(f"Processed {idx}/{len(files)} files...")
            self.process_file(file_path, 0)
        
        summary = self.logger.get_summary()
        print()
        print("=== Run Summary ===")
        print(f"Total files: {self.stats['processed']}")
        print(f"Copied: {self.stats['copied']}")
        print(f"Skipped (duplicates): {self.stats['skipped']}")
        print(f"Unmapped: {self.stats['unmapped']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Log file: {summary['csv_path']}")

def main():
    parser = argparse.ArgumentParser(description='Medical ETL Universal Router')
    parser.add_argument('--src', required=True, help='Source directory')
    parser.add_argument('--dst', required=True, help='Destination directory')
    parser.add_argument('--config', required=True, help='Configuration YAML file')
    parser.add_argument('--log', help='Log directory (default: ./logs)')
    parser.add_argument('--db-url', help='Database URL for SQL logging')
    parser.add_argument('--user', default='system', help='Invoking user')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no actual copying)')
    parser.add_argument('--real', dest='dry_run', action='store_false', help='Real run mode')
    parser.add_argument('--canary', type=int, help='Canary mode: process only first N files')
    parser.set_defaults(dry_run=True)
    
    args = parser.parse_args()
    
    router = UniversalRouter(args.config, args)
    router.run()

if __name__ == '__main__':
    main()
