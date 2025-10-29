#!/usr/bin/env python3
"""
UNIVERSAL Medical File Organizer
Works with ANY dataset, ANY filename patterns, ANY roster formats
Automatically detects and adapts to different naming conventions
"""

import os
import shutil
import zipfile
import pandas as pd
from pathlib import Path
import re
import tempfile
from datetime import datetime


class UniversalDateNormalizer:
    """Handles ANY date format and normalizes to YYYY-MM-DD"""
    
    @staticmethod
    def normalize_date(date_str):
        """Convert ANY date format to YYYY-MM-DD"""
        if not date_str or str(date_str).strip() == '':
            return None
        if str(date_str).lower() in ['unknown', 'nan', 'null', 'none']:
            return None
        
        date_str = str(date_str).strip()
        
        # Common separators: -, /, ., space
        separators = ['-', '/', '.', ' ']
        
        for sep in separators:
            if sep in date_str:
                parts = date_str.split(sep)
                if len(parts) >= 3:
                    # Try different date part orders
                    for i, part1 in enumerate(parts[:3]):
                        for j, part2 in enumerate(parts[:3]):
                            for k, part3 in enumerate(parts[:3]):
                                if i != j and j != k and i != k:
                                    # Try this combination
                                    result = UniversalDateNormalizer._try_date_combination(
                                        part1, part2, part3
                                    )
                                    if result:
                                        return result
        
        # Try without separators (MMDDYYYY, YYYYMMDD, etc.)
        if date_str.isdigit():
            return UniversalDateNormalizer._parse_numeric_date(date_str)
        
        return None
    
    @staticmethod
    def _try_date_combination(p1, p2, p3):
        """Try to parse three parts as year, month, day"""
        try:
            p1, p2, p3 = int(p1), int(p2), int(p3)
            
            # Determine which is year (4 digits or > 31)
            year_candidates = [p for p in [p1, p2, p3] if p > 31 or len(str(p)) == 4]
            if not year_candidates:
                return None
            
            year = year_candidates[0]
            remaining = [p for p in [p1, p2, p3] if p != year]
            
            if len(remaining) != 2:
                return None
            
            # Try both month/day combinations
            for month, day in [(remaining[0], remaining[1]), (remaining[1], remaining[0])]:
                if 1 <= month <= 12 and 1 <= day <= 31:
                    # Validate date
                    try:
                        datetime(year, month, day)
                        return f"{year:04d}-{month:02d}-{day:02d}"
                    except ValueError:
                        continue
        except (ValueError, TypeError):
            pass
        
        return None
    
    @staticmethod
    def _parse_numeric_date(date_str):
        """Parse numeric date strings like 04221988, 19880422, etc."""
        if len(date_str) == 8:
            # Try different formats
            formats = [
                (date_str[:2], date_str[2:4], date_str[4:]),  # MMDDYYYY
                (date_str[4:], date_str[:2], date_str[2:4]),  # YYYYMMDD  
                (date_str[2:4], date_str[:2], date_str[4:]),  # DDMMYYYY
            ]
            
            for p1, p2, p3 in formats:
                result = UniversalDateNormalizer._try_date_combination(p1, p2, p3)
                if result:
                    return result
        
        return None


