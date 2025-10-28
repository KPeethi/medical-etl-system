#!/usr/bin/env python3
"""
Medical ETL Review Queue UI
Flask web application for managing unmapped files and duplicates
"""

import os
import sys
import psycopg2
import json
import tempfile
import shutil
import zipfile
import pandas as pd
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from datetime import datetime
import argparse
from config_validator import validate_config, check_high_unmapped_rate
from roster_autodetect import autodetect_columns, get_sample_data

# Add router_service to path
router_service_path = os.path.join(os.path.dirname(__file__), '..', 'router_service')
sys.path.insert(0, router_service_path)

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL)

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

def parse_state_practice_from_path(path):
    """Parse state and practice from path like \\mrm-fileserver\\practice records\\TX\\Alexander_OBGYN"""
    if not path:
        return None, None
    
    path_str = str(path).replace('\\', '/').replace('//', '/')
    
    parts = path_str.split('/')
    
    for i, part in enumerate(parts):
        if 'practice' in part.lower() and 'records' in part.lower():
            if i + 1 < len(parts):
                state = parts[i + 1]
                if i + 2 < len(parts):
                    practice = parts[i + 2]
                    return state, practice
    
    return None, None

@app.route('/api/stats')
def get_stats():
    """Get overall statistics including states and practices"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                COUNT(DISTINCT RunID) as total_runs,
                COUNT(*) as total_files,
                COUNT(CASE WHEN Action = 'COPY' THEN 1 END) as copied,
                COUNT(CASE WHEN Action LIKE 'SKIP%' THEN 1 END) as skipped,
                COUNT(CASE WHEN Action = 'MOVE_TO_UNMAPPED' THEN 1 END) as unmapped,
                COUNT(CASE WHEN Action = 'MOVE_TO_BAD_DOB' THEN 1 END) as bad_dob,
                COUNT(CASE WHEN Action = 'ERROR' THEN 1 END) as errors
            FROM FACT_FileProcessing
        """)
        
        row = cur.fetchone()
        
        cur.execute("""
            SELECT DISTINCT SourcePath FROM FACT_FileProcessing 
            WHERE SourcePath IS NOT NULL
        """)
        
        paths = cur.fetchall()
        states_set = set()
        practices_set = set()
        
        for (path,) in paths:
            state, practice = parse_state_practice_from_path(path)
            if state:
                states_set.add(state)
            if practice:
                practices_set.add(practice)
        
        stats = {
            'states': len(states_set),
            'practices': len(practices_set),
            'total_runs': row[0] or 0,
            'total_files': row[1] or 0,
            'copied': row[2] or 0,
            'skipped': row[3] or 0,
            'unmapped': row[4] or 0,
            'bad_dob': row[5] or 0,
            'errors': row[6] or 0
        }
        
        cur.close()
        conn.close()
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/practice-stats')
def get_practice_stats():
    """Get statistics broken down by state and practice"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT SourcePath, Action 
            FROM FACT_FileProcessing 
            WHERE SourcePath IS NOT NULL
        """)
        
        rows = cur.fetchall()
        
        practice_data = {}
        
        for source_path, action in rows:
            state, practice = parse_state_practice_from_path(source_path)
            if not state or not practice:
                continue
            
            key = f"{state}|{practice}"
            if key not in practice_data:
                practice_data[key] = {
                    'state': state,
                    'practice': practice,
                    'scanned': 0,
                    'copied': 0,
                    'unmapped': 0,
                    'errors': 0
                }
            
            practice_data[key]['scanned'] += 1
            
            if action == 'COPY':
                practice_data[key]['copied'] += 1
            elif action == 'MOVE_TO_UNMAPPED':
                practice_data[key]['unmapped'] += 1
            elif action == 'ERROR':
                practice_data[key]['errors'] += 1
        
        result = sorted(practice_data.values(), key=lambda x: (x['state'], x['practice']))
        
        cur.close()
        conn.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/states')
