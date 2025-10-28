#!/usr/bin/env python3
"""
Ultimate Enhanced File Organizer - With Robust PDF Content Reading
Handles multiple PDF formats and graceful error handling
"""

import shutil
import zipfile
import pandas as pd
from pathlib import Path
import re
import tempfile

# Multiple PDF reading libraries for robustness
import PyPDF2
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


def extract_text_from_pdf_robust(pdf_path):
    """
    Try multiple PDF libraries to extract text robustly
    """
    text = ""
    pdf_path_str = str(pdf_path)
    
    # Method 1: Try PyPDF2 first
    try:
        with open(pdf_path_str, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        if text.strip():
            print(f"   ✅ PDF text extracted using PyPDF2")
            return text.strip()
    except Exception as e:
        print(f"   ⚠️ PyPDF2 failed: {e}")
    
    # Method 2: Try pdfplumber if available
    if HAS_PDFPLUMBER and not text.strip():
        try:
            with pdfplumber.open(pdf_path_str) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if text.strip():
                print(f"   ✅ PDF text extracted using pdfplumber")
                return text.strip()
        except Exception as e:
            print(f"   ⚠️ pdfplumber failed: {e}")
    
    # Method 3: Try PyMuPDF if available
    if HAS_PYMUPDF and not text.strip():
        try:
            doc = fitz.open(pdf_path_str)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            if text.strip():
                print(f"   ✅ PDF text extracted using PyMuPDF")
                return text.strip()
        except Exception as e:
            print(f"   ⚠️ PyMuPDF failed: {e}")
    
    print(f"   ❌ All PDF extraction methods failed for {pdf_path.name}")
    return ""


def find_patient_info_in_text_enhanced(text, patients_dict):
    """
    Enhanced patient information finder with more patterns
    """
    if not text:
        return None
    
    # Convert text to lowercase for searching
    text_lower = text.lower()
    
    # Enhanced name patterns - more flexible
    lastname_patterns = [
        r'last\s*name[:\s]*[:-]?\s*([a-zA-Z\']+)',
        r'surname[:\s]*[:-]?\s*([a-zA-Z\']+)',
        r'family\s*name[:\s]*[:-]?\s*([a-zA-Z\']+)',
        r'patient[:\s]*[:-]?\s*([a-zA-Z\']+)\s+[a-zA-Z\']+',
        r'patient\s*-\s*last\s*name[:\s]*([a-zA-Z\']+)',
        # New patterns for different formats
        r'([a-zA-Z\']+),\s*[a-zA-Z\']+',  # "Smith, John" format
        r'patient\s*1\s*-\s*last\s*name[:\s]*([a-zA-Z\']+)',
    ]
    
    firstname_patterns = [
        r'first\s*name[:\s]*[:-]?\s*([a-zA-Z\']+)',
        r'given\s*name[:\s]*[:-]?\s*([a-zA-Z\']+)',
        r'forename[:\s]*[:-]?\s*([a-zA-Z\']+)',
        r'patient[:\s]*[:-]?\s*[a-zA-Z\']+\s+([a-zA-Z\']+)',
        r'patient\s*-\s*first\s*name[:\s]*([a-zA-Z\']+)',
        # New patterns
        r'[a-zA-Z\']+,\s*([a-zA-Z\']+)',  # "Smith, John" format
        r'patient\s*1\s*-\s*first\s*name[:\s]*([a-zA-Z\']+)',
    ]
    
    # Enhanced DOB patterns
    dob_patterns = [
        # Standard patterns
        r'dob[:\s]*[:-]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        r'date\s*of\s*birth[:\s]*[:-]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        r'birth\s*date[:\s]*[:-]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        r'birthdate[:\s]*[:-]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        r'born[:\s]*[:-]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        # YYYY-MM-DD formats
        r'dob[:\s]*[:-]?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        r'date\s*of\s*birth[:\s]*[:-]?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        r'birth\s*date[:\s]*[:-]?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        # More flexible patterns
        r'dob[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # Just date patterns
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
        matches = re.findall(pattern, text_lower)
        for date_str in matches:
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
        if found_dob:
            break
    
    print(f"   🔍 Found: Last='{found_lastname}', "
          f"First='{found_firstname}', DOB='{found_dob}'")
    
    # If we found name components, try to match with roster
    if found_lastname and found_firstname:
        # Try with DOB if available
        if found_dob:
            key = f"{found_lastname}_{found_firstname}_{found_dob}"
            if key in patients_dict:
                return patients_dict[key]
        
        # Try case-insensitive exact match
        for patient_key, patient_info in patients_dict.items():
            patient_parts = patient_key.split('_')
            if len(patient_parts) >= 3:
                if (patient_parts[0].lower() == found_lastname.lower() and
                        patient_parts[1].lower() == found_firstname.lower()):
                    print(f"   🎯 Matched by name similarity: {patient_info['folder_name']}")
                    return patient_info
    
    return None


def test_content_reading():
    """Test the content reading on our test PDFs"""
    test_folder = Path(r"C:\Users\kulka\Downloads\test_pdfs")
    
    if not test_folder.exists():
        print("❌ Test PDFs folder not found. Run create_test_pdfs.py first")
        return
    
    # Load dummy roster for testing
    patients = {
        "Smith_John_1985-02-14": {
            'folder_name': "Smith, John 02-14-1985",
            'patient_id': 'PAT001'
        },
        "Kumar_Anita_1969-12-12": {
            'folder_name': "Kumar, Anita 12-12-1969", 
            'patient_id': 'PAT002'
        },
        "Nguyen_Linh_1990-07-23": {
            'folder_name': "Nguyen, Linh 07-23-1990",
            'patient_id': 'PAT003'
        }
    }
    
    print("🧪 Testing PDF content reading on test files...")
    
    for pdf_file in test_folder.glob("*.pdf"):
        print(f"\n📄 Testing: {pdf_file.name}")
        
        # Extract text
        text = extract_text_from_pdf_robust(pdf_file)
        if text:
            print(f"   📝 Extracted text length: {len(text)} characters")
            
            # Try to find patient info
            patient_info = find_patient_info_in_text_enhanced(text, patients)
            if patient_info:
                print(f"   ✅ SUCCESS: Matched to {patient_info['folder_name']}")
            else:
                print(f"   ❌ No patient match found")
        else:
            print(f"   ❌ No text extracted")


def organize_with_ultimate_enhancement():
    """
    Ultimate enhanced organizer with test option
    """
    
    print("🚀 ULTIMATE ENHANCED File Organizer")
    print("Choose option:")
    print("1. Process real fake_patient_dataset.zip")
    print("2. Test on sample PDFs")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "2":
        test_content_reading()
        return
    
    # Continue with real processing...
    source_zip = r"C:\Users\kulka\Downloads\fake_patient_dataset.zip"
    dest_folder = r"C:\Users\kulka\Downloads\organized_patients_ultimate"
    
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
        dataset_folder = temp_path / "fake_patient_dataset"
        
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
        print("\n🔄 Processing files with ULTIMATE enhancement...")
        file_count = 0
        copied_count = 0
        unmapped_count = 0
        content_matched_count = 0
        
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.tif', '.tiff']
        
        for file_path in dataset_folder.rglob('*'):
            if (file_path.is_file() and 
                    file_path.suffix.lower() in allowed_extensions):
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
                    
                    key = f"{last_name}_{first_name}_{dob}"
                    
                    if key in patients:
                        matched_patient = patients[key]
                        match_method = "filename"
                        print(f"   ✅ Matched by filename: "
                              f"{matched_patient['folder_name']}")
                
                # STEP 2: If filename parsing failed and it's a PDF, 
                # try content reading
                if (not matched_patient and 
                        file_path.suffix.lower() == '.pdf'):
                    print("   📖 Trying PDF content reading...")
                    pdf_text = extract_text_from_pdf_robust(file_path)
                    
                    if pdf_text:
                        matched_patient = find_patient_info_in_text_enhanced(
                            pdf_text, patients)
                        if matched_patient:
                            match_method = "content"
                            content_matched_count += 1
                            print(f"   🎯 Matched by PDF content: "
                                  f"{matched_patient['folder_name']}")
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
                        doc_type = match.group(4)
                        doc_type = (doc_type.replace('.pdf', '')
                                           .replace('.jpg', '')
                                           .replace('.tif', ''))
                    else:
                        # For content-matched files, try to guess document type
                        doc_type = filename.lower()
                    
                    if 'lab' in doc_type.lower():
                        module_prefix = "Laboratory"
                    elif ('report' in doc_type.lower() or 
                          'summary' in doc_type.lower()):
                        module_prefix = "Reports"
                    elif ('note' in doc_type.lower() or 
                          'visit' in doc_type.lower()):
                        module_prefix = "Clinical_Notes"
                    elif ('photo' in doc_type.lower() or 
                          'image' in doc_type.lower()):
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
                        original_doc_part = filename.replace(
                            f"{last_name}_{first_name}_{dob}_", "")
                        new_filename = f"{module_prefix}_{original_doc_part}"
                    else:
                        # For content-matched files, keep original with prefix
                        new_filename = f"{module_prefix}_{filename}"
                    
                    # Copy file to patient folder
                    dest_file = patient_folder / new_filename
                    shutil.copy2(file_path, dest_file)
                    copied_count += 1
                    
                    print(f"   ✅ COPIED as: {new_filename} "
                          f"(matched by {match_method})")
                    
                else:
                    # Create unmapped folder
                    unmapped_folder = dest_path / "_Unmapped_Files"
                    unmapped_folder.mkdir(exist_ok=True)
                    dest_file = unmapped_folder / filename
                    shutil.copy2(file_path, dest_file)
                    unmapped_count += 1
                    
                    print(f"   ⚠️ UNMAPPED: {filename}")
        
        print(f"\n🎉 ULTIMATE ENHANCEMENT COMPLETE!")
        print(f"📊 Statistics:")
        print(f"   📄 Files processed: {file_count}")
        print(f"   ✅ Files copied to patient folders: {copied_count}")
        print(f"   🎯 Matched by PDF content reading: {content_matched_count}")
        print(f"   ⚠️ Still unmapped: {unmapped_count}")
        
        print(f"\n📁 Check your organized files at:")
        print(f"   {dest_path}")


if __name__ == "__main__":
    organize_with_ultimate_enhancement()