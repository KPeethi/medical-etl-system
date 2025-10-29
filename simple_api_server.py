#!/usr/bin/env python3
"""
Simple API Server for Medical File Processing
Works with your working_universal_processor.py via Postman
"""

import os
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Check if working processor exists
    processor_path = os.path.join(os.path.dirname(__file__), 'working_universal_processor.py')
    processor_available = os.path.exists(processor_path)
    
    return jsonify({
        'status': 'healthy',
        'processor_available': processor_available,
        'api_endpoints': [
            'GET /health',
            'POST /api/process'
        ]
    })

@app.route('/api/process', methods=['POST'])
def process_files():
    """
    Process medical files with OCR workflow: Mapping → Folder → Filename → OCR → Unmapped
    
    Expected JSON body:
    {
        "source": "C:\\path\\to\\source.zip",
        "dest": "C:\\path\\to\\output",
        "dry_run": false,
        "log": "C:\\path\\to\\log\\directory",    // optional - where to create log file
        "roster": "C:\\path\\to\\roster.csv",    // optional - if not provided, skips mapping step
        "config": "C:\\path\\to\\config.yml",    // optional
        "mapping": "C:\\path\\to\\mapping.json"  // optional
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        required_fields = ['source', 'dest']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Build command using enhanced_universal_processor.py (with OCR)
        cmd = [
            'python',
            'enhanced_universal_processor.py',
            '--source', data['source'],
            '--dest', data['dest']
        ]
        
        # Add optional parameters
        if data.get('roster'):
            cmd.extend(['--roster', data['roster']])
        
        if data.get('log'):
            cmd.extend(['--log', data['log']])
        
        if data.get('config'):
            cmd.extend(['--config', data['config']])
            
        if data.get('mapping'):
            cmd.extend(['--mapping', data['mapping']])
        
        # Add execution mode
        if not data.get('dry_run', True):
            cmd.append('--live')
        else:
            cmd.append('--dry-run')
        
        print(f"Executing command: {' '.join(cmd)}")
        
        # Execute the working processor
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        return jsonify({
            'status': 'success' if result.returncode == 0 else 'error',
            'message': result.stdout,
            'error': result.stderr if result.returncode != 0 else None,
            'command': ' '.join(cmd),
            'returncode': result.returncode
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Processing failed: {str(e)}'
        }), 500


if __name__ == '__main__':
    print("🚀 Starting Simple Medical File Processing API Server...")
    print("📍 Health Check: GET http://localhost:5000/health")
    print("🔄 Process Files: POST http://localhost:5000/api/process")
    print("📖 Uses: working_universal_processor.py")
    
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port, debug=True)