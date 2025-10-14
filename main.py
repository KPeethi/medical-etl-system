"""
CLI Orchestrator for Medical ETL.
Supports two modes:
- Mapping mode: Provide mapping Excel/CSV/JSON with id/firstname/
    lastname/dob (synonyms allowed)
- No-mapping mode: Auto-parse filenames/folders/OCR to extract
    patient data

Always copies (never moves) files to destination. Source remains
untouched. Organizes as: "Lastname, Firstname MM-DD-YYYY".
Duplicates to /duplicates. Unmapped to /unmapped.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Package-relative imports
from medical_etl_system.modules.etl_logger_simple import ETLLogger
from medical_etl_system.modules.ocr_processor import OCRProcessor
from medical_etl_system.modules.patient_parser import PatientParser
from medical_etl_system.modules.file_extractor import FileExtractor
from medical_etl_system.modules.duplicate_detector import DuplicateDetector
from medical_etl_system.modules.file_organizer import FileOrganizer
from medical_etl_system.modules.mapping_processor import MappingProcessor
from medical_etl_system.config.config import Config


class MedicalETL:
    def __init__(self, source: Path, dest: Path,
                 mapping: Optional[Path] = None,
                 dry_run: bool = False) -> None:
        self.config = Config()
        Config.ensure_directories()

        self.source = source
        self.dest = dest
        self.mapping = mapping
        self.dry_run = dry_run

        run_type = Config.DRY_RUN_MODE if dry_run else Config.REAL_RUN_MODE
        self.logger = ETLLogger(
            run_type,
            Config.LOG_LEVEL,
            str(source),
            Config.MAX_LOG_SIZE_MB,
        )

        self.extractor = FileExtractor()
        self.ocr = OCRProcessor()
        self.parser = PatientParser()
        self.mapper = MappingProcessor()
        if mapping and mapping.exists():
            self.mapper.load_mapping_files(single_mapping_file=mapping)
        else:
            self.mapper.load_mapping_files()
        self.dups = DuplicateDetector()
        self.organizer = FileOrganizer(dest)

        self.results: Dict[str, Any] = {
            'total_files_found': 0,
            'total_files_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'mapped_files': 0,
            'unmapped_files': 0,
            'duplicate_files': 0,
            'organized_files': 0,
            'errors': [],
            'warnings': []
        }

    def validate(self) -> bool:
        if not self.source.exists():
            self.logger.log_error(
                'Input Validation', f'Source does not exist: {self.source}'
            )
            return False
        if not self.dry_run:
            self.dest.mkdir(parents=True, exist_ok=True)
        return True

    def discover(self) -> List[Tuple[Path, Path]]:
        # Use FileExtractor to walk directories and return supported files
        files = self.extractor.extract_all_files(self.source)
        self.results['total_files_found'] = len(files)
        if not files:
            self.logger.log_warning(
                'Discovery', f'No files found in {self.source}'
            )
        # Auto-load mapping files from any extracted directories
        try:
            # Gather unique extracted temp dirs from extractor
            extracted_dirs = [
                p for p in self.extractor.extracted_files
                if p.exists()
            ]
            if extracted_dirs:
                self.mapper.load_mapping_from_directories(extracted_dirs)
        except Exception as e:
            self.logger.log_warning('Mapping', f'Auto-load skipped: {e}')
        return files

    def process_file(
        self, file_path: Path, original_path: Path
    ) -> Optional[Dict[str, Any]]:
        try:
            file_info = self.extractor.get_file_info(file_path)
            op = self.logger.log_file_processing_start(
                str(original_path), file_info, None
            )

            result: Dict[str, Any] = {
                'operation_id': op,
                'file_path': file_path,
                'original_path': original_path,
                'file_info': file_info,
                'patient_data': {},
                'success': False
            }

            # 1) Smart lookup from mapping (if available)
            m = self.mapper.smart_patient_lookup(file_path)
            if m.get('found'):
                result['patient_data'] = m['patient_info']
                self.results['mapped_files'] += 1

            # 2) If still not enough, parse filename
            if not result['patient_data']:
                parsed = self.parser.parse_filename(file_path.name)
                if parsed:
                    result['patient_data'] = parsed

            # 3) If still not enough, do basic OCR (best-effort)
            if not result['patient_data'] and (
                self.config.is_image_file(file_path)
                or self.config.is_pdf_file(file_path)
            ):
                ocr = self.ocr.extract_text_from_file(file_path, max_pages=2)
                if ocr.get('success'):
                    parsed = self.parser.parse_ocr_text(ocr)
                    if parsed:
                        result['patient_data'] = parsed

            result['success'] = True
            self.results['successful_extractions'] += 1
            self.results['total_files_processed'] += 1
            self.logger.log_file_processing_end(op, result)
            return result
        except Exception as e:
            self.results['failed_extractions'] += 1
            self.results['errors'].append(str(e))
            return None

    def run(self) -> Dict[str, Any]:
        if not self.validate():
            return self.results

        files = self.discover()
        processed: List[Dict[str, Any]] = []
        for fp, orig in files:
            r = self.process_file(fp, orig)
            if r:
                processed.append(r)

        # duplicate detection
        for r in processed:
            if r.get('success'):
                self.dups.add_file(
                    r['file_path'],
                    r.get('patient_data', {}),
                    r['original_path'],
                )
        groups = self.dups.detect_duplicates()
    # Build a set of exact duplicate file paths (except first keep)
        duplicate_paths = set()
        for grp in groups.get('exact_duplicates', []):
            for p, s, n in grp[1:]:  # skip first (keep original)
                duplicate_paths.add(str(p))
        exact_count = sum(
            max(len(g) - 1, 0) for g in groups.get('exact_duplicates', [])
        )
        pot_count = sum(
            max(len(g) - 1, 0) for g in groups.get('potential_duplicates', [])
        )
        self.results['duplicate_files'] = exact_count + pot_count

        # organize
        for r in processed:
            # Extra safety: never organize archive files
            try:
                fp = r['file_path']
                if self.config.is_archive_file(fp):
                    continue
            except Exception:
                pass
            is_dup = str(r['file_path']) in duplicate_paths
            dest_res = self.organizer.organize_file(
                r['file_path'], r.get('patient_data', {}), is_dup, self.dry_run
            )
            if dest_res.get('success'):
                self.results['organized_files'] += 1

        # finalize
        session = {
            'total_files_processed': self.results['total_files_processed'],
            'successful_extractions': self.results['successful_extractions'],
            'organized_files': self.results['organized_files'],
            'patients': {},
            'processing_results': self.results
        }
        self.logger.finalize_session(session)
        return self.results


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Medical ETL System')
    p.add_argument('source', help='Source directory or file')
    p.add_argument('dest', help='Destination directory')
    p.add_argument('--mapping', '-m', help='Mapping file (Excel/CSV/JSON)')
    p.add_argument(
        '--dry-run', '-d', action='store_true', help='Dry run (no copy)'
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    source = Path(args.source)
    dest = Path(args.dest)
    mapping = Path(args.mapping) if args.mapping else None
    etl = MedicalETL(source, dest, mapping, args.dry_run)
    res = etl.run()
    print('ETL summary:')
    keys = [
        'total_files_found',
        'total_files_processed',
        'successful_extractions',
        'failed_extractions',
        'mapped_files',
        'unmapped_files',
        'duplicate_files',
        'organized_files',
    ]
    for k in keys:
        print(f"  {k}: {res.get(k, 0)}")


if __name__ == '__main__':
    main()
