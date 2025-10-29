#!/usr/bin/env python3
"""
UNIVERSAL MEDICAL FILE PROCESSOR

TL;DR: This tool is universal and portable. No hardcoded paths or column mappings.
Pass a source location (folder or ZIP), and the app auto-discovers files and
infers patient identity from filenames/folders. If roster/mapping isn't provided,
system explicitly sets mapping: "none" and continues with filename/folder parsing.

Expected Behavior:
- No hardcoded paths (all from user input)
- Optional mapping/roster (fallback to filename parsing if not provided)
- Universal input (directory or ZIP, any file types, any date formats)
- Source is read-only (never modify originals)
- Dry-run first option available
"""

import argparse
import csv
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import hashlib


class UniversalMedicalProcessor:
    """Universal medical file processor with no hardcoded assumptions"""
    
    def __init__(self):
        self.mapping_mode = "none"
        self.roster_data = {}
        self.column_aliases = {}
        self.stats = {
            "files_discovered": 0,
            "matched_patients": 0,
            "unmapped": 0,
            "duplicates": 0,
            "errors": 0
        }
        self.logs = []
        self.temp_dirs = []
        self.discovered_files = []
        
    def process_dataset(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing function following the universal spec
        
        Args:
            config: {
                "source": path to input folder or ZIP,
                "dest": path to output folder,
                "dry_run": boolean,
                "roster": optional path to CSV/XLSX,
                "mapping": optional path to JSON aliases,
                "options": optional settings dict
            }
        """
        try:
            # Validate inputs
            source_path = Path(config["source"])
            dest_path = Path(config["dest"])
            dry_run = config.get("dry_run", True)
            roster_path = config.get("roster")
            mapping_path = config.get("mapping")
            options = config.get("options", {})
            
            if not source_path.exists():
                return {
                    "status": "error",
                    "message": f"Source path not found: {source_path}"
                }
            
            # Initialize processing
            self._setup_logging(dest_path)
            self._load_configuration(roster_path, mapping_path)
            
            # Discover files
            discovery_result = self._discover_files(source_path)
            
            # Process files
            processing_result = self._process_files(
                discovery_result["files"], 
                dest_path, 
                dry_run, 
                options
            )
            
            # Generate response
            return {
                "status": "ok",
                "mapping_mode": self.mapping_mode,
                "discovery": discovery_result,
                "matched_patients": self.stats["matched_patients"],
                "unmapped": self.stats["unmapped"],
                "duplicates": self.stats["duplicates"],
                "dry_run": dry_run,
                "logs": {
                    "summary_csv": str(self.log_file),
                    "details_csv": str(self.detail_log_file)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "mapping_mode": self.mapping_mode
            }
        finally:
            self._cleanup_temp_dirs()
    
    def _setup_logging(self, dest_path: Path):
        """Setup log files"""
        log_dir = dest_path / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.log_file = log_dir / f"run_{timestamp}_summary.csv"
        self.detail_log_file = log_dir / f"run_{timestamp}_events.csv"
        
        # Initialize CSV files
        with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "event", "source_file", "patient_match", 
                "mapping_mode", "confidence", "reason"
            ])
        
        with open(self.detail_log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "source_path", "dest_path", "action", 
                "patient_last", "patient_first", "patient_dob", 
                "file_type", "file_size", "content_hash"
            ])
    
    def _load_configuration(self, roster_path: Optional[str], mapping_path: Optional[str]):
        """Load roster and mapping if provided, otherwise set mapping_mode to 'none'"""
        
        # Handle mapping
        if mapping_path:
            if Path(mapping_path).exists():
                try:
                    with open(mapping_path, 'r', encoding='utf-8') as f:
                        self.column_aliases = json.load(f)
                    self.mapping_mode = "file_provided"
                    self._log_event("mapping_loaded", mapping_path, "", "file", 1.0, "mapping file loaded successfully")
                except Exception as e:
                    self.mapping_mode = "file_missing"
                    self._log_event("mapping_error", mapping_path, "", "error", 0.0, f"mapping not found at {mapping_path}. Falling back to auto alias detection.")
            else:
                self.mapping_mode = "file_missing"
                self._log_event("mapping_missing", mapping_path or "none", "", "error", 0.0, f"mapping not found at {mapping_path}. Falling back to auto alias detection.")
        else:
            self.mapping_mode = "none"
            self._log_event("mapping_none", "none", "", "info", 1.0, "mapping_mode set to 'none'. Proceeding with filename/folder inference.")
        
        # Handle roster
        if roster_path:
            if Path(roster_path).exists():
                try:
                    self.roster_data = self._load_roster_file(roster_path)
                    self._log_event("roster_loaded", roster_path, "", "file", 1.0, f"roster loaded with {len(self.roster_data)} patients")
                except Exception as e:
                    self._log_event("roster_error", roster_path, "", "error", 0.0, f"Could not read roster {roster_path}. Continuing in filename-only mode.")
            else:
                self._log_event("roster_missing", roster_path, "", "error", 0.0, f"roster_status: 'unavailable' — Could not read roster {roster_path}. Continuing in filename-only mode.")
        else:
            self._log_event("roster_none", "none", "", "info", 1.0, "No roster provided. Using filename/folder inference only.")
    
    def _load_roster_file(self, roster_path: str) -> Dict[str, Dict]:
        """Load roster file with auto-detection of column names"""
        import pandas as pd
        
        path = Path(roster_path)
        if path.suffix.lower() == '.xlsx':
            df = pd.read_excel(roster_path)
        else:
            df = pd.read_csv(roster_path, encoding='utf-8')
        
        # Auto-detect column names using aliases and common patterns
        column_map = self._detect_roster_columns(df.columns.tolist())
        
        roster = {}
        for _, row in df.iterrows():
            try:
                last_name = str(row[column_map['last_name']]).strip()
                first_name = str(row[column_map['first_name']]).strip()
                dob_raw = str(row[column_map['dob']]).strip()
                
                # Normalize DOB
                dob_normalized = self._normalize_date(dob_raw)
                if not dob_normalized or dob_normalized in ["01-01-1900", "1900-01-01"]:
                    continue  # Skip placeholder DOBs
                
                # Create patient key
                patient_key = f"{last_name}_{first_name}_{dob_normalized}".lower()
                roster[patient_key] = {
                    'last_name': last_name,
                    'first_name': first_name,
                    'dob': dob_normalized,
                    'dob_raw': dob_raw
                }
            except (KeyError, ValueError):
                continue
        
        return roster
    
    def _detect_roster_columns(self, columns: List[str]) -> Dict[str, str]:
        """Auto-detect roster column names using aliases and patterns"""
        
        # Default aliases (can be overridden by mapping file)
        default_aliases = {
            'last_name': ['lastname', 'last_name', 'surname', 'family_name', 'lname', 'last'],
            'first_name': ['firstname', 'first_name', 'given_name', 'fname', 'first', 'givenname'],
            'dob': ['dob', 'date_of_birth', 'birthdate', 'birth_date', 'born', 'dateofbirth']
        }
        
        # Use mapping file aliases if available
        if self.column_aliases:
            aliases = self.column_aliases
        else:
            aliases = default_aliases
        
        column_map = {}
        columns_lower = [col.lower() for col in columns]
        
        for field, possible_names in aliases.items():
            for possible_name in possible_names:
                if possible_name.lower() in columns_lower:
                    idx = columns_lower.index(possible_name.lower())
                    column_map[field] = columns[idx]
                    break
        
        return column_map
    
    def _discover_files(self, source_path: Path) -> Dict[str, Any]:
        """Discover all files in source (handling ZIP extraction)"""
        
        self.discovered_files = []  # Store files for processing
        zip_expanded = 0
        
        if source_path.is_file() and source_path.suffix.lower() == '.zip':
            # Extract ZIP to temporary directory
            temp_dir = tempfile.mkdtemp()
            self.temp_dirs.append(temp_dir)
            
            with zipfile.ZipFile(source_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            zip_expanded = 1
            self._log_event("zip_detected", str(source_path), "", "info", 1.0, "Expanding zip to temp workspace (read-only source preserved)")
            
            # Scan extracted files
            for root, dirs, file_list in os.walk(temp_dir):
                for file_name in file_list:
                    file_path = Path(root) / file_name
                    if self._is_medical_file(file_path):
                        self.discovered_files.append(file_path)
        
        elif source_path.is_dir():
            # Scan directory
            for root, dirs, file_list in os.walk(source_path):
                for file_name in file_list:
                    file_path = Path(root) / file_name
                    if self._is_medical_file(file_path):
                        self.discovered_files.append(file_path)
        
        self.stats["files_discovered"] = len(self.discovered_files)
        
        return {
            "files": len(self.discovered_files),
            "zip_expanded": zip_expanded,
            "discovery_mode": "zip" if zip_expanded else "directory"
        }
    
    def _is_medical_file(self, file_path: Path) -> bool:
        """Check if file is a medical file (any relevant extension)"""
        medical_extensions = {
            '.pdf', '.doc', '.docx', '.txt', '.rtf',
            '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp',
            '.xml', '.json', '.csv', '.xlsx',
            '.dcm', '.dicom'  # Medical imaging
        }
        return file_path.suffix.lower() in medical_extensions
    
    def _process_files(self, file_count: int, dest_path: Path, dry_run: bool, options: Dict) -> Dict[str, Any]:
        """Process discovered files"""
        
        # Get actual file list (this is a simplification - in real implementation
        # we'd pass the actual file list from discovery)
        files = self._get_discovered_files()
        
        if not files:
            self._log_event("no_files", "", "", "error", 0.0, "No medical files found in source")
            return {"processed": 0}
        
        # Process each file
        for file_path in files:
            try:
                self._process_single_file(file_path, dest_path, dry_run, options)
            except Exception as e:
                self.stats["errors"] += 1
                self._log_event("error", str(file_path), "", "error", 0.0, f"Processing error: {str(e)}")
        
        # Check if no matches found
        if self.stats["matched_patients"] == 0:
            self._log_event("no_matches", "", "", "warning", 0.0, "inference_status: 'no_matches' — Unable to extract name/DOB from provided files. Provide a roster or adjust filename patterns.")
        
        return {"processed": len(files)}
    
    def _get_discovered_files(self) -> List[Path]:
        """Get the actual discovered files"""
        return getattr(self, 'discovered_files', [])
    
    def _process_single_file(self, file_path: Path, dest_path: Path, dry_run: bool, options: Dict):
        """Process a single file through the detection pipeline"""
        
        # Detection Order:
        # 1. Roster Match (if provided)
        # 2. Filename/Folder Inference (always available)
        
        patient_match = None
        confidence = 0.0
        detection_method = "none"
        
        # Try roster match first
        if self.roster_data:
            patient_match, confidence = self._match_to_roster(file_path)
            if patient_match:
                detection_method = "roster"
        
        # Fallback to filename inference
        if not patient_match:
            patient_match, confidence = self._infer_from_filename(file_path)
            if patient_match:
                detection_method = "filename"
        
        # Handle result
        if patient_match and confidence > 0.5:
            self._route_file(file_path, patient_match, dest_path, dry_run, detection_method)
            self.stats["matched_patients"] += 1
        else:
            self._route_unmapped_file(file_path, dest_path, dry_run)
            self.stats["unmapped"] += 1
        
        # Log the event
        self._log_detailed_event(file_path, patient_match, detection_method, confidence, dry_run)
    
    def _match_to_roster(self, file_path: Path) -> Tuple[Optional[Dict], float]:
        """Try to match file to roster patient"""
        
        # Extract patient info from filename
        extracted = self._extract_patient_info(file_path.name)
        if not extracted:
            return None, 0.0
        
        last_name, first_name, dob = extracted
        
        # Try to find in roster
        patient_key = f"{last_name}_{first_name}_{dob}".lower()
        if patient_key in self.roster_data:
            return self.roster_data[patient_key], 1.0
        
        # Try fuzzy matching (simplified)
        for key, patient in self.roster_data.items():
            if (patient['last_name'].lower() == last_name.lower() and 
                patient['first_name'].lower() == first_name.lower()):
                return patient, 0.8
        
        return None, 0.0
    
    def _infer_from_filename(self, file_path: Path) -> Tuple[Optional[Dict], float]:
        """Infer patient from filename patterns"""
        
        extracted = self._extract_patient_info(file_path.name)
        if not extracted:
            return None, 0.0
        
        last_name, first_name, dob = extracted
        
        # Create synthetic patient record
        patient = {
            'last_name': last_name,
            'first_name': first_name,
            'dob': dob or "unknown",
            'source': 'filename_inference'
        }
        
        confidence = 0.9 if dob else 0.7  # Lower confidence if no DOB
        return patient, confidence
    
    def _extract_patient_info(self, filename: str) -> Optional[Tuple[str, str, Optional[str]]]:
        """Extract patient info from filename using multiple patterns"""
        
        patterns = [
            # Pattern 1: Lastname_Firstname_YYYY-MM-DD_*
            r'([A-Za-z\'-]+)_([A-Za-z\'-]+)_(\d{4}-\d{2}-\d{2})',
            
            # Pattern 2: Firstname Lastname - module (MM/DD/YYYY)
            r'([A-Za-z\'-]+)\s+([A-Za-z\'-]+)\s*-.*\((\d{2}/\d{2}/\d{4})\)',
            
            # Pattern 3: DOE,J,LAB_04221988.*
            r'([A-Za-z]+),([A-Za-z]),.*_(\d{8})',
            
            # Pattern 4: lastname firstname MM-DD-YYYY
            r'([A-Za-z\'-]+)\s+([A-Za-z\'-]+)\s+(\d{2}-\d{2}-\d{4})',
            
            # Pattern 5: MRN prefix
            r'MRN\d+_([A-Za-z\'-]+)_([A-Za-z\'-]+)_(\d{4}-\d{2}-\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 3:
                    last_name = match.group(1).strip()
                    first_name = match.group(2).strip()
                    dob_raw = match.group(3).strip()
                    
                    # Normalize DOB
                    dob_normalized = self._normalize_date(dob_raw)
                    
                    return last_name, first_name, dob_normalized
        
        return None
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date to YYYY-MM-DD format"""
        if not date_str or date_str.lower() in ['unknown', 'none', '']:
            return None
        
        # Remove common separators and try different formats
        clean_date = re.sub(r'[^\d]', '', date_str)
        
        if len(clean_date) == 8:  # MMDDYYYY or YYYYMMDD
            if clean_date[:4].isdigit() and int(clean_date[:4]) > 1900:
                # YYYYMMDD
                return f"{clean_date[:4]}-{clean_date[4:6]}-{clean_date[6:8]}"
            else:
                # MMDDYYYY
                return f"{clean_date[4:8]}-{clean_date[:2]}-{clean_date[2:4]}"
        
        # Try common date patterns
        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
            r'(\d{2})/(\d{2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{2})-(\d{2})-(\d{4})',  # MM-DD-YYYY
            r'(\d{4})/(\d{2})/(\d{2})',  # YYYY/MM/DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                if len(match.group(1)) == 4:  # Year first
                    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                else:  # Month first
                    return f"{match.group(3)}-{match.group(1)}-{match.group(2)}"
        
        return None
    
    def _route_file(self, file_path: Path, patient: Dict, dest_path: Path, dry_run: bool, method: str):
        """Route file to patient folder"""
        
        # Create patient folder name
        last_name = patient['last_name']
        first_name = patient['first_name']
        dob = patient.get('dob', 'unknown')
        
        patient_folder = f"{last_name}, {first_name} {dob}"
        patient_dir = dest_path / "organized" / patient_folder
        
        if not dry_run:
            patient_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            dest_file = patient_dir / file_path.name
            shutil.copy2(file_path, dest_file)
        
        self._log_event("matched", str(file_path), str(patient_dir / file_path.name), method, 1.0, f"Matched via {method}")
    
    def _route_unmapped_file(self, file_path: Path, dest_path: Path, dry_run: bool):
        """Route unmapped file to unmapped folder"""
        
        unmapped_dir = dest_path / "unmapped"
        
        if not dry_run:
            unmapped_dir.mkdir(parents=True, exist_ok=True)
            dest_file = unmapped_dir / file_path.name
            shutil.copy2(file_path, dest_file)
        
        self._log_event("unmapped", str(file_path), str(unmapped_dir / file_path.name), "none", 0.0, "Could not identify patient")
    
    def _log_event(self, event: str, source: str, dest: str, method: str, confidence: float, reason: str):
        """Log an event to the summary log"""
        
        timestamp = datetime.now().isoformat()
        
        with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, event, source, dest, self.mapping_mode, confidence, reason
            ])
    
    def _log_detailed_event(self, file_path: Path, patient: Optional[Dict], method: str, confidence: float, dry_run: bool):
        """Log detailed processing event"""
        
        timestamp = datetime.now().isoformat()
        
        # Get file info
        file_size = file_path.stat().st_size if file_path.exists() else 0
        content_hash = self._get_file_hash(file_path) if file_path.exists() else ""
        
        patient_last = patient['last_name'] if patient else ""
        patient_first = patient['first_name'] if patient else ""
        patient_dob = patient.get('dob', '') if patient else ""
        
        action = "DRY_RUN" if dry_run else "COPY"
        
        with open(self.detail_log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, str(file_path), "", action,
                patient_last, patient_first, patient_dob,
                file_path.suffix, file_size, content_hash
            ])
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get SHA-256 hash of file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()[:16]  # First 16 chars
        except:
            return ""
    
    def _cleanup_temp_dirs(self):
        """Clean up temporary directories"""
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(description='Universal Medical File Processor - No hardcoded paths, optional mapping, smart fallbacks')
    
    parser.add_argument('--source', required=False, help='Source folder or ZIP file')
    parser.add_argument('--dest', required=False, help='Destination folder')
    parser.add_argument('--dry-run', action='store_true', help='Enable dry run mode')
    parser.add_argument('--no-dry-run', action='store_true', help='Disable dry run mode')
    parser.add_argument('--roster', help='Optional path to roster CSV/XLSX')
    parser.add_argument('--mapping', help='Optional path to column mapping JSON')
    
    args = parser.parse_args()
    
    # Interactive mode if no args provided
    if not args.source:
        print("🌟 Universal Medical File Processor")
        print("No hardcoded paths - fully portable and universal")
        print()
        
        source = input("Enter source path (folder or ZIP): ").strip()
        if not source:
            print("❌ Source path required")
            sys.exit(1)
        
        dest = input("Enter destination path: ").strip()
        if not dest:
            print("❌ Destination path required")
            sys.exit(1)
        
        dry_run_input = input("Dry run? (y/N): ").strip().lower()
        dry_run = dry_run_input in ['y', 'yes', 'true']
        
        roster = input("Roster file (optional, press Enter to skip): ").strip() or None
        mapping = input("Mapping file (optional, press Enter to skip): ").strip() or None
        
    else:
        source = args.source
        dest = args.dest
        dry_run = args.dry_run if not args.no_dry_run else False
        roster = args.roster
        mapping = args.mapping
    
    # Build config
    config = {
        "source": source,
        "dest": dest,
        "dry_run": dry_run,
        "roster": roster,
        "mapping": mapping,
        "options": {
            "duplicate_policy": "size_and_module",
            "output_root_style": "container",
            "skip_placeholder_dobs": ["01-01-1900", "1900-01-01"]
        }
    }
    
    # Process
    processor = UniversalMedicalProcessor()
    result = processor.process_dataset(config)
    
    # Display results
    print("\n🎉 PROCESSING COMPLETE")
    print("=" * 50)
    print(f"Status: {result['status']}")
    print(f"Mapping Mode: {result.get('mapping_mode', 'unknown')}")
    
    if result['status'] == 'ok':
        print(f"Files Discovered: {result['discovery']['files']}")
        print(f"Matched Patients: {result['matched_patients']}")
        print(f"Unmapped Files: {result['unmapped']}")
        print(f"Duplicates: {result['duplicates']}")
        print(f"Dry Run: {result['dry_run']}")
        print()
        print("📊 Log Files:")
        print(f"  Summary: {result['logs']['summary_csv']}")
        print(f"  Details: {result['logs']['details_csv']}")
    else:
        print(f"Error: {result['message']}")
    
    print("\n✨ Universal processing complete - no hardcoded paths used!")


if __name__ == '__main__':
    main()