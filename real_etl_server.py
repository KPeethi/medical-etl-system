#!/usr/bin/env python3
"""
Real ETL Server - Actually processes files
"""

import os
import sys
import json
import tempfile
import shutil
import zipfile
import pandas as pd
from pathlib import Path
from flask import Flask, jsonify, request
import re
from datetime import datetime
import uuid

app = Flask(__name__)

def extract_patient_info_from_filename(filename):
    """Extract patient info from filename like 'Smith_John_1985-02-14_lab_1.pdf'"""
    # Pattern: LastName_FirstName_YYYY-MM-DD_document.ext
    pattern = r'([A-Za-z\']+)_([A-Za-z]+)_(\d{4}-\d{2}-\d{2})_(.+)'
    match = re.match(pattern, filename)
    
    if match:
        return {
            'last_name': match.group(1),
            'first_name': match.group(2), 
            'dob': match.group(3),
            'document_type': match.group(4).replace('.pdf', '').replace('.jpg', '').replace('.tif', '')
        }
    return None

def load_roster(roster_path):
    """Load patient roster from CSV"""
    try:
        df = pd.read_csv(roster_path)
        patients = {}
        for _, row in df.iterrows():
            key = f"{row['last_name'].lower()}_{row['first_name'].lower()}_{row['dob']}"
            patients[key] = {
                'patient_id': row['patient_id'],
                'last_name': row['last_name'],
                'first_name': row['first_name'],
                'dob': row['dob'],
                'mrn': row['mrn']
            }
        return patients
    except Exception as e:
        print(f"Error loading roster: {e}")
        return {}

def process_files_real(source_path, dest_path, dry_run=True):
    """Actually process the files"""
    results = {
        'processed': 0,
        'copied': 0,
        'skipped': 0,
        'unmapped': 0,
        'errors': 0,
        'files_processed': []
    }
    
    source = Path(source_path)
    dest = Path(dest_path)
    
    # Create temp extraction directory
    with tempfile.TemporaryDirectory() as temp_dir:
        if source.suffix.lower() == '.zip':
            # Extract ZIP
            with zipfile.ZipFile(source, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find the actual data directory
            temp_path = Path(temp_dir)
            data_dirs = list(temp_path.glob('**/'))
            if data_dirs:
                work_dir = data_dirs[0] if len(data_dirs) == 1 else temp_path
            else:
                work_dir = temp_path
        else:
            work_dir = source
        
        # Look for roster file
        roster_file = None
        for roster_name in ['roster.csv', 'patients.csv', 'patient_roster.csv']:
            roster_path = work_dir / roster_name
            if roster_path.exists():
                roster_file = roster_path
                break
        
        patients = {}
        if roster_file:
            patients = load_roster(roster_file)
            print(f"Loaded {len(patients)} patients from roster")
        
        # Process all files
        for file_path in work_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.jpg', '.jpeg', '.tif', '.tiff', '.png']:
                results['processed'] += 1
                
                filename = file_path.name
                patient_info = extract_patient_info_from_filename(filename)
                
                file_result = {
                    'filename': filename,
                    'source_path': str(file_path),
                    'action': 'unknown',
                    'patient_info': patient_info
                }
                
                if patient_info:
                    # Try to match with roster
                    key = f"{patient_info['last_name'].lower()}_{patient_info['first_name'].lower()}_{patient_info['dob']}"
                    
                    if key in patients:
                        patient = patients[key]
                        
                        # Create patient directory
                        patient_dir = dest / f"{patient['last_name']}, {patient['first_name']} {patient['dob']}"
                        
                        # Determine document type/module
                        doc_type = patient_info['document_type']
                        if 'lab' in doc_type.lower():
                            module_dir = patient_dir / 'Laboratory'
                        elif 'report' in doc_type.lower() or 'summary' in doc_type.lower():
                            module_dir = patient_dir / 'Reports'
                        elif 'note' in doc_type.lower() or 'visit' in doc_type.lower():
                            module_dir = patient_dir / 'Clinical_Notes'
                        elif 'photo' in doc_type.lower() or 'image' in doc_type.lower():
                            module_dir = patient_dir / 'Imaging'
                        else:
                            module_dir = patient_dir / 'Documents'
                        
                        if not dry_run:
                            # Actually create directories and copy file
                            module_dir.mkdir(parents=True, exist_ok=True)
                            dest_file = module_dir / filename
                            shutil.copy2(file_path, dest_file)
                        
                        file_result['action'] = 'COPY'
                        file_result['destination'] = str(module_dir / filename)
                        file_result['patient'] = patient
                        results['copied'] += 1
                    else:
                        file_result['action'] = 'UNMAPPED'
                        results['unmapped'] += 1
                else:
                    file_result['action'] = 'UNMAPPED'
                    results['unmapped'] += 1
                
                results['files_processed'].append(file_result)
    
    return results

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Real ETL server is running',
        'server': 'real-processing'
    })

@app.route('/api/process', methods=['POST'])
def process_files():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        source_path = data.get('source')
        dest_path = data.get('dest')
        dry_run = data.get('dry_run', True)
        
        if not source_path or not dest_path:
            return jsonify({'error': 'source and dest are required'}), 400
        
        source = Path(source_path)
        if not source.exists():
            return jsonify({
                'error': f'Source path does not exist: {source_path}'
            }), 400
        
        # Process the files
        processing_results = process_files_real(source_path, dest_path, dry_run)
        
        run_id = str(uuid.uuid4())[:8]
        
        result = {
            'status': 'success',
            'run_id': f'real-run-{run_id}',
            'mode': 'DRY_RUN' if dry_run else 'REAL_RUN',
            'source': source_path,
            'destination': dest_path,
            'stats': {
                'processed': processing_results['processed'],
                'copied': processing_results['copied'],
                'skipped': processing_results['skipped'],
                'unmapped': processing_results['unmapped'],
                'errors': processing_results['errors']
            },
            'files_processed': processing_results['files_processed'][:10],  # First 10 for brevity
            'message': f'{"DRY RUN: Would process" if dry_run else "Successfully processed"} {processing_results["processed"]} files',
            'destination_created': not dry_run and Path(dest_path).exists()
        }
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Processing failed'
        }), 500

if __name__ == '__main__':
    print("🏥 Real ETL Server Starting...")
    print("URL: http://127.0.0.1:8080")
    print("This server will ACTUALLY process your files!")
    
    app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)