class UniversalFilenameParser:
    """Automatically detects and parses ANY filename pattern"""
    
    @staticmethod
    def extract_patient_info(filename):
        """Extract patient info from ANY filename pattern"""
        filename_base = os.path.splitext(filename)[0]
        
        # Character classes for names (including international characters)
        name_chars = r'[A-Za-z\'\-À-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]'
        date_chars = r'[0-9\-/\.\s]'
        
        # Pattern library - ordered by specificity
        patterns = [
            # LastName_FirstName_DATE_document
            (rf'({name_chars}+)_({name_chars}+)_({date_chars}+)_(.+)', 
             lambda m: (m.group(1), m.group(2), m.group(3))),
            
            # FirstName LastName - document (DATE) or FirstName LastName (DATE)
            (rf'({name_chars}+(?:\s+{name_chars}+)*)\s+({name_chars}+(?:\s+{name_chars}+)*)\s*[-\(]\s*[^(]*\s*\(({date_chars}+)\)',
             lambda m: (m.group(2).strip(), m.group(1).strip(), m.group(3))),
            
            # DOE,J,LAB_DATE or LASTNAME,F,TYPE_DATE
            (rf'([A-Z]+),([A-Z]+),[^_]*_?({date_chars}*\d{{6,8}}{date_chars}*)',
             lambda m: (m.group(1), m.group(2), m.group(3))),
            
            # lastname_firstname_date_type (lowercase)
            (rf'([a-z]+)_([a-z]+)_({date_chars}+)_(.+)',
             lambda m: (m.group(1).title(), m.group(2).title(), m.group(3))),
            
            # firstname lastname DATE (space separated)
            (rf'([a-z]+)\s+([a-z]+)\s+({date_chars}+)',
             lambda m: (m.group(2).title(), m.group(1).title(), m.group(3))),
            
            # LastName_FirstName_DATE (no document type)
            (rf'({name_chars}+)_({name_chars}+)_({date_chars}+)$',
             lambda m: (m.group(1), m.group(2), m.group(3))),
            
            # MRN123_LastName_FirstName_DATE_type
            (rf'[A-Z]*\d+_({name_chars}+)_({name_chars}+)_({date_chars}+)_(.+)',
             lambda m: (m.group(1), m.group(2), m.group(3))),
            
            # LastName_F_DDMMYYYY_type (abbreviated first name)
            (rf'({name_chars}+)_([A-Z])_({date_chars}+)_(.+)',
             lambda m: (m.group(1), m.group(2), m.group(3))),
        ]
        
        for pattern, extractor in patterns:
            try:
                match = re.match(pattern, filename_base, re.IGNORECASE)
                if match:
                    last_name, first_name, date_raw = extractor(match)
                    
                    # Normalize the date
                    date_normalized = UniversalDateNormalizer.normalize_date(date_raw)
                    
                    if date_normalized and last_name and first_name:
                        return last_name.strip(), first_name.strip(), date_normalized
            except Exception:
                continue
        
        return None, None, None


class UniversalRosterLoader:
    """Automatically detects and loads ANY roster format"""
    
    @staticmethod
    def find_roster_files(source_path):
        """Find ALL possible roster files"""
        roster_patterns = [
            '*roster*.csv', '*roster*.xlsx', '*roster*.xls',
            '*patient*.csv', '*patient*.xlsx', '*patient*.xls', 
            '*practice*.csv', '*practice*.xlsx', '*practice*.xls',
            '*member*.csv', '*member*.xlsx', '*member*.xls',
            '*client*.csv', '*client*.xlsx', '*client*.xls',
            'roster.*', 'patients.*', 'practice.*', 'members.*', 'clients.*'
        ]
        
        roster_files = []
        for pattern in roster_patterns:
            files = list(Path(source_path).rglob(pattern))
            roster_files.extend(files)
        
        # Remove duplicates and sort by name (prefer 'roster' over others)
        unique_files = list(set(roster_files))
        unique_files.sort(key=lambda f: (
            'roster' not in f.name.lower(),
            'patient' not in f.name.lower(),
            f.name.lower()
        ))
        
        return unique_files
    
    @staticmethod
    def load_roster_universal(roster_file):
        """Load roster with automatic column detection"""
        if not roster_file or not roster_file.exists():
            return {}
        
        try:
            # Try multiple encodings
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            df = None
            
            for encoding in encodings:
                try:
                    if roster_file.suffix.lower() == '.csv':
                        df = pd.read_csv(roster_file, encoding=encoding)
                    else:
                        df = pd.read_excel(roster_file)
                    break
                except (UnicodeDecodeError, pd.errors.EmptyDataError):
                    continue
            
            if df is None or df.empty:
                return {}
            
            print(f"📋 Roster columns: {list(df.columns)}")
            
            # Smart column detection
            column_mapping = UniversalRosterLoader._detect_columns(df.columns)
            
            if not all(column_mapping.values()):
                print(f"❌ Could not detect all required columns")
                return {}
            
            print(f"✅ Detected columns: {column_mapping}")
            
            # Build patient lookup
            patients = {}
            for _, row in df.iterrows():
                try:
                    last_name = str(row[column_mapping['last_name']]).strip()
                    first_name = str(row[column_mapping['first_name']]).strip()
                    dob_raw = str(row[column_mapping['dob']]).strip()
                    
                    dob_normalized = UniversalDateNormalizer.normalize_date(dob_raw)
                    
                    if dob_normalized and last_name and first_name:
                        # Create multiple lookup keys for fuzzy matching
                        keys = [
                            f"{last_name}_{first_name}_{dob_normalized}",
                            f"{last_name.upper()}_{first_name.upper()}_{dob_normalized}",
                            f"{last_name.lower()}_{first_name.lower()}_{dob_normalized}",
                        ]
                        
                        patient_data = {
                            'last_name': last_name,
                            'first_name': first_name,
                            'dob_original': dob_raw,
                            'dob_normalized': dob_normalized,
                            'folder_name': f"{last_name}_{first_name}_{dob_normalized}"
                        }
                        
                        for key in keys:
                            patients[key] = patient_data
                        
                        print(f"  ✅ {last_name}_{first_name}_{dob_normalized} (from {dob_raw})")
                
                except Exception as e:
                    continue
            
            print(f"✅ Loaded {len(set(p['folder_name'] for p in patients.values()))} unique patients")
            return patients
            
        except Exception as e:
            print(f"❌ Error loading roster: {e}")
            return {}
    
    @staticmethod
    def _detect_columns(columns):
        """Automatically detect column names for last name, first name, and DOB"""
        column_mapping = {'last_name': None, 'first_name': None, 'dob': None}
        
        for col in columns:
            col_lower = col.lower().strip()
            col_clean = re.sub(r'[^a-z]', '', col_lower)
            
            # Last name detection
            if not column_mapping['last_name']:
                lastname_patterns = [
                    'lastname', 'last_name', 'lname', 'surname', 'family_name',
                    'familyname', 'last', 'l_name'
                ]
                if col_lower in lastname_patterns or col_clean in lastname_patterns:
                    column_mapping['last_name'] = col
            
            # First name detection  
            if not column_mapping['first_name']:
                firstname_patterns = [
                    'firstname', 'first_name', 'fname', 'given_name', 'givenname',
                    'first', 'f_name', 'forename'
                ]
                if col_lower in firstname_patterns or col_clean in firstname_patterns:
                    column_mapping['first_name'] = col
            
            # DOB detection
            if not column_mapping['dob']:
                dob_patterns = [
                    'dob', 'dateofbirth', 'date_of_birth', 'birthdate', 'birthday',
                    'birth_date', 'born', 'bdate'
                ]
                if col_lower in dob_patterns or col_clean in dob_patterns:
                    column_mapping['dob'] = col
        
        return column_mapping


