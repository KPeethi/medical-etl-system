#!/usr/bin/env python3
"""
WORKING UNIVERSAL MEDICAL PROCESSOR

This is the working version that actually processes your files and creates organized folders.
"""

import argparse
import csv
import os
import re
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class WorkingUniversalProcessor:
    """Working universal processor that actually organizes files"""
    
    def __init__(self, roster_path: str = None, mapping_path: str = None):
        self.roster_path = roster_path
        self.mapping_path = mapping_path
        self.roster_data = {}
        self.mapping_data = {}
        self.stats = {
            "files_discovered": 0,
            "mapping_matched": 0,
            "folder_matched": 0,
            "filename_matched": 0,
            "ocr_matched": 0,
            "unmapped": 0,
            "duplicates": 0
        }
        self.temp_dirs = []
        self._load_roster_data()
        self._load_mapping_data()
        self._setup_ocr_processor()

    def _load_roster_data(self):
        """Load roster data if provided"""
        if self.roster_path and os.path.exists(self.roster_path):
            try:
                import pandas as pd
                df = pd.read_csv(self.roster_path)
                for _, row in df.iterrows():
                    key = str(row.get('id', '')).strip().lower()
                    if key:
                        self.roster_data[key] = {
                            'first_name': str(row.get('first_name', '')),
                            'last_name': str(row.get('last_name', '')),
                            'dob': str(row.get('dob', ''))
                        }
                print(f"📊 Loaded {len(self.roster_data)} roster entries")
            except Exception as e:
                print(f"⚠️ Warning: Could not load roster: {e}")

    def _load_mapping_data(self):
        """Load mapping data if provided"""
        if self.mapping_path and os.path.exists(self.mapping_path):
            try:
                import pandas as pd
                df = pd.read_csv(self.mapping_path)
                for _, row in df.iterrows():
                    filename = str(row.get('filename', '')).strip()
                    if filename:
                        self.mapping_data[filename] = {
                            'first_name': str(row.get('first_name', '')),
                            'last_name': str(row.get('last_name', '')),
                            'dob': str(row.get('dob', ''))
                        }
                print(f"📊 Loaded {len(self.mapping_data)} mapping entries")
            except Exception as e:
                print(f"⚠️ Warning: Could not load mapping: {e}")

    def _setup_ocr_processor(self):
        """Setup OCR processor if available"""
        try:
            # Import the existing OCR processor
            sys.path.append(str(Path(__file__).parent))
            from ocr_processor import MedicalOCRProcessor
            self.ocr_processor = MedicalOCRProcessor()
            print("🔍 OCR processor initialized")
        except ImportError:
            try:
                # Try importing from modules directory
                sys.path.append(str(Path(__file__).parent / "modules"))
                from ocr_processor import OCRProcessor
                self.ocr_processor = OCRProcessor()
                print("🔍 OCR processor (modules) initialized")
            except ImportError:
                self.ocr_processor = None
                print("⚠️ OCR processor not available")
        
    def process_dataset(self, source_path: str, dest_path: str,
                        dry_run: bool = True):
        """Process medical dataset with universal detection"""
        
        print("🚀 Universal Medical File Processor")
        print(f"📁 Source: {source_path}")
        print(f"📁 Destination: {dest_path}")
        print(f"🔄 Mode: {'DRY RUN' if dry_run else 'LIVE PROCESSING'}")
        print(f"📊 Roster: {len(self.roster_data)} entries")
        print(f"📋 Mapping: {len(self.mapping_data)} entries")
        print()
        
        try:
            source = Path(source_path)
            dest = Path(dest_path)
            
            if not source.exists():
                print(f"❌ Source path not found: {source_path}")
                return False
            
            # Setup output directories
            if not dry_run:
                dest.mkdir(parents=True, exist_ok=True)
                (dest / "organized").mkdir(exist_ok=True)
                (dest / "unmapped").mkdir(exist_ok=True)
                (dest / "logs").mkdir(exist_ok=True)
            
            # Discover files
            files = self._discover_files(source)
            print(f"📄 Found {len(files)} medical files to process")
            
            if not files:
                print("❌ No medical files found")
                return False
            
            # Process files using the correct workflow:
            # Mapping → Folder → Filename → OCR → Unmapped
            for file_path in files:
                patient_info = self._process_single_file(file_path)
                
                if patient_info:
                    method, last_name, first_name, dob = patient_info
                    patient_folder = f"{last_name}, {first_name} " + \
                                   f"{dob or 'unknown'}"
                    
                    print(f"✅ [{method}] {file_path.name} → {patient_folder}")
                    
                    if not dry_run:
                        patient_dir = dest / "organized" / patient_folder
                        patient_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, patient_dir / file_path.name)
                    
                    # Update stats based on method
                    if method == "MAPPING":
                        self.stats["mapping_matched"] += 1
                    elif method == "FOLDER":
                        self.stats["folder_matched"] += 1
                    elif method == "FILENAME":
                        self.stats["filename_matched"] += 1
                    elif method == "OCR":
                        self.stats["ocr_matched"] += 1
                else:
                    print(f"❓ {file_path.name} → unmapped")
                    
                    if not dry_run:
                        unmapped_dir = dest / "unmapped"
                        unmapped_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, unmapped_dir / file_path.name)
                    
                    self.stats["unmapped"] += 1
            
            # Calculate totals
            total_matched = (self.stats["mapping_matched"] +
                            self.stats["folder_matched"] +
                            self.stats["filename_matched"] +
                            self.stats["ocr_matched"])
            
            # Write summary log
            if not dry_run:
                self._write_summary_log(dest, total_matched,
                                       self.stats["unmapped"], len(files))
            
            print()
            print("🎉 PROCESSING COMPLETE!")
            print(f"📊 Files Discovered: {len(files)}")
            print(f"📋 DETECTION BREAKDOWN:")
            print(f"  📊 Mapping: {self.stats['mapping_matched']}")
            print(f"  📁 Folder: {self.stats['folder_matched']}")
            print(f"  📝 Filename: {self.stats['filename_matched']}")
            print(f"  🔍 OCR: {self.stats['ocr_matched']}")
            print(f"✅ Total Matched: {total_matched}")
            print(f"❓ Unmapped Files: {self.stats['unmapped']}")
            print(f"📁 Output: {dest_path}")
            
            success_rate = (total_matched / len(files)) * 100 if files else 0
            print(f"🌟 Success Rate: {success_rate:.1f}%")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
        finally:
            self._cleanup_temp_dirs()
    
    def _discover_files(self, source_path: Path) -> List[Path]:
        """Discover all medical files in source"""
        
        files = []
        
        if source_path.is_file() and source_path.suffix.lower() == '.zip':
            # Extract ZIP
            temp_dir = tempfile.mkdtemp()
            self.temp_dirs.append(temp_dir)
            
            print(f"📦 Extracting ZIP to temporary folder...")
            with zipfile.ZipFile(source_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Scan extracted files
            for root, dirs, file_list in os.walk(temp_dir):
                for file_name in file_list:
                    file_path = Path(root) / file_name
                    if self._is_medical_file(file_path):
                        files.append(file_path)
        
        elif source_path.is_dir():
            # Scan directory
            for root, dirs, file_list in os.walk(source_path):
                for file_name in file_list:
                    file_path = Path(root) / file_name
                    if self._is_medical_file(file_path):
                        files.append(file_path)
        
        return files
    
    def _is_medical_file(self, file_path: Path) -> bool:
        """Check if file is a medical file"""
        medical_extensions = {
            '.pdf', '.doc', '.docx', '.txt', '.rtf',
            '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp',
            '.xml', '.json', '.csv', '.xlsx'
        }
        
        # Skip roster files and system files
        if 'roster' in file_path.name.lower():
            return False
        if file_path.name.startswith('.') or file_path.name.startswith('~'):
            return False
        
        return file_path.suffix.lower() in medical_extensions
    
    def _extract_patient_info(self, filename: str) -> Optional[Tuple[str, str, Optional[str]]]:
        """Extract patient info from filename using universal patterns"""
        
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
            
            # Pattern 6: Reversed (Firstname Lastname)
            r'([A-Za-z\'-]+)\s+([A-Za-z\'-]+)\s*-.*\((\d{4}-\d{2}-\d{2})\)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 3:
                    if 'DOE,J' in pattern:  # Special handling for comma pattern
                        last_name = match.group(1)
                        first_name = match.group(2)
                        dob_raw = match.group(3)
                    elif 'Firstname Lastname' in pattern or pattern == patterns[1] or pattern == patterns[5]:
                        # Firstname Lastname pattern
                        first_name = match.group(1).strip()
                        last_name = match.group(2).strip()
                        dob_raw = match.group(3).strip()
                    else:
                        # Lastname_Firstname pattern
                        last_name = match.group(1).strip()
                        first_name = match.group(2).strip()
                        dob_raw = match.group(3).strip()
                    
                    # Normalize DOB
                    dob_normalized = self._normalize_date(dob_raw)
                    
                    return last_name, first_name, dob_normalized
        
        return None

    def _process_single_file(self, file_path: Path) -> Optional[Tuple[str, str, str, Optional[str]]]:
        """
        Process single file following the workflow order:
        Mapping → Folder → Filename → OCR → Unmapped
        
        Returns: (method, last_name, first_name, dob) or None if unmapped
        """
        filename = file_path.name
        
        # STEP 1: MAPPING - Check mapping file first
        if self.mapping_data:
            for mapped_filename, patient_data in self.mapping_data.items():
                if mapped_filename.lower() in filename.lower() or filename.lower() in mapped_filename.lower():
                    return ("MAPPING", 
                           patient_data['last_name'], 
                           patient_data['first_name'], 
                           patient_data['dob'])
        
        # STEP 2: FOLDER - Check parent folder name for patient info
        folder_name = file_path.parent.name
        if folder_name != file_path.root:
            folder_patient = self._extract_patient_info(folder_name)
            if folder_patient:
                last_name, first_name, dob = folder_patient
                return ("FOLDER", last_name, first_name, dob)
        
        # STEP 3: FILENAME - Extract from filename
        filename_patient = self._extract_patient_info(filename)
        if filename_patient:
            last_name, first_name, dob = filename_patient
            return ("FILENAME", last_name, first_name, dob)
        
        # STEP 4: OCR - Try OCR extraction (if file supports it)
        if file_path.suffix.lower() in ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            ocr_patient = self._extract_patient_from_ocr(file_path)
            if ocr_patient:
                last_name, first_name, dob = ocr_patient
                return ("OCR", last_name, first_name, dob)
        
        # STEP 5: UNMAPPED - Return None if no method worked
        return None

    def _extract_patient_from_ocr(self, file_path: Path) -> Optional[Tuple[str, str, Optional[str]]]:
        """Extract patient info using OCR"""
        try:
            print(f"🔍 OCR processing: {file_path.name}")
            
            # Use the existing OCR processor if available
            if hasattr(self, 'ocr_processor') and self.ocr_processor:
                result = self.ocr_processor.extract_patient_from_pdf(
                    str(file_path), max_pages=10
                )
                
                if result and result.get('confidence', 0) > 0.5:
                    return (result.get('last_name', ''),
                           result.get('first_name', ''),
                           result.get('dob', None))
            
            # Simple OCR fallback using basic pattern matching
            # This would extract text and look for patterns
            return None
            
        except Exception as e:
            print(f"⚠️ OCR failed for {file_path.name}: {e}")
            return None
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date to YYYY-MM-DD format"""
        if not date_str:
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
    
    def _write_summary_log(self, dest_path: Path, matched: int, unmapped: int, total: int):
        """Write processing summary log"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        log_file = dest_path / "logs" / f"processing_summary_{timestamp}.csv"
        
        with open(log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "mapping_mode", "total_files", "matched_patients", 
                "unmapped_files", "success_rate"
            ])
            
            success_rate = (matched / total) * 100 if total > 0 else 0
            writer.writerow([
                datetime.now().isoformat(),
                "universal",  # mapping mode
                total,
                matched,
                unmapped,
                f"{success_rate:.1f}%"
            ])
        
        print(f"📊 Summary log written: {log_file}")
    
    def _cleanup_temp_dirs(self):
        """Clean up temporary directories"""
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Working Universal Medical File Processor'
    )
    
    parser.add_argument('--source', help='Source folder or ZIP file')
    parser.add_argument('--dest', help='Destination folder')
    parser.add_argument('--roster', help='Roster CSV file')
    parser.add_argument('--mapping', help='Mapping CSV file')
    parser.add_argument('--live', action='store_true', 
                       help='Live processing (default is dry run)')
    
    args = parser.parse_args()
    
    # Interactive mode if no args provided
    if not args.source:
        print("🌟 Working Universal Medical File Processor")
        print("Universal processor - handles any medical dataset")
        print()
        
        source = input("Enter source path (folder or ZIP): ").strip()
        if not source:
            print("❌ Source path required")
            sys.exit(1)
        
        dest = input("Enter destination path: ").strip()
        if not dest:
            print("❌ Destination path required")
            sys.exit(1)
        
        live_run = input("Live processing? (y/N): ").strip().lower()
        dry_run = not (live_run in ['y', 'yes'])
        
    else:
        source = args.source
        dest = args.dest
        dry_run = not args.live
    
    # Validate source exists
    if not Path(source).exists():
        print(f"❌ Source path does not exist: {source}")
        sys.exit(1)
    
    # Process
    processor = WorkingUniversalProcessor(
        roster_path=args.roster if hasattr(args, 'roster') else None,
        mapping_path=args.mapping if hasattr(args, 'mapping') else None
    )
    success = processor.process_dataset(source, dest, dry_run)
    
    if success:
        print("\n✨ Universal processing complete!")
    else:
        print("\n❌ Processing failed")
        sys.exit(1)


if __name__ == '__main__':
    main()