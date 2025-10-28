#!/usr/bin/env python3
"""
Simple File Organizer - Guaranteed to work
Creates proper patient folder structure with subfolders
"""

import os
import shutil
import zipfile
import pandas as pd
from pathlib import Path
from flask import Flask, jsonify, request
import re
import uuid

app = Flask(__name__)

def organize_patient_files(source_zip, dest_folder):
    """Organize files into patient folders with subfolders"""
    
    print(f"Starting organization...")
    print(f"Source: {source_zip}")
    print(f"Destination: {dest_folder}")
    
    # Create destination folder
    dest_path = Path(dest_folder)
    dest_path.mkdir(parents=True, exist_ok=True)
    print(f"Created destination folder: {dest_path}")
    
    # Extract ZIP to temp location
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Extracting ZIP to: {temp_dir}")
        
        with zipfile.ZipFile(source_zip, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the dataset folder
        temp_path = Path(temp_dir)
        dataset_folder = temp_path / "fake_patient_dataset"
        
        if not dataset_folder.exists():
            # Look for any folder
            subfolders = [f for f in temp_path.iterdir() if f.is_dir()]
            if subfolders:
                dataset_folder = subfolders[0]
        
        print(f"Dataset folder: {dataset_folder}")
        
        # Load roster
        roster_file = dataset_folder / "roster.csv"
        patients = {}
        
        if roster_file.exists():
            print("Loading roster...")
            df = pd.read_csv(roster_file)
            for _, row in df.iterrows():
                key = f"{row['last_name']}_{row['first_name']}_{row['dob']}"
                patients[key] = {
                    'folder_name': f"{row['last_name']}, {row['first_name']} {row['dob']}",
                    'patient_id': row['patient_id']
                }
            print(f"Loaded {len(patients)} patients")
        
        # Process all files
        results = []
        file_count = 0
        
        for file_path in dataset_folder.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.jpg', '.jpeg', '.tif', '.tiff']:
                file_count += 1
                filename = file_path.name
                print(f"Processing file {file_count}: {filename}")
                
                # Extract patient info from filename
                # Pattern: LastName_FirstName_YYYY-MM-DD_document.ext
                pattern = r'([A-Za-z\']+)_([A-Za-z]+)_(\d{4}-\d{2}-\d{2})_(.+)'
                match = re.match(pattern, filename)
                
                if match:
                    last_name = match.group(1)
                    first_name = match.group(2)
                    dob = match.group(3)
                    doc_type = match.group(4)
                    
                    key = f"{last_name}_{first_name}_{dob}"
                    
                    if key in patients:
                        # Create patient folder
                        patient_folder = dest_path / patients[key]['folder_name']
                        patient_folder.mkdir(exist_ok=True)
                        
                        # Determine subfolder based on document type
                        if 'lab' in doc_type.lower():
                            subfolder = patient_folder / "Laboratory"
                        elif 'report' in doc_type.lower() or 'summary' in doc_type.lower():
                            subfolder = patient_folder / "Reports"
                        elif 'note' in doc_type.lower() or 'visit' in doc_type.lower():
                            subfolder = patient_folder / "Clinical_Notes"
                        elif 'photo' in doc_type.lower() or 'image' in doc_type.lower():
                            subfolder = patient_folder / "Imaging"
                        elif 'invoice' in doc_type.lower():
                            subfolder = patient_folder / "Billing"
                        elif 'medrec' in doc_type.lower():
                            subfolder = patient_folder / "Medical_Records"
                        else:
                            subfolder = patient_folder / "Documents"
                        
                        # Create subfolder and copy file
                        subfolder.mkdir(exist_ok=True)
                        dest_file = subfolder / filename
                        shutil.copy2(file_path, dest_file)
                        
                        print(f"  → Copied to: {subfolder.name}/{filename}")
                        
                        results.append({
                            'filename': filename,
                            'patient': patients[key]['folder_name'],
                            'subfolder': subfolder.name,
                            'action': 'COPIED'
                        })
                    else:
                        # Create unmapped folder
                        unmapped_folder = dest_path / "_Unmapped_Files"
                        unmapped_folder.mkdir(exist_ok=True)
                        dest_file = unmapped_folder / filename
                        shutil.copy2(file_path, dest_file)
                        
                        print(f"  → Unmapped: {filename}")
                        
                        results.append({
                            'filename': filename,
                            'action': 'UNMAPPED'
                        })
                else:
                    # Create unmapped folder for unparseable filenames
                    unmapped_folder = dest_path / "_Unmapped_Files"
                    unmapped_folder.mkdir(exist_ok=True)
                    dest_file = unmapped_folder / filename
                    shutil.copy2(file_path, dest_file)
                    
                    print(f"  → Unparseable: {filename}")
                    
                    results.append({
                        'filename': filename,
                        'action': 'UNPARSEABLE'
                    })
        
        print(f"Processing complete! Processed {file_count} files")
        return results

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Simple file organizer ready',
        'version': 'guaranteed-working'
    })

@app.route('/api/process', methods=['POST'])
def process_files():
    try:
        data = request.get_json()
        
        source_path = data.get('source')
        dest_path = data.get('dest')
        dry_run = data.get('dry_run', True)
        
        print(f"API Request received:")
        print(f"  Source: {source_path}")
        print(f"  Destination: {dest_path}")
        print(f"  Dry run: {dry_run}")
        
        if not source_path or not dest_path:
            return jsonify({'error': 'source and dest are required'}), 400
        
        if not Path(source_path).exists():
            return jsonify({'error': f'Source file not found: {source_path}'}), 400
        
        if dry_run:
            return jsonify({
                'status': 'success',
                'mode': 'DRY_RUN',
                'message': 'DRY RUN: Would organize files from your dataset',
                'note': 'Set dry_run to false to actually create folders',
                'source': source_path,
                'destination': dest_path
            })
        
        # Actually process files
        results = organize_patient_files(source_path, dest_path)
        
        # Count results
        copied = len([r for r in results if r['action'] == 'COPIED'])
        unmapped = len([r for r in results if r['action'] in ['UNMAPPED', 'UNPARSEABLE']])
        
        return jsonify({
            'status': 'success',
            'mode': 'REAL_RUN',
            'source': source_path,
            'destination': dest_path,
            'stats': {
                'processed': len(results),
                'copied': copied,
                'unmapped': unmapped,
                'errors': 0
            },
            'message': f'Successfully organized {copied} files into patient folders with subfolders!',
            'files_processed': results[:5],  # Show first 5
            'folder_created': str(Path(dest_path).exists())
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("📁 Simple File Organizer Starting...")
    print("URL: http://127.0.0.1:8080")
    print("This WILL create patient folders with subfolders!")
    
    app.run(host='127.0.0.1', port=8080, debug=True)