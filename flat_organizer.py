#!/usr/bin/env python3
"""
Flat File Organizer - No subfolders, just patient folders with prefixed filenames
"""

import os
import shutil
import zipfile
import pandas as pd
from pathlib import Path
import re
import tempfile

def organize_files_flat_structure():
    """Organize files into patient folders WITHOUT subfolders - flat structure with prefixed filenames"""
    
    source_zip = r"C:\Users\kulka\Downloads\fake_patient_dataset.zip"
    dest_folder = r"C:\Users\kulka\Downloads\organized_patients_flat"
    
    print(f"🚀 Starting FLAT file organization...")
    print(f"📦 Source: {source_zip}")
    print(f"📁 Destination: {dest_folder}")
    print(f"📋 Structure: Patient folders → prefixed files (NO subfolders)")
    
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
        print(f"📦 Extracting ZIP to temporary folder...")
        
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
                    'folder_name': f"{row['last_name']}, {row['first_name']} {formatted_dob}",
                    'patient_id': row['patient_id']
                }
            print(f"✅ Loaded {len(patients)} patients from roster")
        else:
            print(f"❌ ERROR: Roster file not found: {roster_file}")
            return
        
        # Process all files
        print(f"\n🔄 Processing files...")
        file_count = 0
        copied_count = 0
        unmapped_count = 0
        
        for file_path in dataset_folder.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.jpg', '.jpeg', '.tif', '.tiff']:
                file_count += 1
                filename = file_path.name
                print(f"\n📄 File {file_count}: {filename}")
                
                # Extract patient info from filename
                pattern = r'([A-Za-z\']+)_([A-Za-z]+)_(\d{4}-\d{2}-\d{2})_(.+)'
                match = re.match(pattern, filename)
                
                if match:
                    last_name = match.group(1)
                    first_name = match.group(2)
                    dob = match.group(3)
                    doc_type = match.group(4).replace('.pdf', '').replace('.jpg', '').replace('.tif', '')
                    
                    print(f"   🔍 Parsed: {last_name}, {first_name} ({dob}) - {doc_type}")
                    
                    key = f"{last_name}_{first_name}_{dob}"
                    
                    if key in patients:
                        # Create patient folder (no subfolders!)
                        patient_folder = dest_path / patients[key]['folder_name']
                        patient_folder.mkdir(exist_ok=True)
                        print(f"   📁 Patient folder: {patient_folder.name}")
                        
                        # Determine module prefix based on document type
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
                        
                        # Create new filename with module prefix but WITHOUT patient name
                        # Remove patient name part from original filename
                        original_doc_part = filename.replace(f"{last_name}_{first_name}_{dob}_", "")
                        new_filename = f"{module_prefix}_{original_doc_part}"
                        
                        # Copy file DIRECTLY to patient folder with prefixed name
                        dest_file = patient_folder / new_filename
                        shutil.copy2(file_path, dest_file)
                        copied_count += 1
                        
                        print(f"   ✅ COPIED as: {new_filename}")
                        
                    else:
                        # Create unmapped folder
                        unmapped_folder = dest_path / "_Unmapped_Files"
                        unmapped_folder.mkdir(exist_ok=True)
                        dest_file = unmapped_folder / filename
                        shutil.copy2(file_path, dest_file)
                        unmapped_count += 1
                        
                        print(f"   ⚠️ UNMAPPED: {filename}")
                        
                else:
                    # Unmapped for unparseable filenames
                    unmapped_folder = dest_path / "_Unmapped_Files"
                    unmapped_folder.mkdir(exist_ok=True)
                    dest_file = unmapped_folder / filename
                    shutil.copy2(file_path, dest_file)
                    unmapped_count += 1
                    
                    print(f"   ❌ UNPARSEABLE: {filename}")
        
        print(f"\n🎉 FLAT ORGANIZATION COMPLETE!")
        print(f"📊 Statistics:")
        print(f"   📄 Files processed: {file_count}")
        print(f"   ✅ Files copied to patient folders: {copied_count}")
        print(f"   ⚠️ Unmapped files: {unmapped_count}")
        
        print(f"\n📁 Check your organized files at:")
        print(f"   {dest_path}")
        
        # Show folder structure
        print(f"\n📂 FLAT folder structure created (NO subfolders):")
        for item in dest_path.iterdir():
            if item.is_dir():
                print(f"   📁 {item.name}/")
                for file in item.iterdir():
                    if file.is_file():
                        print(f"      📄 {file.name}")

if __name__ == "__main__":
    organize_files_flat_structure()