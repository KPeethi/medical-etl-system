#!/usr/bin/env python3
"""
Flat Organizer API Server - Works with Postman
Actually processes files with flat structure (no subfolders)
"""

import os
import shutil
import zipfile
import pandas as pd
from pathlib import Path
import re
import tempfile
import uuid
from flask import Flask, jsonify, request

app = Flask(__name__)

def organize_files_api(source_zip, dest_folder):
    """API version of the flat organizer"""
    
    results = {
        'processed': 0,
        'copied': 0,
        'unmapped': 0,
        'errors': 0,
        'files_processed': []
    }
    
    # Create destination folder
    dest_path = Path(dest_folder)
    dest_path.mkdir(parents=True, exist_ok=True)
    
    # Extract ZIP to temp location
    with tempfile.TemporaryDirectory() as temp_dir:
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
        
        # Process all files
        for file_path in dataset_folder.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.jpg', '.jpeg', '.tif', '.tiff']:
                results['processed'] += 1
                filename = file_path.name
                
                # Extract patient info from filename
                pattern = r'([A-Za-z\']+)_([A-Za-z]+)_(\d{4}-\d{2}-\d{2})_(.+)'
                match = re.match(pattern, filename)
                
                file_result = {
                    'original_filename': filename,
                    'action': 'unknown',
                    'new_filename': '',
                    'patient_folder': ''
                }
                
                if match:
                    last_name = match.group(1)
                    first_name = match.group(2)
                    dob = match.group(3)
                    doc_type = match.group(4).replace('.pdf', '').replace('.jpg', '').replace('.tif', '')
                    
                    key = f"{last_name}_{first_name}_{dob}"
                    
                    if key in patients:
                        # Create patient folder
                        patient_folder = dest_path / patients[key]['folder_name']
                        patient_folder.mkdir(exist_ok=True)
                        
                        # Determine module prefix
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
                        
                        # Create new filename WITHOUT patient name
                        original_doc_part = filename.replace(f"{last_name}_{first_name}_{dob}_", "")
                        new_filename = f"{module_prefix}_{original_doc_part}"
                        
                        # Copy file to patient folder
                        dest_file = patient_folder / new_filename
                        shutil.copy2(file_path, dest_file)
                        results['copied'] += 1
                        
                        file_result.update({
                            'action': 'COPIED',
                            'new_filename': new_filename,
                            'patient_folder': patients[key]['folder_name'],
                            'module': module_prefix
                        })
                    else:
                        # Unmapped
                        unmapped_folder = dest_path / "_Unmapped_Files"
                        unmapped_folder.mkdir(exist_ok=True)
                        dest_file = unmapped_folder / filename
                        shutil.copy2(file_path, dest_file)
                        results['unmapped'] += 1
                        
                        file_result.update({
                            'action': 'UNMAPPED',
                            'reason': 'Patient not found in roster'
                        })
                else:
                    # Unparseable
                    unmapped_folder = dest_path / "_Unmapped_Files"
                    unmapped_folder.mkdir(exist_ok=True)
                    dest_file = unmapped_folder / filename
                    shutil.copy2(file_path, dest_file)
                    results['unmapped'] += 1
                    
                    file_result.update({
                        'action': 'UNPARSEABLE',
                        'reason': 'Could not parse filename format'
                    })
                
                results['files_processed'].append(file_result)
    
    return results

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Flat organizer API ready for Postman',
        'version': 'flat-structure-api'
    })

@app.route('/api/process', methods=['POST'])
def process_files():
    try:
        # Check if it's a file upload or JSON data
        if request.files:
            # Handle file upload from Postman
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided. Upload a ZIP file with key "file"'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if not file.filename.endswith('.zip'):
                return jsonify({'error': 'Please upload a ZIP file'}), 400
            
            # Save uploaded file temporarily
            temp_zip_path = f"temp_upload_{uuid.uuid4().hex}.zip"
            file.save(temp_zip_path)
            
            # Set default destination
            dest_path = "organized_patients_api"
            dry_run = False  # Real processing for file uploads
            
        else:
            # Handle JSON data (original way)
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No JSON data or file provided. Either upload a ZIP file or send JSON with source/dest paths'}), 400
            
            temp_zip_path = data.get('source')
            dest_path = data.get('dest')
            dry_run = data.get('dry_run', True)
            
            if not temp_zip_path or not dest_path:
                return jsonify({'error': 'source and dest are required in JSON mode'}), 400
            
            if not Path(temp_zip_path).exists():
                return jsonify({'error': f'Source file not found: {temp_zip_path}'}), 400
        
        if dry_run:
            return jsonify({
                'status': 'success',
                'mode': 'DRY_RUN',
                'message': 'DRY RUN: Would organize files with flat structure',
                'structure': 'Patient folders → Module_filename.pdf (NO subfolders)',
                'example': 'LastName, FirstName YYYY-MM-DD/Module_filename.pdf',
                'source': temp_zip_path,
                'destination': dest_path,
                'note': 'Set dry_run to false to actually create organized folders'
            })
        
        # Actually process files
        processing_results = organize_files_api(temp_zip_path, dest_path)
        
        run_id = str(uuid.uuid4())[:8]
        
        response_data = {
            'status': 'success',
            'mode': 'REAL_RUN',
            'run_id': f'flat-run-{run_id}',
            'source': temp_zip_path if not request.files else 'uploaded_file.zip',
            'destination': dest_path,
            'structure': 'FLAT - Patient folders with prefixed files (NO subfolders)',
            'stats': {
                'processed': processing_results['processed'],
                'copied': processing_results['copied'],
                'unmapped': processing_results['unmapped'],
                'errors': processing_results['errors']
            },
            'files_processed': processing_results['files_processed'][:10],  # First 10
            'message': f'Successfully organized {processing_results["copied"]} files into flat patient folders!',
            'folder_created': str(Path(dest_path).exists())
        }
        
        # Clean up temporary file if it was uploaded
        if request.files and Path(temp_zip_path).exists():
            try:
                os.unlink(temp_zip_path)
            except:
                pass
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Processing failed'
        }), 500

if __name__ == '__main__':
    print("📁 Flat Organizer API Server for Postman")
    print("URL: http://127.0.0.1:8080")
    print("Structure: Patient folders → Module_filename.pdf (NO subfolders)")
    
    app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)