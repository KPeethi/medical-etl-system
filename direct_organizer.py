#!/usr/bin/env python3
"""
Direct File Organizer - Run directly to create subfolders
This script will definitely create patient folders WITH subfolders
"""

import os
import shutil
import zipfile
import pandas as pd
from pathlib import Path
import re
import tempfile

def organize_files_with_subfolders():
    """Organize files into patient folders with proper subfolders"""
    
    source_zip = r"C:\Users\kulka\Downloads\fake_patient_dataset.zip"
    dest_folder = r"C:\Users\kulka\Downloads\organized_patients_with_subfolders"
    
    print(f"🚀 Starting file organization...")
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
        print(f"📦 Extracting ZIP to temporary folder...")
        
        with zipfile.ZipFile(source_zip, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the dataset folder
        temp_path = Path(temp_dir)
        dataset_folder = temp_path / "fake_patient_dataset"
        
        if not dataset_folder.exists():
            print("⚠️ Dataset folder not found, looking for alternatives...")
            subfolders = [f for f in temp_path.iterdir() if f.is_dir()]
            if subfolders:
                dataset_folder = subfolders[0]
                print(f"📂 Using folder: {dataset_folder}")
        
        # Load roster
        roster_file = dataset_folder / "roster.csv"
        patients = {}
        
        if roster_file.exists():
            print("📋 Loading patient roster...")
            df = pd.read_csv(roster_file)
            for _, row in df.iterrows():
                key = f"{row['last_name']}_{row['first_name']}_{row['dob']}"
                patients[key] = {
                    'folder_name': f"{row['last_name']}, {row['first_name']} {row['dob']}",
                    'patient_id': row['patient_id']
                }
            print(f"✅ Loaded {len(patients)} patients from roster")
            
            # Print patient list
            for key, patient in patients.items():
                print(f"   👤 {patient['folder_name']}")
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
                # Pattern: LastName_FirstName_YYYY-MM-DD_document.ext
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
                        # Create patient folder
                        patient_folder = dest_path / patients[key]['folder_name']
                        patient_folder.mkdir(exist_ok=True)
                        print(f"   📁 Patient folder: {patient_folder.name}")
                        
                        # Determine subfolder based on document type
                        if 'lab' in doc_type.lower():
                            subfolder_name = "Laboratory"
                        elif 'report' in doc_type.lower() or 'summary' in doc_type.lower():
                            subfolder_name = "Reports"
                        elif 'note' in doc_type.lower() or 'visit' in doc_type.lower():
                            subfolder_name = "Clinical_Notes"
                        elif 'photo' in doc_type.lower() or 'image' in doc_type.lower():
                            subfolder_name = "Imaging"
                        elif 'invoice' in doc_type.lower():
                            subfolder_name = "Billing"
                        elif 'medrec' in doc_type.lower():
                            subfolder_name = "Medical_Records"
                        else:
                            subfolder_name = "Documents"
                        
                        # Create subfolder INSIDE patient folder
                        subfolder = patient_folder / subfolder_name
                        subfolder.mkdir(exist_ok=True)
                        print(f"   📂 Creating subfolder: {subfolder}")
                        
                        # Copy file to subfolder
                        dest_file = subfolder / filename
                        shutil.copy2(file_path, dest_file)
                        copied_count += 1
                        
                        print(f"   ✅ COPIED to: {patient_folder.name}/{subfolder_name}/{filename}")
                        
                    else:
                        # Create unmapped folder
                        unmapped_folder = dest_path / "_Unmapped_Files"
                        unmapped_folder.mkdir(exist_ok=True)
                        dest_file = unmapped_folder / filename
                        shutil.copy2(file_path, dest_file)
                        unmapped_count += 1
                        
                        print(f"   ⚠️ UNMAPPED: {filename} (patient not found in roster)")
                        
                else:
                    # Create unmapped folder for unparseable filenames
                    unmapped_folder = dest_path / "_Unmapped_Files"
                    unmapped_folder.mkdir(exist_ok=True)
                    dest_file = unmapped_folder / filename
                    shutil.copy2(file_path, dest_file)
                    unmapped_count += 1
                    
                    print(f"   ❌ UNPARSEABLE: {filename}")
        
        print(f"\n🎉 ORGANIZATION COMPLETE!")
        print(f"📊 Statistics:")
        print(f"   📄 Files processed: {file_count}")
        print(f"   ✅ Files copied to patient folders: {copied_count}")
        print(f"   ⚠️ Unmapped files: {unmapped_count}")
        
        print(f"\n📁 Check your organized files at:")
        print(f"   {dest_path}")
        
        # Show folder structure
        print(f"\n📂 Folder structure created:")
        for item in dest_path.iterdir():
            if item.is_dir():
                print(f"   📁 {item.name}/")
                for subitem in item.iterdir():
                    if subitem.is_dir():
                        print(f"      📂 {subitem.name}/")
                        for file in subitem.iterdir():
                            if file.is_file():
                                print(f"         📄 {file.name}")

if __name__ == "__main__":
    organize_files_with_subfolders()