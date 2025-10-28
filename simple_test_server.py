#!/usr/bin/env python3
"""
Simple Medical ETL Test Server
A minimal Flask server for testing file processing without database requirements
"""

import os
import sys
import json
import tempfile
import shutil
import zipfile
import argparse
from pathlib import Path
from flask import Flask, jsonify, request

# Add router_service to path
router_service_path = os.path.join(os.path.dirname(__file__), 'router_service')
sys.path.insert(0, router_service_path)

app = Flask(__name__)

@app.route('/health')
def health():
    """Simple health check without database"""
    return jsonify({
        'status': 'healthy', 
        'message': 'Simple test server running',
        'database': 'not_required'
    })

@app.route('/api/process', methods=['POST'])
def process_files():
    """
    Process files from source to destination with optional mapping
    Simplified version without database logging
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
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
        
        # Handle ZIP extraction
        extracted_source = None
        if source_path.suffix.lower() == '.zip':
            temp_dir = tempfile.mkdtemp(prefix='etl_extract_')
            try:
                with zipfile.ZipFile(source_path, 'r') as zip_ref:
                    # Safe extraction
                    for member in zip_ref.namelist():
                        if member.startswith('/') or '..' in member:
                            continue  # Skip unsafe paths
                        zip_ref.extract(member, temp_dir)
                
                extracted_source = Path(temp_dir)
                source_to_process = extracted_source
            except Exception as e:
                if extracted_source:
                    shutil.rmtree(extracted_source, ignore_errors=True)
                return jsonify({'error': f'Failed to extract ZIP: {str(e)}'}), 500
        else:
            source_to_process = source_path
        
        try:
            # Use simplified router without database
            from universal_router import UniversalRouter
            
            # Create minimal args
            args = argparse.Namespace(
                src=str(source_to_process),
                dst=str(dest_path),
                log='./logs',
                db_url=None,  # No database required
                user='postman_test',
                dry_run=dry_run,
                canary=None
            )
            
            # Use default config
            config_path = Path(__file__).parent / 'router_service' / 'configs' / 'default.yml'
            
            # Create router and run
            router = UniversalRouter(str(config_path), args)
            router.run()
            
            # Get results
            result = {
                'status': 'success',
                'run_id': getattr(router, 'run_id', 'test-run'),
                'session_key': getattr(router, 'session_key', 'test-session'),
                'mode': 'DRY_RUN' if dry_run else 'REAL_RUN',
                'source': str(source_path),
                'destination': str(dest_path),
                'stats': getattr(router, 'stats', {
                    'processed': 0,
                    'copied': 0,
                    'skipped': 0,
                    'unmapped': 0,
                    'errors': 0
                }),
                'message': 'Processing completed successfully (simplified mode)'
            }
            
            return jsonify(result), 200
        
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e),
                'message': 'Processing failed'
            }), 500
        
        finally:
            # Cleanup
            if extracted_source and extracted_source.exists():
                shutil.rmtree(extracted_source, ignore_errors=True)
    
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/stats')
def get_stats():
    """Simple stats without database"""
    return jsonify({
        'message': 'This is a simplified test server',
        'note': 'Run /api/process to process your dataset',
        'total_runs': 0,
        'total_files': 0,
        'copied': 0,
        'skipped': 0,
        'unmapped': 0,
        'errors': 0
    })

if __name__ == '__main__':
    print("🧪 Simple Medical ETL Test Server")
    print("=" * 40)
    print("📍 URL: http://127.0.0.1:8080")
    print("🔥 This is a simplified version for testing without database")
    print("✅ Available endpoints:")
    print("   GET  /health")
    print("   POST /api/process")
    print("   GET  /api/stats")
    print()
    
    app.run(host='127.0.0.1', port=8080, debug=True)