class UniversalMedicalOrganizer:
    """Universal organizer that adapts to ANY medical dataset"""
    
    def __init__(self):
        self.date_normalizer = UniversalDateNormalizer()
        self.filename_parser = UniversalFilenameParser()
        self.roster_loader = UniversalRosterLoader()
    
    def organize_dataset(self, dataset_path, output_path="UNIVERSAL_OUTPUT"):
        """Organize ANY medical dataset universally"""
        
        print(f"🚀 Universal Medical File Organizer")
        print(f"📁 Processing: {dataset_path}")
        
        try:
            # Handle ZIP files or directories
            if dataset_path.endswith('.zip') and os.path.isfile(dataset_path):
                temp_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(dataset_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                source_path = Path(temp_dir)
                cleanup_temp = True
            else:
                source_path = Path(dataset_path)
                cleanup_temp = False
            
            # Find roster files
            roster_files = self.roster_loader.find_roster_files(source_path)
            
            if not roster_files:
                print("❌ No roster files found")
                return {"error": "No roster files found"}
            
            print(f"📋 Found {len(roster_files)} potential roster file(s)")
            
            # Try each roster file until we find one that works
            patients = {}
            for roster_file in roster_files:
                print(f"📋 Trying roster: {roster_file}")
                patients = self.roster_loader.load_roster_universal(roster_file)
                if patients:
                    print(f"✅ Successfully loaded roster: {roster_file}")
                    break
            
            if not patients:
                print("❌ Could not load any roster file")
                return {"error": "Could not load patient data"}
            
            # Create output directories
            organized_dir = Path(output_path) / "organized"
            unmapped_dir = Path(output_path) / "unmapped"
            organized_dir.mkdir(parents=True, exist_ok=True)
            unmapped_dir.mkdir(parents=True, exist_ok=True)
            
            # Find all potential medical files
            medical_extensions = [
                '.pdf', '.doc', '.docx', '.txt', '.rtf',
                '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp',
                '.xml', '.json', '.csv', '.xls', '.xlsx',
                '.dcm', '.dicom'  # Medical imaging formats
            ]
            
            all_files = []
            for ext in medical_extensions:
                all_files.extend(source_path.rglob(f'*{ext}'))
            
            # Remove roster files from processing
            roster_paths = {str(rf) for rf in roster_files}
            all_files = [f for f in all_files if str(f) not in roster_paths]
            
            print(f"📄 Found {len(all_files)} files to process")
            
            organized_count = 0
            unmapped_count = 0
            results = []
            
            # Process each file
            for file_path in all_files:
                filename = file_path.name
                
                # Extract patient info using universal parser
                last_name, first_name, dob_normalized = self.filename_parser.extract_patient_info(filename)
                
                if last_name and first_name and dob_normalized:
                    # Try multiple lookup keys
                    lookup_keys = [
                        f"{last_name}_{first_name}_{dob_normalized}",
                        f"{last_name.upper()}_{first_name.upper()}_{dob_normalized}",
                        f"{last_name.lower()}_{first_name.lower()}_{dob_normalized}",
                    ]
                    
                    matched_patient = None
                    for key in lookup_keys:
                        if key in patients:
                            matched_patient = patients[key]
                            break
                    
                    if matched_patient:
                        # Match found!
                        patient_folder = organized_dir / matched_patient['folder_name']
                        patient_folder.mkdir(exist_ok=True)
                        
                        dest_file = patient_folder / filename
                        
                        try:
                            shutil.copy2(file_path, dest_file)
                            organized_count += 1
                            results.append({
                                'file': filename,
                                'status': 'organized',
                                'patient': f"{matched_patient['first_name']} {matched_patient['last_name']}",
                                'folder': matched_patient['folder_name']
                            })
                            print(f"✅ {filename} → {matched_patient['folder_name']}")
                        except Exception as e:
                            print(f"❌ Copy error: {e}")
                            shutil.copy2(file_path, unmapped_dir / filename)
                            unmapped_count += 1
                    else:
                        # No match found
                        shutil.copy2(file_path, unmapped_dir / filename)
                        unmapped_count += 1
                        results.append({
                            'file': filename,
                            'status': 'unmapped',
                            'reason': f'No patient match for {last_name}, {first_name}, {dob_normalized}'
                        })
                        print(f"❓ No match: {filename}")
                else:
                    # Could not parse filename
                    shutil.copy2(file_path, unmapped_dir / filename)
                    unmapped_count += 1
                    results.append({
                        'file': filename,
                        'status': 'unmapped',
                        'reason': 'Could not parse patient info from filename'
                    })
                    print(f"❓ Parse failed: {filename}")
            
            # Cleanup
            if cleanup_temp:
                shutil.rmtree(temp_dir)
            
            # Results
            print(f"\n🎉 UNIVERSAL PROCESSING COMPLETE!")
            print(f"📊 Results:")
            print(f"   Total files: {len(all_files)}")
            print(f"   ✅ Organized: {organized_count}")
            print(f"   ❓ Unmapped: {unmapped_count}")
            print(f"   📁 Output: {output_path}")
            
            return {
                'status': 'success',
                'stats': {
                    'total_files': len(all_files),
                    'organized': organized_count,
                    'unmapped': unmapped_count,
                    'success_rate': f"{(organized_count/len(all_files)*100):.1f}%" if all_files else "0%"
                },
                'output_path': output_path,
                'details': results
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {"error": str(e)}


def main():
    """Universal organizer - works with ANY dataset"""
    import sys
    
    # Get dataset path from command line argument or prompt user
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = input(
            "Enter path to your medical dataset (ZIP file or folder): "
        ).strip()
        if not dataset_path:
            print("❌ No dataset path provided. Exiting.")
            sys.exit(1)
    
    if not Path(dataset_path).exists():
        print(f"❌ Path does not exist: {dataset_path}")
        sys.exit(1)
    
    organizer = UniversalMedicalOrganizer()
    
    # Process it universally
    results = organizer.organize_dataset(dataset_path, "UNIVERSAL_OUTPUT")
    
    if 'error' not in results:
        print("\n🌟 Universal processing successful!")
        print(f"Success Rate: {results['stats']['success_rate']}")
    else:
        print(f"❌ Error: {results['error']}")


if __name__ == '__main__':
    main()