def get_states():
    """Get list of all states with file statistics"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT SourcePath, Action 
            FROM FACT_FileProcessing 
            WHERE SourcePath IS NOT NULL
        """)
        
        rows = cur.fetchall()
        
        state_data = {}
        
        for source_path, action in rows:
            state, practice = parse_state_practice_from_path(source_path)
            if not state:
                continue
            
            if state not in state_data:
                state_data[state] = {
                    'state': state,
                    'total_files': 0,
                    'copied': 0,
                    'unmapped': 0,
                    'errors': 0,
                    'practices': set()
                }
            
            state_data[state]['total_files'] += 1
            state_data[state]['practices'].add(practice)
            
            if action == 'COPY':
                state_data[state]['copied'] += 1
            elif action == 'MOVE_TO_UNMAPPED':
                state_data[state]['unmapped'] += 1
            elif action == 'ERROR':
                state_data[state]['errors'] += 1
        
        result = []
        for state_code, data in sorted(state_data.items()):
            result.append({
                'state': data['state'],
                'total_files': data['total_files'],
                'copied': data['copied'],
                'unmapped': data['unmapped'],
                'errors': data['errors'],
                'practice_count': len(data['practices'])
            })
        
        cur.close()
        conn.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/states/<state>/practices')
def get_state_practices(state):
    """Get practices in a specific state"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT SourcePath, Action 
            FROM FACT_FileProcessing 
            WHERE SourcePath IS NOT NULL
        """)
        
        rows = cur.fetchall()
        
        practice_data = {}
        
        for source_path, action in rows:
            parsed_state, practice = parse_state_practice_from_path(source_path)
            if parsed_state != state or not practice:
                continue
            
            if practice not in practice_data:
                practice_data[practice] = {
                    'practice': practice,
                    'state': state,
                    'scanned': 0,
                    'copied': 0,
                    'unmapped': 0,
                    'errors': 0
                }
            
            practice_data[practice]['scanned'] += 1
            
            if action == 'COPY':
                practice_data[practice]['copied'] += 1
            elif action == 'MOVE_TO_UNMAPPED':
                practice_data[practice]['unmapped'] += 1
            elif action == 'ERROR':
                practice_data[practice]['errors'] += 1
        
        result = sorted(practice_data.values(), key=lambda x: x['practice'])
        
        cur.close()
        conn.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/practices/<state>/<practice>/files')
def get_practice_files(state, practice):
    """Get files for a specific practice with pagination"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        action_filter = request.args.get('action')
        
        query = """
            SELECT 
                FileProcessingKey,
                SourcePath,
                DestinationPath,
                Action,
                Reason,
                EventTimeUTC,
                FileExtension,
                FileSizeBytes
            FROM FACT_FileProcessing 
            WHERE SourcePath IS NOT NULL
        """
        
        params = []
        
        if action_filter:
            query += " AND Action = %s"
            params.append(action_filter)
        
        query += " ORDER BY EventTimeUTC DESC"
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        all_files = []
        for row in rows:
            parsed_state, parsed_practice = parse_state_practice_from_path(row[1])
            
            if parsed_state != state or parsed_practice != practice:
                continue
            
            all_files.append({
                'id': row[0],
                'source_path': row[1],
                'destination_path': row[2],
                'action': row[3],
                'reason': row[4],
                'timestamp': row[5].isoformat() if row[5] else None,
                'file_extension': row[6],
                'file_size': row[7]
            })
        
        total_files = len(all_files)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_files = all_files[start_idx:end_idx]
        
        cur.close()
        conn.close()
        
        return jsonify({
            'files': paginated_files,
            'total': total_files,
            'page': page,
            'page_size': page_size,
            'has_more': end_idx < total_files
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/unmapped')
def get_unmapped():
    """Get unmapped files"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        session_key = request.args.get('session')
        
        query = """
            SELECT 
                FileProcessingKey,
                RunID,
                SessionKey,
                EventTimeUTC,
                SourcePath,
                Reason,
                FileExtension,
                FileSizeBytes,
                Module
            FROM FACT_FileProcessing
            WHERE Action = 'MOVE_TO_UNMAPPED'
        """
        
        if session_key:
            query += " AND SessionKey = %s"
            cur.execute(query, (session_key,))
        else:
            cur.execute(query)
        
        rows = cur.fetchall()
        unmapped = []
        for row in rows:
            unmapped.append({
                'id': row[0],
                'run_id': row[1],
                'session_key': row[2],
                'timestamp': row[3].isoformat() if row[3] else None,
                'source_path': row[4],
                'reason': row[5],
                'file_extension': row[6],
                'file_size': row[7],
                'module': row[8]
            })
        
        cur.close()
        conn.close()
        
        return jsonify(unmapped)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bad-dob')
