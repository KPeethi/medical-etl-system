#!/usr/bin/env python3
"""
Medical ETL Review Queue UI
Flask web application for managing unmapped files and duplicates
"""

import os
import psycopg2
from flask import Flask, render_template, jsonify, request
from datetime import datetime

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

@app.route('/api/stats')
def get_stats():
    """Get overall statistics"""
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
        stats = {
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
