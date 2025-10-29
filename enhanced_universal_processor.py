#!/usr/bin/env python3
"""
Enhanced Universal Medical File Processor with OCR
Includes: Roster Matching → Filename Patterns → Folder Cues → OCR → Unmapped
Flat structure: Module_filename.ext
"""

import os
import re
import csv
import sys
import argparse
import logging
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
import uuid

# Import OCR processor if available
try:
    from ocr_processor import MedicalOCRProcessor
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

class EnhancedUniversalProcessor:
    """Enhanced medical file processor with OCR capabilities"""
    
    def __init__(self, source_path, dest_path, roster_path=None, config_path=None, log_path=None):
        self.source_path = Path(source_path)
        self.dest_path = Path(dest_path)
        self.roster_path = Path(roster_path) if roster_path else None
        self.config_path = Path(config_path) if config_path else None
        self.log_path = Path(log_path) if log_path else self.dest_path
        
        # Initialize OCR processor if available
        self.ocr_processor = None
        if OCR_AVAILABLE:
            try:
                self.ocr_processor = MedicalOCRProcessor()
                logging.info("✅ OCR processor initialized")
            except Exception as e:
                logging.warning(f"OCR initialization failed: {e}")
        
        # Load roster if provided
        self.roster = self._load_roster() if self.roster_path else []
        
        # Processing stats - CORRECTED ORDER
        self.stats = {
            'total_files': 0,
            'mapping_matched': 0,     # Step 1: Roster/Mapping
            'folder_matched': 0,      # Step 2: Folder Cues  
            'filename_matched': 0,    # Step 3: Filename Patterns
            'ocr_matched': 0,         # Step 4: OCR Processing
            'unmapped': 0,            # Step 5: Unmapped
            'errors': 0
        }
        
        # Create log file
        self.log_file = self._setup_logging()
        
        # Filename patterns (comprehensive)
        self.filename_patterns = [
            # Standard patterns
            r'([A-Z][a-z]+)[_,\s]+([A-Z][a-z]+)[_,\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'([A-Z][a-z]+)[_,\s]+([A-Z][a-z]+)[_,\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            
            # Reversed patterns  
            r'([A-Z][a-z]+)[_,\s]+([A-Z][a-z]+)',  # Name only
            
            # Special formats
            r'([A-Z]+)[,\s]+([A-Z])[,\s]+([A-Z]+)',  # DOE,J,LAB format
        ]
        
        # Date normalization patterns
        self.date_patterns = [
            r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',  # MM-DD-YYYY
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{2})',  # MM-DD-YY
        ]

    def _load_roster(self):
        """Load patient roster from CSV/Excel"""
        if not self.roster_path or not self.roster_path.exists():
            return []
        
        try:
            if self.roster_path.suffix.lower() == '.csv':
                with open(self.roster_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    return list(reader)
            else:
                # Excel file
                import pandas as pd
                df = pd.read_excel(self.roster_path)
                return df.to_dict('records')
        except Exception as e:
            logging.error(f"Failed to load roster: {e}")
            return []

    def _setup_logging(self):
        """Setup CSV logging in specified log path"""
        session_id = str(uuid.uuid4())
        log_file = self.log_path / f"processing_log_{session_id[:8]}.csv"
        
        # Create log directory
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write CSV header
        with open(log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'source_file', 'dest_file', 'action', 
                'patient_last', 'patient_first', 'patient_dob', 
                'detection_method', 'confidence', 'module', 'notes'
            ])
        
        return log_file

    def _log_action(self, source_file, dest_file, action, patient_info=None, 
                   method='unknown', confidence=0, module='unknown', notes=''):
        """Log processing action to CSV"""
        try:
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    str(source_file),
                    str(dest_file) if dest_file else '',
                    action,
                    patient_info.get('last', '') if patient_info else '',
                    patient_info.get('first', '') if patient_info else '',
                    patient_info.get('dob', '') if patient_info else '',
                    method,
                    confidence,
                    module,
                    notes
                ])
        except Exception as e:
            logging.error(f"Failed to log action: {e}")

    def process_dataset(self, dry_run=True):
        """Process the entire dataset with enhanced detection"""
        
        print(f"🔄 Processing: {self.source_path}")
        print(f"📁 Output: {self.dest_path}")
        print(f"📋 Roster: {len(self.roster)} patients" if self.roster else "📋 No roster provided")
        print(f"🔍 OCR: {'Enabled' if self.ocr_processor else 'Disabled'}")
        print(f"🧪 Mode: {'DRY RUN' if dry_run else 'LIVE PROCESSING'}")
        print("-" * 60)
        
        # Discover files
        files = self._discover_files()
        self.stats['total_files'] = len(files)
        
        print(f"📂 Found {len(files)} files to process")
        
        # Process each file
        for file_path in files:
            try:
                self._process_single_file(file_path, dry_run)
            except Exception as e:
                logging.error(f"Error processing {file_path}: {e}")
                self.stats['errors'] += 1
        
        # Print final statistics
        self._print_results()
        
        return self.stats

    def _discover_files(self):
        """Discover all files to process"""
        files = []
        
        if self.source_path.is_file():
            if self.source_path.suffix.lower() == '.zip':
                # Extract ZIP and get files
                files = self._extract_zip_files()
            else:
                files = [self.source_path]
        else:
            # Directory - find all files
            for file_path in self.source_path.rglob('*'):
                if file_path.is_file():
                    files.append(file_path)
        
        return files

    def _extract_zip_files(self):
        """Extract ZIP file and return list of extracted files"""
        extract_dir = self.dest_path / "temp_extract"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        files = []
        try:
            with zipfile.ZipFile(self.source_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Find all extracted files
            for file_path in extract_dir.rglob('*'):
                if file_path.is_file():
                    files.append(file_path)
        except Exception as e:
            logging.error(f"Failed to extract ZIP: {e}")
        
        return files

    def _process_single_file(self, file_path, dry_run):
        """Process a single file through CORRECTED detection pipeline"""
        
        filename = file_path.name
        print(f"Processing: {filename}")
        
        # Step 1: Mapping/Roster matching (highest priority)
        patient_info = self._try_roster_matching(file_path)
        if patient_info:
            self.stats['mapping_matched'] += 1
            self._organize_file(file_path, patient_info, 'mapping_match', 0.9, dry_run)
            return
        
        # Step 2: Folder structure cues
        patient_info = self._try_folder_cues(file_path)
        if patient_info:
            self.stats['folder_matched'] += 1
            self._organize_file(file_path, patient_info, 'folder_cues', 0.8, dry_run)
            return
        
        # Step 3: Filename pattern matching
        patient_info = self._try_filename_patterns(file_path)
        if patient_info:
            self.stats['filename_matched'] += 1
            self._organize_file(file_path, patient_info, 'filename_pattern', 0.7, dry_run)
            return
        
        # Step 4: OCR processing (if available and PDF)
        if self.ocr_processor and file_path.suffix.lower() == '.pdf':
            patient_info = self._try_ocr_processing(file_path)
            if patient_info and patient_info.get('confidence', 0) > 0.5:
                self.stats['ocr_matched'] += 1
                self._organize_file(file_path, patient_info, 'ocr_scan', 
                                  patient_info.get('confidence', 0.5), dry_run)
                return
        
        # Step 5: Send to unmapped
        self._send_to_unmapped(file_path, dry_run)
        self.stats['unmapped'] += 1

    def _try_roster_matching(self, file_path):
        """Try to match file against patient roster"""
        if not self.roster:
            return None
        
        # Extract name/DOB from filename
        filename_info = self._extract_info_from_filename(file_path.name)
        if not filename_info:
            return None
        
        # Match against roster
        for patient in self.roster:
            if self._names_match(filename_info, patient):
                return self._normalize_patient_info(patient)
        
        return None

    def _try_filename_patterns(self, file_path):
        """Try to extract patient info from filename patterns"""
        return self._extract_info_from_filename(file_path.name)

    def _try_folder_cues(self, file_path):
        """Try to extract patient info from folder structure"""
        # Check parent folder names for patient info
        for parent in file_path.parents:
            folder_info = self._extract_info_from_filename(parent.name)
            if folder_info:
                return folder_info
        return None

    def _try_ocr_processing(self, file_path):
        """Try OCR processing on PDF files"""
        if not self.ocr_processor:
            return None
        
        try:
            return self.ocr_processor.extract_patient_from_pdf(str(file_path), max_pages=20)
        except Exception as e:
            logging.error(f"OCR failed for {file_path}: {e}")
            return None

    def _extract_info_from_filename(self, filename):
        """Extract patient info from filename using patterns"""
        
        for pattern in self.filename_patterns:
            match = re.search(pattern, filename)
            if match:
                groups = match.groups()
                
                if len(groups) >= 2:
                    patient_info = {
                        'last': groups[0].title(),
                        'first': groups[1].title(),
                        'dob': self._normalize_date(groups[2]) if len(groups) > 2 else 'unknown'
                    }
                    return patient_info
        
        return None

    def _normalize_date(self, date_str):
        """Normalize date to YYYY-MM-DD format"""
        
        for pattern in self.date_patterns:
            match = re.search(pattern, date_str)
            if match:
                groups = match.groups()
                
                if len(groups) == 3:
                    # Determine date format and convert
                    if len(groups[0]) == 4:  # YYYY format
                        return f"{groups[0]}-{groups[1]:0>2}-{groups[2]:0>2}"
                    else:  # MM-DD-YYYY or MM-DD-YY
                        year = groups[2]
                        if len(year) == 2:
                            year = "20" + year if int(year) < 50 else "19" + year
                        return f"{year}-{groups[0]:0>2}-{groups[1]:0>2}"
        
        return date_str

    def _names_match(self, filename_info, roster_patient):
        """Check if filename info matches roster patient"""
        # Simple name matching (can be enhanced)
        return (filename_info.get('last', '').lower() == 
                roster_patient.get('last_name', '').lower() and
                filename_info.get('first', '').lower() == 
                roster_patient.get('first_name', '').lower())

    def _normalize_patient_info(self, patient_data):
        """Normalize patient info to standard format"""
        return {
            'last': patient_data.get('last_name', patient_data.get('last', '')),
            'first': patient_data.get('first_name', patient_data.get('first', '')),
            'dob': patient_data.get('dob', patient_data.get('date_of_birth', 'unknown'))
        }

    def _organize_file(self, source_file, patient_info, method, confidence, dry_run):
        """Organize file into flat patient folder structure"""
        
        # Create patient folder name: LastName, FirstName MM-DD-YYYY
        dob_formatted = self._format_dob_for_folder(patient_info.get('dob', 'unknown'))
        patient_folder = f"{patient_info['last']}, {patient_info['first']} {dob_formatted}"
        
        # Detect module/category
        module = self._detect_module(source_file)
        
        # Create flat filename: Module_originalname.ext
        original_name = source_file.name
        new_filename = f"{module}_{original_name}"
        
        # Destination path
        dest_dir = self.dest_path / patient_folder
        dest_file = dest_dir / new_filename
        
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, dest_file)
        
        print(f"  → {patient_folder}/{new_filename}")
        
        # Log action
        self._log_action(
            source_file, dest_file, 'COPY_FLAT' if not dry_run else 'DRY_RUN',
            patient_info, method, confidence, module
        )

    def _send_to_unmapped(self, source_file, dry_run):
        """Send file to unmapped folder"""
        
        unmapped_dir = self.dest_path / "_UNMAPPED_FILES"
        dest_file = unmapped_dir / source_file.name
        
        if not dry_run:
            unmapped_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, dest_file)
        
        print(f"  → _UNMAPPED_FILES/{source_file.name}")
        
        # Log action
        self._log_action(
            source_file, dest_file, 'MOVE_TO_UNMAPPED' if not dry_run else 'DRY_RUN_UNMAPPED',
            notes='No patient identification possible'
        )

    def _format_dob_for_folder(self, dob):
        """Format DOB for folder name (MM-DD-YYYY)"""
        if dob == 'unknown':
            return 'UNKNOWN-DOB'
        
        try:
            # Parse various date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y']:
                try:
                    date_obj = datetime.strptime(dob, fmt)
                    return date_obj.strftime('%m-%d-%Y')
                except ValueError:
                    continue
        except:
            pass
        
        return dob

    def _detect_module(self, file_path):
        """Detect file module/category"""
        
        filename = file_path.name.lower()
        
        # Module keywords
        module_keywords = {
            'Laboratory': ['lab', 'blood', 'urine', 'pathology', 'cbc'],
            'Imaging': ['xray', 'ct', 'mri', 'scan', 'ultrasound', 'radio'],
            'Clinical_Notes': ['note', 'progress', 'visit', 'encounter', 'consult'],
            'Reports': ['report', 'summary', 'discharge', 'operative'],
            'Billing': ['bill', 'statement', 'invoice', 'payment'],
            'Insurance': ['insurance', 'claim', 'auth', 'eob']
        }
        
        for module, keywords in module_keywords.items():
            if any(keyword in filename for keyword in keywords):
                return module
        
        return 'Medical_Records'  # Default

    def _print_results(self):
        """Print processing results"""
        
        total = self.stats['total_files']
        if total == 0:
            print("No files processed.")
            return
        
        print("\n" + "=" * 60)
        print("📊 PROCESSING RESULTS - CORRECTED ORDER")
        print("=" * 60)
        print(f"📂 Total Files: {total}")
        print(f"🎯 Step 1 - Mapping Matched: {self.stats['mapping_matched']} ({self.stats['mapping_matched']/total*100:.1f}%)")
        print(f"� Step 2 - Folder Matched: {self.stats['folder_matched']} ({self.stats['folder_matched']/total*100:.1f}%)")
        print(f"� Step 3 - Filename Matched: {self.stats['filename_matched']} ({self.stats['filename_matched']/total*100:.1f}%)")
        print(f"🔍 Step 4 - OCR Matched: {self.stats['ocr_matched']} ({self.stats['ocr_matched']/total*100:.1f}%)")
        print(f"❓ Step 5 - Unmapped: {self.stats['unmapped']} ({self.stats['unmapped']/total*100:.1f}%)")
        print(f"❌ Errors: {self.stats['errors']}")
        
        success_rate = (total - self.stats['unmapped'] - self.stats['errors']) / total * 100
        print(f"\n🎯 Overall Success Rate: {success_rate:.1f}%")
        print(f"📋 Log File: {self.log_file}")

def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description='Enhanced Medical File Processor with OCR')
    parser.add_argument('--source', required=True, help='Source path (file or directory)')
    parser.add_argument('--dest', required=True, help='Destination directory')
    parser.add_argument('--roster', help='Patient roster CSV/Excel file')
    parser.add_argument('--log', help='Log directory path (optional)')
    parser.add_argument('--config', help='Configuration file (not implemented yet)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (default)')
    parser.add_argument('--live', action='store_true', help='Live processing mode')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Determine processing mode
    dry_run = not args.live
    
    try:
        processor = EnhancedUniversalProcessor(
            args.source,
            args.dest,
            args.roster,
            args.config,
            args.log
        )
        
        stats = processor.process_dataset(dry_run=dry_run)
        
        print(f"\n✅ Processing complete! Check: {args.dest}")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()