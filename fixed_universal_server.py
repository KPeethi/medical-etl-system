#!/usr/bin/env python3
"""
Fixed Universal Medical File Organizer API Server
Handles date format mismatches between filenames and roster
"""

import os
import shutil
import zipfile
import pandas as pd
from pathlib import Path
import re
import tempfile
from flask import Flask, jsonify, request

app = Flask(__name__)


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
        
        print(f"✅ Found columns: {last_name_col}, {first_name_col}, {dob_col}")
        
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
                    print(f"  Loaded: {key}")
                else:
                    print(f"  Skipped: {last_name} {first_name} {dob_raw} (normalization failed)")
            except Exception as e:
                print(f"  Error processing row: {e}")
                continue
        
        print(f"✅ Loaded {len(patients)} patients from roster")
        return patients
        
    except Exception as e:
        print(f"❌ Error loading roster: {e}")
        return patients


def extract_patient_from_filename(filename):
    """Extract patient info from filename with flexible date parsing"""
    filename_base = os.path.splitext(filename)[0]
    
    # Pattern 1: LastName_FirstName_DATE_document
    pattern1 = r'([A-Za-z\']+)_([A-Za-z\']+)_([0-9\-/]+)_(.+)'
    match = re.match(pattern1, filename_base)
    
    if match:
        last_name = match.group(1)
        first_name = match.group(2)
        dob_raw = match.group(3)
        doc_type = match.group(4)
        
        dob_normalized = normalize_date(dob_raw)
        if dob_normalized:
            return last_name, first_name, dob_normalized, doc_type
    
    return None, None, None, None


def organize_files_fixed(dataset_path, output_path="FIXED_OUTPUT"):
    """Organize files with date normalization fix"""
    
    results = {
        "total_files": 0,
        "organized": 0,
        "unmapped": 0,
        "details": []
    }
    
    try:
        # Handle ZIP files
        if dataset_path.endswith('.zip'):
            temp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(dataset_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            source_path = Path(temp_dir)
        else:
            source_path = Path(dataset_path)
        
        print(f"📁 Processing: {source_path}")
        
        # Find and load roster
        roster_file = find_roster_file(source_path)
        if not roster_file:
            return {"error": "No roster file found"}
        
        print(f"📋 Found roster: {roster_file}")
        patients = load_roster_with_date_fix(roster_file)
        
        if not patients:
            return {"error": "Could not load patient data from roster"}
        
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
        
        results["total_files"] = len(all_files)
        print(f"📄 Found {len(all_files)} files to process")
        
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
                        results["organized"] += 1
                        results["details"].append({
                            "file": filename,
                            "status": "organized",
                            "patient": f"{first_name} {last_name}",
                            "dob": patient_info['dob_original'],
                            "folder": patient_info['folder_name']
                        })
                        print(f"✅ Organized: {filename} → {patient_info['folder_name']}")
                    except Exception as e:
                        print(f"❌ Copy error: {filename} - {e}")
                        # Fall back to unmapped
                        shutil.copy2(file_path, unmapped_dir / filename)
                        results["unmapped"] += 1
                else:
                    # No patient match found
                    shutil.copy2(file_path, unmapped_dir / filename)
                    results["unmapped"] += 1
                    results["details"].append({
                        "file": filename,
                        "status": "unmapped",
                        "reason": f"No patient found for {last_name}, {first_name}, {dob_normalized}"
                    })
                    print(f"❓ Unmapped: {filename} (no match for {patient_key})")
            else:
                # Could not parse filename
                shutil.copy2(file_path, unmapped_dir / filename)
                results["unmapped"] += 1
                results["details"].append({
                    "file": filename,
                    "status": "unmapped",
                    "reason": "Could not parse patient info from filename"
                })
                print(f"❓ Unmapped: {filename} (parse failed)")
        
        # Clean up temp directory if we created one
        if dataset_path.endswith('.zip'):
            shutil.rmtree(temp_dir)
        
        print(f"🎉 Complete! Organized: {results['organized']}, Unmapped: {results['unmapped']}")
        return results
        
    except Exception as e:
        return {"error": f"Processing failed: {str(e)}"}


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Fixed Universal Medical File Organizer",
        "version": "date-fix-1.0"
    })


@app.route('/organize', methods=['POST'])
def organize():
    try:
        data = request.get_json()
        
        if not data or 'dataset_path' not in data:
            return jsonify({"error": "Missing dataset_path"}), 400
        
        dataset_path = data['dataset_path']
        output_path = data.get('output_base', 'FIXED_OUTPUT')
        
        if not os.path.exists(dataset_path):
            return jsonify({"error": f"Dataset path not found: {dataset_path}"}), 400
        
        # Process the dataset
        results = organize_files_fixed(dataset_path, output_path)
        
        if "error" in results:
            return jsonify(results), 500
        
        return jsonify({
            "status": "success",
            "message": f"Processed {results['total_files']} files. {results['organized']} organized, {results['unmapped']} unmapped.",
            "results": results
        })
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


if __name__ == '__main__':
    print("🚀 Fixed Universal Medical File Organizer API Server")
    print("🔧 Features:")
    print("   ✅ Robust date format normalization")
    print("   ✅ Handles MM/DD/YYYY, YYYY-MM-DD, MM-DD-YYYY, etc.")
    print("   ✅ Flexible roster column detection")
    print("   ✅ ZIP file support")
    print("🌐 Server running on http://localhost:8080")
    print("📋 Endpoints:")
    print("   GET  /health")
    print("   POST /organize")
    app.run(host='0.0.0.0', port=8080, debug=False)