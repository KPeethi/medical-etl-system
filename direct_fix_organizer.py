#!/usr/bin/env python3
"""
Direct File Organizer with Date Fix
Processes your dataset directly without API server
"""

import os
import shutil
import zipfile
import pandas as pd
from pathlib import Path
import re
import tempfile


def normalize_date(date_str):
    """Convert various date formats to YYYY-MM-DD for comparison"""
    if not date_str or str(date_str).strip() == '' or str(date_str).lower() in ['unknown', 'nan']:
        return None
    
    date_str = str(date_str).strip()
    
    # Pattern 1: YYYY-MM-DD or YYYY-M-D (already correct format)
    match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # Pattern 2: MM/DD/YYYY or M/D/YYYY
    match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
    if match:
        month, day, year = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # Pattern 3: YYYY/MM/DD or YYYY/M/D
    match = re.match(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # Pattern 4: MM-DD-YYYY or M-D-YYYY
    match = re.match(r'(\d{1,2})-(\d{1,2})-(\d{4})', date_str)
    if match:
        month, day, year = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    return None


def find_roster_file(source_path):
    """Find roster file in various formats and locations"""
    roster_patterns = ['*roster*.csv', '*patient*.csv', '*practice*.csv']
    
    for pattern in roster_patterns:
        files = list(Path(source_path).rglob(pattern))
        if files:
            return files[0]
    
    return None


def load_roster_with_date_fix(roster_file):
    """Load roster with robust date normalization"""
    patients = {}
    
    if not roster_file or not roster_file.exists():
        print("❌ No roster file found")
        return patients
    
    try:
        # Try different encodings
        for encoding in ['utf-8', 'latin1', 'cp1252']:
            try:
                df = pd.read_csv(roster_file, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            print("❌ Could not read roster file")
            return patients
        
        print(f"📋 Roster columns: {list(df.columns)}")
        
        # Find columns flexibly
        last_name_col = None
        first_name_col = None
        dob_col = None
        
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in ['lastname', 'last_name', 'lname', 'surname']:
                last_name_col = col
            elif col_lower in ['firstname', 'first_name', 'fname', 'givenname']:
                first_name_col = col
            elif col_lower in ['dob', 'dateofbirth', 'date_of_birth', 'birthdate']:
                dob_col = col
        
        if not all([last_name_col, first_name_col, dob_col]):
            print(f"❌ Missing columns. Found: {list(df.columns)}")
            return patients
        
        print(f"✅ Using columns: {last_name_col}, {first_name_col}, {dob_col}")
        
        # Process each row with date normalization
        for _, row in df.iterrows():
            try:
                last_name = str(row[last_name_col]).strip()
                first_name = str(row[first_name_col]).strip()
                dob_raw = str(row[dob_col]).strip()
                
                # Normalize the date
                dob_normalized = normalize_date(dob_raw)
                
                if dob_normalized and last_name and first_name:
                    key = f"{last_name}_{first_name}_{dob_normalized}"
                    patients[key] = {
                        'last_name': last_name,
                        'first_name': first_name,
                        'dob_original': dob_raw,
                        'dob_normalized': dob_normalized,
                        'folder_name': f"{last_name}_{first_name}_{dob_normalized}"
                    }
                    print(f"  ✅ Loaded: {key} (from {dob_raw})")
                else:
                    print(f"  ❌ Skipped: {last_name} {first_name} {dob_raw}")
            except Exception as e:
                print(f"  ❌ Error processing row: {e}")
                continue
        
        print(f"✅ Loaded {len(patients)} patients from roster")
        return patients
        
    except Exception as e:
        print(f"❌ Error loading roster: {e}")
        return patients


def extract_patient_from_filename(filename):
    """Extract patient info from filename with flexible date parsing"""
    filename_base = os.path.splitext(filename)[0]
    
    # Pattern 1: LastName_FirstName_DATE_document (handles hyphens and accents)
    pattern1 = r'([A-Za-z\'\-ÀÁÂÃÄÅàáâãäåĀāĂăĄąÇçĆćĈĉĊċČčÐðĎďĐđÈÉÊËèéêëĒēĔĕĖėĘęĚěĜĝĞğĠġĢģĤĥĦħÌÍÎÏìíîïĨĩĪīĬĭĮįİıĴĵĶķĸĹĺĻļĽľĿŀŁłÑñŃńŅņŇňŉŋÒÓÔÕÖØòóôõöøŌōŎŏŐőŔŕŖŗŘřŚśŜŝŞşŠšſŢţŤťŦŧÙÚÛÜùúûüŨũŪūŬŭŮůŰűŲųŴŵÝýŸÿŶŷŹźŻżŽž]+)_([A-Za-z\'\-ÀÁÂÃÄÅàáâãäåĀāĂăĄąÇçĆćĈĉĊċČčÐðĎďĐđÈÉÊËèéêëĒēĔĕĖėĘęĚěĜĝĞğĠġĢģĤĥĦħÌÍÎÏìíîïĨĩĪīĬĭĮįİıĴĵĶķĸĹĺĻļĽľĿŀŁłÑñŃńŅņŇňŉŋÒÓÔÕÖØòóôõöøŌōŎŏŐőŔŕŖŗŘřŚśŜŝŞşŠšſŢţŤťŦŧÙÚÛÜùúûüŨũŪūŬŭŮůŰűŲųŴŵÝýŸÿŶŷŹźŻżŽž]+)_([0-9\-/]+)_(.+)'
    match = re.match(pattern1, filename_base)
    
    if match:
        last_name = match.group(1)
        first_name = match.group(2)
        dob_raw = match.group(3)
        doc_type = match.group(4)
        
        dob_normalized = normalize_date(dob_raw)
        if dob_normalized:
            return last_name, first_name, dob_normalized, doc_type
    
    # Pattern 2: FirstName LastName - document (DATE) format
    pattern2 = r'([A-Za-z\'\-ÀÁÂÃÄÅàáâãäåĀāĂăĄąÇçĆćĈĉĊċČčÐðĎďĐđÈÉÊËèéêëĒēĔĕĖėĘęĚěĜĝĞğĠġĢģĤĥĦħÌÍÎÏìíîïĨĩĪīĬĭĮįİıĴĵĶķĸĹĺĻļĽľĿŀŁłÑñŃńŅņŇňŉŋÒÓÔÕÖØòóôõöøŌōŎŏŐőŔŕŖŗŘřŚśŜŝŞşŠšſŢţŤťŦŧÙÚÛÜùúûüŨũŪūŬŭŮůŰűŲųŴŵÝýŸÿŶŷŹźŻżŽž\s]+)\s+([A-Za-z\'\-ÀÁÂÃÄÅàáâãäåĀāĂăĄąÇçĆćĈĉĊċČčÐðĎďĐđÈÉÊËèéêëĒēĔĕĖėĘęĚěĜĝĞğĠġĢģĤĥĦħÌÍÎÏìíîïĨĩĪīĬĭĮįİıĴĵĶķĸĹĺĻļĽľĿŀŁłÑñŃńŅņŇňŉŋÒÓÔÕÖØòóôõöøŌōŎŏŐőŔŕŖŗŘřŚśŜŝŞşŠšſŢţŤťŦŧÙÚÛÜùúûüŨũŪūŬŭŮůŰűŲųŴŵÝýŸÿŶŷŹźŻżŽž\s]+)\s*-\s*.+\s*\(([0-9\-/]+)\)'
    match = re.match(pattern2, filename_base)
    
    if match:
        first_name = match.group(1).strip()
        last_name = match.group(2).strip()
        dob_raw = match.group(3)
        
        dob_normalized = normalize_date(dob_raw)
        if dob_normalized:
            return last_name, first_name, dob_normalized, "document"
    
    # Pattern 3: DOE,J,LAB_MMDDYYYY format
    pattern3 = r'([A-Z]+),([A-Z]+),.*([0-9]{8})'
    match = re.match(pattern3, filename_base)
    
    if match:
        last_name = match.group(1)
        first_name = match.group(2)
        date_raw = match.group(3)
        
        # Convert MMDDYYYY to MM/DD/YYYY
        if len(date_raw) == 8:
            month = date_raw[:2]
            day = date_raw[2:4]
            year = date_raw[4:]
            dob_formatted = f"{month}/{day}/{year}"
            dob_normalized = normalize_date(dob_formatted)
            if dob_normalized:
                return last_name, first_name, dob_normalized, "document"
    
    # Pattern 4: garcia_maria_1995_10_14_clinical format
    pattern4 = r'([a-z]+)_([a-z]+)_(\d{4}_\d{1,2}_\d{1,2})_(.+)'
    match = re.match(pattern4, filename_base)
    
    if match:
        last_name = match.group(1).title()
        first_name = match.group(2).title()
        date_parts = match.group(3).split('_')
        dob_formatted = f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}"
        dob_normalized = normalize_date(dob_formatted)
        if dob_normalized:
            return last_name, first_name, dob_normalized, match.group(4)
    
    return None, None, None, None


def main():
    """Main processing function"""
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
    
    output_path = "FIXED_OUTPUT_DIRECT"
    
    print(f"🚀 Processing dataset: {dataset_path}")
    
    # Handle ZIP files
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(dataset_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    source_path = Path(temp_dir)
    
    print(f"📁 Extracted to: {source_path}")
    
    # Find and load roster
    roster_file = find_roster_file(source_path)
    if not roster_file:
        print("❌ No roster file found")
        return
    
    print(f"📋 Found roster: {roster_file}")
    patients = load_roster_with_date_fix(roster_file)
    
    if not patients:
        print("❌ Could not load patient data from roster")
        return
    
    # Create output directories
    organized_dir = Path(output_path) / "organized"
    unmapped_dir = Path(output_path) / "unmapped"
    organized_dir.mkdir(parents=True, exist_ok=True)
    unmapped_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all medical files
    extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.xml']
    all_files = []
    for ext in extensions:
        all_files.extend(source_path.rglob(f'*{ext}'))
    
    print(f"📄 Found {len(all_files)} files to process")
    
    organized_count = 0
    unmapped_count = 0
    
    # Process each file
    for file_path in all_files:
        filename = file_path.name
        
        # Extract patient info
        last_name, first_name, dob_normalized, doc_type = extract_patient_from_filename(filename)
        
        if last_name and first_name and dob_normalized:
            # Look for patient match
            patient_key = f"{last_name}_{first_name}_{dob_normalized}"
            
            if patient_key in patients:
                # Match found!
                patient_info = patients[patient_key]
                patient_folder = organized_dir / patient_info['folder_name']
                patient_folder.mkdir(exist_ok=True)
                
                dest_file = patient_folder / filename
                
                try:
                    shutil.copy2(file_path, dest_file)
                    organized_count += 1
                    print(f"✅ {filename} → {patient_info['folder_name']}")
                except Exception as e:
                    print(f"❌ Copy error: {filename} - {e}")
                    shutil.copy2(file_path, unmapped_dir / filename)
                    unmapped_count += 1
            else:
                # No patient match found
                shutil.copy2(file_path, unmapped_dir / filename)
                unmapped_count += 1
                print(f"❓ Unmapped: {filename} (no match for {patient_key})")
        else:
            # Could not parse filename
            shutil.copy2(file_path, unmapped_dir / filename)
            unmapped_count += 1
            print(f"❓ Unmapped: {filename} (parse failed)")
    
    # Clean up
    shutil.rmtree(temp_dir)
    
    print(f"\n🎉 COMPLETE!")
    print(f"📊 Results:")
    print(f"   Total files: {len(all_files)}")
    print(f"   Organized: {organized_count}")
    print(f"   Unmapped: {unmapped_count}")
    print(f"📁 Output directory: {output_path}")


if __name__ == '__main__':
    main()