#!/usr/bin/env python3
"""
Minimal Test Server for Postman
Just to verify Postman can connect and make requests
"""

from flask import Flask, jsonify, request
import os
from pathlib import Path

app = Flask(__name__)

@app.route('/health')
def health():
    """Simple health check"""
    return jsonify({
        'status': 'healthy',
        'message': 'Minimal test server is running',
        'note': 'This server can process your fake_patient_dataset.zip'
    })

@app.route('/api/stats')
def get_stats():
    """Simple stats response"""
    return jsonify({
        'message': 'Test server - Use /api/process to process files',
        'total_runs': 0,
        'total_files': 0,
        'copied': 0,
        'skipped': 0,
        'unmapped': 0,
        'errors': 0
    })

@app.route('/api/process', methods=['POST'])
def process_files():
    """Process files - simplified version for testing"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        source_path = data.get('source')
        dest_path = data.get('dest')
        dry_run = data.get('dry_run', True)
        
        if not source_path or not dest_path:
            return jsonify({'error': 'source and dest are required'}), 400
        
        # Check if source exists
        if not Path(source_path).exists():
            return jsonify({
                'error': f'Source path does not exist: {source_path}'
            }), 400
        
        # For now, just return success without actually processing
        # This is to test that Postman can communicate with the server
        result = {
            'status': 'success',
            'run_id': 'test-run-001',
            'session_key': 'test-session',
            'mode': 'DRY_RUN' if dry_run else 'REAL_RUN',
            'source': source_path,
            'destination': dest_path,
            'stats': {
                'processed': 0,
                'copied': 0,
                'skipped': 0,
                'unmapped': 0,
                'errors': 0
            },
            'message': 'Test server received your request successfully!',
            'note': 'This is a minimal test - no actual file processing yet'
        }
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Request processing failed'
        }), 500

if __name__ == '__main__':
    print("🧪 Minimal Test Server for Postman")
    print("=" * 40)
    print("📍 URL: http://127.0.0.1:8080")
    print("✅ Available endpoints:")
    print("   GET  /health")
    print("   GET  /api/stats")
    print("   POST /api/process")
    print()
    print("🎯 Ready to test your fake_patient_dataset.zip!")
    print()
    
    app.run(host='127.0.0.1', port=8080, debug=True)