def get_bad_dob():
    """Get files with bad DOB"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                FileProcessingKey,
                RunID,
                SourcePath,
                Reason,
                EventTimeUTC
            FROM FACT_FileProcessing
            WHERE Action = 'MOVE_TO_BAD_DOB'
            ORDER BY EventTimeUTC DESC
            LIMIT 100
        """)
        
        rows = cur.fetchall()
        bad_dob = []
        for row in rows:
            bad_dob.append({
                'id': row[0],
                'run_id': row[1],
                'source_path': row[2],
                'reason': row[3],
                'timestamp': row[4].isoformat() if row[4] else None
            })
        
        cur.close()
        conn.close()
        
        return jsonify(bad_dob)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent-runs')
def get_recent_runs():
    """Get recent ETL runs"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                RunID,
                SessionKey,
                MIN(EventTimeUTC) as start_time,
                MAX(EventTimeUTC) as end_time,
                PracticeID,
                Mode,
                COUNT(*) as file_count,
                COUNT(CASE WHEN Action = 'COPY' THEN 1 END) as copied,
                COUNT(CASE WHEN Action = 'MOVE_TO_UNMAPPED' THEN 1 END) as unmapped
            FROM FACT_FileProcessing
            GROUP BY RunID, SessionKey, PracticeID, Mode
            ORDER BY MIN(EventTimeUTC) DESC
            LIMIT 20
        """)
        
        rows = cur.fetchall()
        runs = []
        for row in rows:
            runs.append({
                'run_id': row[0],
                'session_key': row[1],
                'start_time': row[2].isoformat() if row[2] else None,
                'end_time': row[3].isoformat() if row[3] else None,
                'practice_id': row[4],
                'mode': row[5],
                'file_count': row[6],
                'copied': row[7],
                'unmapped': row[8]
            })
        
        cur.close()
        conn.close()
        
        return jsonify(runs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/audit')
def get_audit():
    """Get audit trail"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        session_key = request.args.get('session')
        limit = int(request.args.get('limit', 100))
        
        query = """
            SELECT 
                FileProcessingKey,
                RunID,
                EventTimeUTC,
                Action,
                SourcePath,
                DestinationPath,
                Reason,
                InvokedByUser
            FROM FACT_FileProcessing
        """
        
        if session_key:
            query += " WHERE SessionKey = %s"
            query += " ORDER BY EventTimeUTC DESC LIMIT %s"
            cur.execute(query, (session_key, limit))
        else:
            query += " ORDER BY EventTimeUTC DESC LIMIT %s"
            cur.execute(query, (limit,))
        
        rows = cur.fetchall()
        audit = []
        for row in rows:
            audit.append({
                'id': row[0],
                'run_id': row[1],
                'timestamp': row[2].isoformat() if row[2] else None,
                'action': row[3],
                'source_path': row[4],
                'destination_path': row[5],
                'reason': row[6],
                'user': row[7]
            })
        
        cur.close()
        conn.close()
        
        return jsonify(audit)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reprocess/file', methods=['POST'])
def reprocess_file():
    """Reprocess a single file"""
    data = request.get_json()
    file_id = data.get('file_id')
    reason = data.get('reason', 'Manual reprocess')
    
    return jsonify({
        'status': 'queued',
        'message': f'File {file_id} queued for reprocessing',
        'file_id': file_id
    })

@app.route('/api/reprocess/patient', methods=['POST'])
def reprocess_patient():
    """Reprocess all files for a patient"""
    data = request.get_json()
    patient_id = data.get('patient_id')
    session_id = data.get('session_id')
    
    return jsonify({
        'status': 'queued',
        'message': f'Patient {patient_id} files queued for reprocessing',
        'patient_id': patient_id
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

def parse_mapping_file(mapping_path):
    """Parse mapping file (JSON, Excel, or CSV) into config format"""
    mapping_path = Path(mapping_path)
    
    if not mapping_path.exists():
        raise ValueError(f"Mapping file not found: {mapping_path}")
    
    ext = mapping_path.suffix.lower()
    
    if ext == '.json':
        with open(mapping_path, 'r', encoding='utf-8') as f:
            mapping_data = json.load(f)
            return mapping_data
    
    elif ext in ['.xlsx', '.xls']:
        df = pd.read_excel(mapping_path)
        mapping_data = {}
        for _, row in df.iterrows():
            if 'pattern' in df.columns and 'module' in df.columns:
                mapping_data[str(row['pattern'])] = str(row['module'])
        return {'module_mappings': mapping_data}
    
    elif ext == '.csv':
        df = pd.read_csv(mapping_path)
        mapping_data = {}
        for _, row in df.iterrows():
            if 'pattern' in df.columns and 'module' in df.columns:
                mapping_data[str(row['pattern'])] = str(row['module'])
        return {'module_mappings': mapping_data}
    
    else:
        raise ValueError(f"Unsupported mapping file format: {ext}")

def check_api_key():
    """Verify API key if authentication is enabled"""
    api_key_required = os.environ.get('API_KEY')
    if api_key_required:
        provided_key = request.headers.get('X-API-Key')
        if not provided_key or provided_key != api_key_required:
            return jsonify({'error': 'Unauthorized - Invalid or missing API key'}), 401
    return None

@app.route('/api/identity/preview', methods=['GET', 'POST'])
def preview_roster():
    """
    Preview roster column detection
    GET /api/identity/preview?roster=path/to/file.xlsx
    POST /api/identity/preview with {"roster": {"path": "..."}}
    """
    try:
        if request.method == 'GET':
            roster_path = request.args.get('roster')
        else:
            data = request.get_json()
            roster_path = data.get('roster', {}).get('path') if isinstance(data.get('roster'), dict) else data.get('roster')
        
        if not roster_path:
            return jsonify({'error': 'roster path is required'}), 400
        
        if not os.path.exists(roster_path):
            return jsonify({'error': f'Roster file not found: {roster_path}'}), 404
        
        detected, confidence = autodetect_columns(roster_path)
        
        samples = get_sample_data(roster_path, detected, limit=5)
        
        return jsonify({
            'detected': detected,
            'confidence': confidence,
            'sample': samples,
            'message': f'Auto-detected columns with {len(detected)}/3 fields found'
        })
    
    except Exception as e:
        return jsonify({'error': f'Failed to preview roster: {str(e)}'}), 500

@app.route('/api/process', methods=['POST'])
def process_files():
    """
    Process files from source to destination with optional mapping
    
    Example POST body:
    {
        "source": "C:/path/to/source.zip",
        "dest": "C:/path/to/destination",
        "dry_run": false,
        "mapping": "C:/path/to/mapping.json"  // optional
    }
    
    Security: Set API_KEY environment variable to require authentication
    """
    auth_error = check_api_key()
    if auth_error:
        return auth_error
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        mapping_data = data.get('mapping', {})
        if isinstance(mapping_data, dict):
            is_valid, error_msg = validate_config(mapping_data)
            if not is_valid:
                return jsonify({
                    'error': error_msg,
                    'status': 'validation_failed'
                }), 400
        
        source_path = data.get('source')
        dest_path = data.get('dest')
        dry_run = data.get('dry_run', True)
        mapping_path = data.get('mapping')
        
        if not source_path or not dest_path:
            return jsonify({'error': 'source and dest are required'}), 400
        
        source_path = Path(source_path)
        dest_path = Path(dest_path)
        
        if not source_path.exists():
            return jsonify({'error': f'Source path does not exist: {source_path}'}), 400
        
        extracted_source = None
        
        if source_path.suffix.lower() == '.zip':
            temp_dir = tempfile.mkdtemp(prefix='etl_extract_')
            try:
                with zipfile.ZipFile(source_path, 'r') as zip_ref:
                    temp_dir_real = os.path.realpath(temp_dir)
                    
                    for member_info in zip_ref.infolist():
                        member = member_info.filename
                        
                        if member_info.is_dir():
                            continue
                        
                        member_path = os.path.normpath(os.path.join(temp_dir, member))
                        member_path_real = os.path.realpath(member_path)
                        
                        try:
                            common_path = os.path.commonpath([member_path_real, temp_dir_real])
                            if common_path != temp_dir_real:
                                raise ValueError(f'ZIP contains path outside extraction directory: {member}')
                        except ValueError:
                            raise ValueError(f'ZIP contains unsafe path: {member}')
                        
                        target_dir = os.path.dirname(member_path)
                        if not os.path.exists(target_dir):
                            os.makedirs(target_dir)
                        
                        with zip_ref.open(member) as source, open(member_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                        
                        final_path_real = os.path.realpath(member_path)
                        try:
                            final_common = os.path.commonpath([final_path_real, temp_dir_real])
                            if final_common != temp_dir_real:
                                os.unlink(member_path)
                                raise ValueError(f'Extracted file escaped temp directory (symlink attack?): {member}')
                        except ValueError:
                            if os.path.exists(member_path):
                                os.unlink(member_path)
                            raise ValueError(f'Security check failed for extracted file: {member}')
                
                extracted_source = Path(temp_dir)
                source_to_process = extracted_source
            except Exception as e:
                if extracted_source:
                    shutil.rmtree(extracted_source, ignore_errors=True)
                return jsonify({'error': f'Failed to extract ZIP: {str(e)}'}), 500
        else:
            source_to_process = source_path
        
        config_path = Path(__file__).parent.parent / 'router_service' / 'configs' / 'default.yml'
        temp_config = None
        
        if mapping_path:
            try:
                mapping_data = parse_mapping_file(mapping_path)
                
                with open(config_path, 'r') as f:
                    base_config = f.read()
                
                import yaml
                config_dict = yaml.safe_load(base_config)
                
                if 'module_mappings' in mapping_data:
                    config_dict.setdefault('modules', {})
                    config_dict['modules'].update(mapping_data['module_mappings'])
                elif isinstance(mapping_data, dict):
                    config_dict.update(mapping_data)
                
                temp_config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False)
                yaml.dump(config_dict, temp_config_file)
                temp_config = temp_config_file.name
                temp_config_file.close()
                
                config_to_use = temp_config
            except Exception as e:
                if extracted_source:
                    shutil.rmtree(extracted_source, ignore_errors=True)
                return jsonify({'error': f'Failed to parse mapping file: {str(e)}'}), 400
        else:
            config_to_use = str(config_path)
        
        try:
            from universal_router import UniversalRouter
            
            args = argparse.Namespace(
                src=str(source_to_process),
                dst=str(dest_path),
                log='./logs',
                db_url=DATABASE_URL,
                user=request.remote_addr or 'postman',
                dry_run=dry_run,
                canary=None
            )
            
            router = UniversalRouter(config_to_use, args)
            router.run()
            
            summary = router.logger.get_summary()
            
            is_high_unmapped, unmapped_warning = check_high_unmapped_rate(router.stats, threshold=0.6)
            
            result = {
                'status': 'success',
                'run_id': router.run_id,
                'session_key': router.session_key,
                'mode': 'DRY_RUN' if dry_run else 'REAL_RUN',
                'source': str(source_path),
                'destination': str(dest_path),
                'stats': router.stats,
                'log_file': summary.get('csv_path'),
                'message': 'Processing completed successfully'
            }
            
            if is_high_unmapped and dry_run:
                result['warning'] = unmapped_warning
                result['recommendation'] = 'Review roster configuration. Use GET /api/unmapped to see examples.'
                return jsonify(result), 409
            
            if is_high_unmapped:
                result['warning'] = unmapped_warning
            
            return jsonify(result), 200
        
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e),
                'message': 'Processing failed'
            }), 500
        
        finally:
            if extracted_source and extracted_source.exists():
                shutil.rmtree(extracted_source, ignore_errors=True)
            
            if temp_config and os.path.exists(temp_config):
                os.unlink(temp_config)
    
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port, debug=True)
