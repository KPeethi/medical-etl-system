#!/usr/bin/env python3
"""
Production-Ready Medical File Processing API Server for Postman
Supports complete workflow: Mapping → Folder → Filename → OCR → Unmapped
"""

import os
import sys
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


class PostmanAPIServer:
    """Clean API server for Postman integration"""
    
    def __init__(self):
        self.processing_results = {}
        self.log_directory = Path("./api_logs")
        self.log_directory.mkdir(exist_ok=True)
    
    def validate_request(self, data: Dict):
        """Validate incoming request data"""
        if not data:
            return False, "No JSON data provided"
        
        required_fields = ['source', 'dest']
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
        
        # Validate source path exists
        source_path = Path(data['source'])
        if not source_path.exists():
            return False, f"Source path does not exist: {data['source']}"
        
        return True, "Valid"
    
    def build_command(self, data: Dict):
        """Build command for working_universal_processor.py"""
        cmd = [
            sys.executable,  # Use current Python interpreter
            'working_universal_processor.py',
            '--source', data['source'],
            '--dest', data['dest']
        ]
        
        # Add optional parameters
        if data.get('roster'):
            cmd.extend(['--roster', data['roster']])
            
        if data.get('mapping'):
            cmd.extend(['--mapping', data['mapping']])
        
        # Add execution mode
        if not data.get('dry_run', True):
            cmd.append('--live')
        
        return cmd
    
    def execute_processing(self, cmd, run_id):
        """Execute the processing command"""
        try:
            print(f"🚀 Executing: {' '.join(cmd)}")
            
            # Create log file for this run
            log_file = self.log_directory / f"run_{run_id}.log"
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__),
                timeout=1800  # 30 minute timeout
            )
            
            # Save logs
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"Command: {' '.join(cmd)}\n")
                f.write(f"Return code: {result.returncode}\n")
                f.write(f"STDOUT:\n{result.stdout}\n")
                f.write(f"STDERR:\n{result.stderr}\n")
            
            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'log_file': str(log_file),
                'success': result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': 'Processing timeout (30 minutes exceeded)',
                'log_file': str(log_file) if 'log_file' in locals() else '',
                'success': False
            }
        except Exception as e:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': f'Execution failed: {str(e)}',
                'log_file': '',
                'success': False
            }


# Global server instance
server = PostmanAPIServer()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Medical File Processing API',
        'workflow': 'Mapping → Folder → Filename → OCR → Unmapped',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.route('/api/process', methods=['POST'])
def process_files():
    """
    Process medical files with complete workflow
    
    POST /api/process
    {
        "source": "C:/path/to/source/files",
        "dest": "C:/path/to/organized/output",
        "roster": "C:/path/to/roster.csv",          // optional
        "mapping": "C:/path/to/mapping.csv",        // optional
        "dry_run": true                             // optional, default true
    }
    """
    try:
        data = request.get_json()
        
        # Validate request
        is_valid, message = server.validate_request(data)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Generate run ID
        run_id = str(uuid.uuid4())[:8]
        
        # Build and execute command
        cmd = server.build_command(data)
        execution_result = server.execute_processing(cmd, run_id)
        
        # Store result for potential retrieval
        server.processing_results[run_id] = execution_result
        
        # Parse output for stats (if available)
        stats = {
            'mapping_matched': 0,
            'folder_matched': 0,
            'filename_matched': 0,
            'ocr_matched': 0,
            'unmapped': 0,
            'total_processed': 0
        }
        
        # Try to extract stats from stdout
        if execution_result['stdout']:
            lines = execution_result['stdout'].split('\n')
            for line in lines:
                if 'Mapping:' in line:
                    try:
                        stats['mapping_matched'] = int(line.split(':')[1].strip())
                    except:
                        pass
                elif 'Folder:' in line:
                    try:
                        stats['folder_matched'] = int(line.split(':')[1].strip())
                    except:
                        pass
                elif 'Filename:' in line:
                    try:
                        stats['filename_matched'] = int(line.split(':')[1].strip())
                    except:
                        pass
                elif 'OCR:' in line:
                    try:
                        stats['ocr_matched'] = int(line.split(':')[1].strip())
                    except:
                        pass
                elif 'Unmapped Files:' in line:
                    try:
                        stats['unmapped'] = int(line.split(':')[1].strip())
                    except:
                        pass
        
        stats['total_processed'] = (stats['mapping_matched'] + 
                                   stats['folder_matched'] + 
                                   stats['filename_matched'] + 
                                   stats['ocr_matched'] + 
                                   stats['unmapped'])
        
        # Build response
        response = {
            'status': 'success' if execution_result['success'] else 'error',
            'run_id': run_id,
            'mode': 'DRY_RUN' if data.get('dry_run', True) else 'LIVE_RUN',
            'workflow': 'Mapping → Folder → Filename → OCR → Unmapped',
            'source': data['source'],
            'destination': data['dest'],
            'stats': stats,
            'command': ' '.join(cmd),
            'timestamp': datetime.now().isoformat()
        }
        
        if execution_result['success']:
            response['message'] = 'Processing completed successfully'
            if data.get('dry_run', True):
                response['note'] = 'DRY RUN - No files were actually moved'
        else:
            response['error'] = execution_result['stderr'] or 'Processing failed'
            response['details'] = execution_result['stdout']
        
        return jsonify(response), 200 if execution_result['success'] else 500
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'API error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/status/<run_id>', methods=['GET'])
def get_status(run_id: str):
    """Get status of a processing run"""
    if run_id not in server.processing_results:
        return jsonify({'error': 'Run ID not found'}), 404
    
    result = server.processing_results[run_id]
    return jsonify({
        'run_id': run_id,
        'success': result['success'],
        'returncode': result['returncode'],
        'log_file': result['log_file']
    })


@app.route('/api/logs/<run_id>', methods=['GET'])
def get_logs(run_id: str):
    """Get logs for a processing run"""
    if run_id not in server.processing_results:
        return jsonify({'error': 'Run ID not found'}), 404
    
    result = server.processing_results[run_id]
    log_file = Path(result['log_file'])
    
    if not log_file.exists():
        return jsonify({'error': 'Log file not found'}), 404
    
    return send_file(log_file, as_attachment=True)


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            'GET /health',
            'POST /api/process',
            'GET /api/status/<run_id>',
            'GET /api/logs/<run_id>'
        ]
    }), 404


if __name__ == '__main__':
    print("🏥 Medical File Processing API Server")
    print("📋 Workflow: Mapping → Folder → Filename → OCR → Unmapped")
    print("🌐 Health Check: http://localhost:5001/health")
    print("🔄 Process Files: POST http://localhost:5001/api/process")
    print("📊 Check Status: GET http://localhost:5001/api/status/<run_id>")
    print("📝 Get Logs: GET http://localhost:5001/api/logs/<run_id>")
    print()
    
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5001))
    
    app.run(host=host, port=port, debug=True)