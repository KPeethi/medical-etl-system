#!/usr/bin/env python3
"""
Enhanced Flat File Organizer - With PDF Content Reading
Reads PDF content to find patient names and DOB when filename parsing fails
"""

import shutil
import zipfile
import pandas as pd
from pathlib import Path
import re
import tempfile
import PyPDF2


def extract_text_from_pdf(pdf_path):
    """Extract text content from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"   ❌ Error reading PDF {pdf_path}: {e}")
        return ""


def find_patient_info_in_text(text, patients_dict):
    """
    Search for patient information in text using various synonyms
    """
    if not text:
        return None
    
    # Convert text to lowercase for searching
    text_lower = text.lower()
    
    # Define synonyms for name fields
    lastname_patterns = [
        r'last\s*name[:\s]+([a-zA-Z\']+)',
        r'surname[:\s]+([a-zA-Z\']+)',
        r'family\s*name[:\s]+([a-zA-Z\']+)',
        r'patient[:\s]+([a-zA-Z\']+)\s+[a-zA-Z\']+',  # Patient: Smith John
    ]
    
    firstname_patterns = [
        r'first\s*name[:\s]+([a-zA-Z\']+)',
        r'given\s*name[:\s]+([a-zA-Z\']+)',
        r'forename[:\s]+([a-zA-Z\']+)',
    ]
    
    # DOB patterns with various synonyms
    dob_patterns = [
        r'dob[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        r'date\s*of\s*birth[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        r'birth\s*date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        r'birthdate[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        r'born[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        r'birth[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        # Also try YYYY-MM-DD format
        r'dob[:\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        r'date\s*of\s*birth[:\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        r'birth\s*date[:\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
    ]
    
    # Try to find last name
    found_lastname = None
    for pattern in lastname_patterns:
        match = re.search(pattern, text_lower)
        if match:
            found_lastname = match.group(1).capitalize()
            break
    
    # Try to find first name
    found_firstname = None
    for pattern in firstname_patterns:
        match = re.search(pattern, text_lower)
        if match:
            found_firstname = match.group(1).capitalize()
            break
    
    # Try to find DOB
    found_dob = None
    for pattern in dob_patterns:
        match = re.search(pattern, text_lower)
        if match:
            date_str = match.group(1)
            # Normalize date format to YYYY-MM-DD
            try:
                if '/' in date_str:
                    date_str = date_str.replace('/', '-')
                
                parts = date_str.split('-')
                if len(parts) == 3:
                    if len(parts[0]) == 4:  # YYYY-MM-DD format
                        found_dob = date_str
                    else:  # MM-DD-YYYY format
                        found_dob = (f"{parts[2]}-{parts[0].zfill(2)}-"
                                     f"{parts[1].zfill(2)}")
                break
            except Exception:
                continue
    
    print(f"   🔍 Found: Last='{found_lastname}', "
          f"First='{found_firstname}', DOB='{found_dob}'")
    
    # If we found name components, try to match with roster
    if found_lastname and found_firstname and found_dob:
        # Create key to match with roster
        key = f"{found_lastname}_{found_firstname}_{found_dob}"
        
        # Try exact match first
        if key in patients_dict:
            return patients_dict[key]
        
        # Try case-insensitive match
        for patient_key, patient_info in patients_dict.items():
            if patient_key.lower() == key.lower():
                return patient_info
        
        # Try partial matches (name only, different DOB formats)
        for patient_key, patient_info in patients_dict.items():
            patient_parts = patient_key.split('_')
            if len(patient_parts) >= 3:
                if (patient_parts[0].lower() == found_lastname.lower() and
                        patient_parts[1].lower() == found_firstname.lower()):
                    return patient_info
    
    return None


def organize_files_with_content_reading(source_zip=None, dest_folder=None):
    """Enhanced organizer that reads PDF content for patient matching"""
    
    # Get paths from parameters or prompt user
    if not source_zip:
        source_zip = input("Enter path to source ZIP file: ").strip()
    if not dest_folder:
        dest_folder = input("Enter destination folder path: ").strip()
    
    if not source_zip or not dest_folder:
        print("❌ Both source and destination paths are required.")
        return False
    
    print("🚀 Starting ENHANCED file organization...")
    print("📋 Features: Filename parsing + PDF content reading")
    print(f"📦 Source: {source_zip}")
    print(f"📁 Destination: {dest_folder}")
    
    # Check if source exists
    if not Path(source_zip).exists():
        print(f"❌ ERROR: Source file not found: {source_zip}")
        return
    
    # Create destination folder
    dest_path = Path(dest_folder)
    if dest_path.exists():
        print(f"🗑️ Removing existing folder: {dest_path}")
        shutil.rmtree(dest_path)
    
    dest_path.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created destination folder: {dest_path}")
    
    # Extract ZIP to temp location
    with tempfile.TemporaryDirectory() as temp_dir:
        print("📦 Extracting ZIP...")
        
        with zipfile.ZipFile(source_zip, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the dataset folder
        temp_path = Path(temp_dir)
        dataset_folder = temp_path / "medical_dataset"
        
        if not dataset_folder.exists():
            subfolders = [f for f in temp_path.iterdir() if f.is_dir()]
            if subfolders:
                dataset_folder = subfolders[0]
        
        # Load roster
        roster_file = dataset_folder / "roster.csv"
        patients = {}
        
        if roster_file.exists():
            print("📋 Loading patient roster...")
            df = pd.read_csv(roster_file)
            for _, row in df.iterrows():
                key = f"{row['last_name']}_{row['first_name']}_{row['dob']}"
                # Convert date format from YYYY-MM-DD to MM-DD-YYYY
                dob_parts = row['dob'].split('-')
                formatted_dob = f"{dob_parts[1]}-{dob_parts[2]}-{dob_parts[0]}"
                
                patients[key] = {
                    'folder_name': (f"{row['last_name']}, "
                                    f"{row['first_name']} {formatted_dob}"),
                    'patient_id': row['patient_id']
                }
            print(f"✅ Loaded {len(patients)} patients from roster")
        else:
            print(f"❌ ERROR: Roster file not found: {roster_file}")
            return
        
        # Process all files
        print("\n🔄 Processing files with enhanced matching...")
        file_count = 0
        copied_count = 0
        unmapped_count = 0
        content_matched_count = 0
        
        for file_path in dataset_folder.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.jpg', '.jpeg', '.tif', '.tiff']:
                file_count += 1
                filename = file_path.name
                print(f"\n📄 File {file_count}: {filename}")
                
                matched_patient = None
                match_method = "unknown"
                
                # STEP 1: Try filename parsing first
                pattern = r'([A-Za-z\']+)_([A-Za-z]+)_(\d{4}-\d{2}-\d{2})_(.+)'
                match = re.match(pattern, filename)
                
                if match:
                    last_name = match.group(1)
                    first_name = match.group(2)
                    dob = match.group(3)
                    doc_type = match.group(4).replace('.pdf', '').replace('.jpg', '').replace('.tif', '')
                    
                    key = f"{last_name}_{first_name}_{dob}"
                    
                    if key in patients:
                        matched_patient = patients[key]
                        match_method = "filename"
                        print(f"   ✅ Matched by filename: {matched_patient['folder_name']}")
                
                # STEP 2: If filename parsing failed and it's a PDF, try content reading
                if not matched_patient and file_path.suffix.lower() == '.pdf':
                    print("   📖 Filename parsing failed, trying PDF content reading...")
                    pdf_text = extract_text_from_pdf(file_path)
                    
                    if pdf_text:
                        matched_patient = find_patient_info_in_text(pdf_text, patients)
                        if matched_patient:
                            match_method = "content"
                            content_matched_count += 1
                            print(f"   🎯 Matched by PDF content: {matched_patient['folder_name']}")
                        else:
                            print("   ❌ No patient match found in PDF content")
                    else:
                        print("   ❌ Could not extract text from PDF")
                
                # STEP 3: Process the file based on matching results
                if matched_patient:
                    # Create patient folder
                    patient_folder = dest_path / matched_patient['folder_name']
                    patient_folder.mkdir(exist_ok=True)
                    
                    # Determine module prefix
                    if match and match_method == "filename":
                        doc_type = match.group(4).replace('.pdf', '').replace('.jpg', '').replace('.tif', '')
                    else:
                        # For content-matched files, try to guess document type from filename or content
                        doc_type = filename.lower()
                    
                    if 'lab' in doc_type.lower():
                        module_prefix = "Laboratory"
                    elif 'report' in doc_type.lower() or 'summary' in doc_type.lower():
                        module_prefix = "Reports"
                    elif 'note' in doc_type.lower() or 'visit' in doc_type.lower():
                        module_prefix = "Clinical_Notes"
                    elif 'photo' in doc_type.lower() or 'image' in doc_type.lower():
                        module_prefix = "Imaging"
                    elif 'invoice' in doc_type.lower():
                        module_prefix = "Billing"
                    elif 'medrec' in doc_type.lower():
                        module_prefix = "Medical_Records"
                    else:
                        module_prefix = "Documents"
                    
                    # Create new filename
                    if match_method == "filename":
                        # Remove patient name part from filename
                        original_doc_part = filename.replace(f"{last_name}_{first_name}_{dob}_", "")
                        new_filename = f"{module_prefix}_{original_doc_part}"
                    else:
                        # For content-matched files, keep original filename with prefix
                        new_filename = f"{module_prefix}_{filename}"
                    
                    # Copy file to patient folder
                    dest_file = patient_folder / new_filename
                    shutil.copy2(file_path, dest_file)
                    copied_count += 1
                    
                    print(f"   ✅ COPIED as: {new_filename} (matched by {match_method})")
                    
                else:
                    # Create unmapped folder
                    unmapped_folder = dest_path / "_Unmapped_Files"
                    unmapped_folder.mkdir(exist_ok=True)
                    dest_file = unmapped_folder / filename
                    shutil.copy2(file_path, dest_file)
                    unmapped_count += 1
                    
                    print(f"   ⚠️ UNMAPPED: {filename}")
        
        print(f"\n🎉 ENHANCED ORGANIZATION COMPLETE!")
        print(f"📊 Statistics:")
        print(f"   📄 Files processed: {file_count}")
        print(f"   ✅ Files copied to patient folders: {copied_count}")
        print(f"   🎯 Matched by PDF content reading: {content_matched_count}")
        print(f"   ⚠️ Still unmapped: {unmapped_count}")
        
        print(f"\n📁 Check your organized files at:")
        print(f"   {dest_path}")
        
        # Show folder structure
        print(f"\n📂 Enhanced folder structure:")
        for item in dest_path.iterdir():
            if item.is_dir():
                print(f"   📁 {item.name}/")
                for file in item.iterdir():
                    if file.is_file():
                        print(f"      📄 {file.name}")

if __name__ == "__main__":
    import sys
    
    # Get source and destination paths from command line or prompt user
    if len(sys.argv) > 2:
        source_zip = sys.argv[1]
        dest_folder = sys.argv[2]
        organize_files_with_content_reading(source_zip, dest_folder)
    else:
        organize_files_with_content_reading()