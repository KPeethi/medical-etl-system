#!/usr/bin/env python3
"""
Universal Medical File Organizer API Server
Handles any dataset structure - folders or ZIP files
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


def normalize_date(date_str):
    """Convert various date formats to YYYY-MM-DD for comparison"""
    if not date_str or date_str.strip() == '' or date_str.lower() == 'unknown':
        return None
    
    date_str = date_str.strip()
    
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
    roster_files = []
    
    # Look for common roster file names
    roster_patterns = ['roster.csv', 'patients.csv', 'patient_list.csv', 'roster.xlsx', 'patients.xlsx']
    
    for pattern in roster_patterns:
        for file_path in source_path.rglob(pattern):
            roster_files.append(file_path)
    
    return roster_files[0] if roster_files else None

def load_roster_universal(roster_file):
    """Load roster from CSV or Excel with flexible column names"""
    patients = {}
    
    if not roster_file or not roster_file.exists():
        print("❌ No roster file found - will process files without patient matching")
        return patients
    
    try:
        # Try CSV first
        if roster_file.suffix.lower() == '.csv':
            df = pd.read_csv(roster_file)
        else:
            # Try Excel
            df = pd.read_excel(roster_file)
        
        # Find columns with flexible names
        last_name_col = None
        first_name_col = None
        dob_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ['last', 'surname', 'family']):
                last_name_col = col
            elif any(x in col_lower for x in ['first', 'given', 'forename']):
                first_name_col = col
            elif any(x in col_lower for x in ['dob', 'birth', 'born']):
                dob_col = col
        
        if not all([last_name_col, first_name_col, dob_col]):
            print(f"⚠️ Missing required columns. Found: {df.columns.tolist()}")
            return patients
        
        for _, row in df.iterrows():
            try:
                last_name = str(row[last_name_col]).strip()
                first_name = str(row[first_name_col]).strip()
                dob = str(row[dob_col]).strip()
                
                # Robust date normalization to YYYY-MM-DD
                dob_key = normalize_date(dob)
                if not dob_key:
                    continue  # Skip if date can't be parsed
                
                dob_display = dob  # Keep original for display
                
                key = f"{last_name}_{first_name}_{dob_key}"
                patients[key] = {
                    'folder_name': f"{last_name}, {first_name} {dob_display}",
                    'patient_id': row.get('patient_id', row.get('id', f'PAT_{len(patients)+1}'))
                }
            except Exception as e:
                print(f"⚠️ Error processing row: {e}")
                continue
        
        print(f"✅ Loaded {len(patients)} patients from {roster_file.name}")
        return patients
        
    except Exception as e:
        print(f"❌ Error loading roster: {e}")
        return patients

def organize_universal(source_path, dest_folder):
    """Universal organizer that works with any folder structure"""
    
    results = {
        'processed': 0,
        'copied': 0,
        'unmapped': 0,
        'errors': 0,
        'files_processed': [],
        'source_type': 'unknown'
    }
    
    source_path = Path(source_path)
    dest_path = Path(dest_folder)
    dest_path.mkdir(parents=True, exist_ok=True)
    
    # Handle ZIP files
    if source_path.suffix.lower() == '.zip':
        results['source_type'] = 'zip'
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                with zipfile.ZipFile(source_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                temp_path = Path(temp_dir)
                # Find the main folder in ZIP
                subfolders = [f for f in temp_path.iterdir() if f.is_dir()]
                if subfolders:
                    source_path = subfolders[0]
                else:
                    source_path = temp_path
                
                return process_folder(source_path, dest_path, results)
            except Exception as e:
                results['errors'] += 1
                print(f"❌ Error extracting ZIP: {e}")
                return results
    
    # Handle folders
    elif source_path.is_dir():
        results['source_type'] = 'folder'
        return process_folder(source_path, dest_path, results)
    
    else:
        results['errors'] += 1
        print(f"❌ Source is neither a ZIP file nor a folder: {source_path}")
        return results

def process_folder(source_path, dest_path, results):
    """Process files in a folder"""
    
    # Find roster file
    roster_file = find_roster_file(source_path)
    patients = load_roster_universal(roster_file)
    
    # Find all medical files
    medical_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.doc', '.docx']
    
    for file_path in source_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in medical_extensions:
            results['processed'] += 1
            filename = file_path.name
            
            file_result = {
                'original_filename': filename,
                'action': 'unknown',
                'new_filename': '',
                'patient_folder': ''
            }
            
            # Try to extract patient info from filename
            matched_patient = None
            
            # Pattern 1: LastName_FirstName_DATE_document.ext (flexible date formats)
            pattern1 = r'([A-Za-z\']+)_([A-Za-z]+)_([0-9\-/]+)_(.+)'
            match1 = re.match(pattern1, filename)
            
            if match1 and patients:
                last_name = match1.group(1)
                first_name = match1.group(2)
                dob_raw = match1.group(3)
                doc_type = match1.group(4)
                
                # Normalize the date from filename
                dob_normalized = normalize_date(dob_raw)
                if dob_normalized:
                    key = f"{last_name}_{first_name}_{dob_normalized}"
                    if key in patients:
                        matched_patient = patients[key]
                        doc_type = doc_type.replace(file_path.suffix, '')
            
            # Pattern 2: Try other common patterns
            if not matched_patient:
                # LastName_FirstName_document.ext
                pattern2 = r'([A-Za-z\']+)_([A-Za-z]+)_(.+)'
                match2 = re.match(pattern2, filename)
                
                if match2 and patients:
                    last_name = match2.group(1)
                    first_name = match2.group(2)
                    doc_type = match2.group(3).replace(file_path.suffix, '')
                    
                    # Try to find patient by name only
                    for patient_key, patient_info in patients.items():
                        if (patient_key.startswith(f"{last_name}_{first_name}_")):
                            matched_patient = patient_info
                            break
            
            if matched_patient:
                # Create patient folder
                patient_folder = dest_path / matched_patient['folder_name']
                patient_folder.mkdir(exist_ok=True)
                
                # Determine module prefix
                doc_type_lower = filename.lower()
                if 'lab' in doc_type_lower:
                    module_prefix = "Laboratory"
                elif any(word in doc_type_lower for word in ['report', 'summary']):
                    module_prefix = "Reports"
                elif any(word in doc_type_lower for word in ['note', 'visit']):
                    module_prefix = "Clinical_Notes"
                elif any(word in doc_type_lower for word in ['photo', 'image', 'scan']):
                    module_prefix = "Imaging"
                elif 'invoice' in doc_type_lower:
                    module_prefix = "Billing"
                elif 'record' in doc_type_lower:
                    module_prefix = "Medical_Records"
                else:
                    module_prefix = "Documents"
                
                # Create new filename
                new_filename = f"{module_prefix}_{filename}"
                
                # Copy file
                try:
                    dest_file = patient_folder / new_filename
                    shutil.copy2(file_path, dest_file)
                    results['copied'] += 1
                    
                    file_result.update({
                        'action': 'COPIED',
                        'new_filename': new_filename,
                        'patient_folder': matched_patient['folder_name'],
                        'module': module_prefix
                    })
                except Exception as e:
                    results['errors'] += 1
                    file_result.update({
                        'action': 'ERROR',
                        'error': str(e)
                    })
            
            else:
                # Unmapped file
                unmapped_folder = dest_path / "_Unmapped_Files"
                unmapped_folder.mkdir(exist_ok=True)
                
                try:
                    dest_file = unmapped_folder / filename
                    shutil.copy2(file_path, dest_file)
                    results['unmapped'] += 1
                    
                    file_result.update({
                        'action': 'UNMAPPED',
                        'reason': 'Patient not found or no roster available'
                    })
                except Exception as e:
                    results['errors'] += 1
                    file_result.update({
                        'action': 'ERROR',
                        'error': str(e)
                    })
            
            results['files_processed'].append(file_result)
    
    return results

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Universal Medical File Organizer API ready',
        'version': 'universal-v1.0',
        'supported_formats': ['ZIP files', 'Folders', 'CSV/Excel rosters'],
        'supported_files': ['.pdf', '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.doc', '.docx']
    })

@app.route('/api/process', methods=['POST'])
def process_files():
    try:
        # Handle file upload or JSON
        if request.files:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided. Upload a ZIP file with key "file"'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Save uploaded file temporarily
            temp_file_path = f"temp_upload_{uuid.uuid4().hex}{Path(file.filename).suffix}"
            file.save(temp_file_path)
            
            source_path = temp_file_path
            dest_path = "/path/to/organized_universal"
            dry_run = False
            
        else:
            # Handle JSON data
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data or file provided'}), 400
            
            source_path = data.get('source')
            dest_path = data.get('dest')
            dry_run = data.get('dry_run', True)
            
            if not source_path or not dest_path:
                return jsonify({'error': 'source and dest are required'}), 400
            
            # Check if source exists
            source_check = Path(source_path)
            if not source_check.exists():
                return jsonify({
                    'error': f'Source not found: {source_path}',
                    'suggestion': 'Please check the path exists and is accessible',
                    'checked_path': str(source_check.absolute())
                }), 400
        
        if dry_run:
            return jsonify({
                'status': 'success',
                'mode': 'DRY_RUN',
                'message': 'DRY RUN: Would organize medical files from any source',
                'source': source_path,
                'destination': dest_path,
                'features': [
                    'Auto-detects ZIP files or folders',
                    'Finds roster files automatically',
                    'Supports flexible filename patterns',
                    'Creates flat patient folder structure'
                ]
            })
        
        # Process files
        processing_results = organize_universal(source_path, dest_path)
        
        run_id = str(uuid.uuid4())[:8]
        
        response_data = {
            'status': 'success',
            'mode': 'REAL_RUN',
            'run_id': f'universal-run-{run_id}',
            'source': source_path if not request.files else f'uploaded_{Path(source_path).name}',
            'destination': dest_path,
            'source_type': processing_results['source_type'],
            'stats': {
                'processed': processing_results['processed'],
                'copied': processing_results['copied'],
                'unmapped': processing_results['unmapped'],
                'errors': processing_results['errors']
            },
            'files_processed': processing_results['files_processed'][:10],
            'message': f'Successfully organized {processing_results["copied"]} files!',
            'folder_created': str(Path(dest_path).exists())
        }
        
        # Clean up temporary file
        if request.files and Path(source_path).exists():
            try:
                os.unlink(source_path)
            except Exception:
                pass
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Processing failed'
        }), 500

if __name__ == '__main__':
    print("🌍 Universal Medical File Organizer API Server")
    print("URL: http://127.0.0.1:8080")
    print("Features:")
    print("  ✅ Handles any folder structure or ZIP file")
    print("  ✅ Auto-detects roster files (CSV/Excel)")
    print("  ✅ Flexible filename patterns")
    print("  ✅ Flat patient folder organization")
    
    app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)