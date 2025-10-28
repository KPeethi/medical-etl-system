#!/usr/bin/env python3
"""
Stable Test Server for Postman - No Debug Mode
"""

from flask import Flask, jsonify, request
from pathlib import Path

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Stable server is running',
        'server': 'production-mode'
    })

@app.route('/api/stats')
def get_stats():
    return jsonify({
        'message': 'Use /api/process to process your dataset',
        'total_runs': 0,
        'total_files': 0,
        'server': 'stable-mode'
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
        
        # Check if source exists
        if not Path(source_path).exists():
            return jsonify({
                'error': f'Source path does not exist: {source_path}',
                'note': 'Make sure the path is correct'
            }), 400
        
        result = {
            'status': 'success',
            'run_id': 'stable-test-001',
            'mode': 'DRY_RUN' if dry_run else 'REAL_RUN',
            'source': source_path,
            'destination': dest_path,
            'stats': {
                'processed': 42,
                'copied': 38,
                'skipped': 2,
                'unmapped': 2,
                'errors': 0
            },
            'message': 'TEST SERVER: Request received successfully!',
            'next_step': 'Your dataset structure looks good for processing'
        }
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Stable Server Starting...")
    print("URL: http://127.0.0.1:8080")
    print("Ready for Postman!")
    
    # No debug mode to avoid crashes
    app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)