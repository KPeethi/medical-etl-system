#!/usr/bin/env python3
"""
UNIVERSAL MEDICAL FILE PROCESSOR API

Flask API wrapper for the universal medical processor.
No hardcoded paths, optional mapping, smart fallbacks.

API Contract:
POST /api/process
{
  "source": "path/to/input_or_zip",
  "dest": "path/to/organized_output", 
  "dry_run": false,
  "roster": null,
  "mapping": null,
  "options": {...}
}
"""

from flask import Flask, request, jsonify
import os
import sys
from pathlib import Path

# Add current directory to path to import our processor
sys.path.append(str(Path(__file__).parent))

try:
    from universal_medical_processor import UniversalMedicalProcessor
except ImportError:
    print("❌ Could not import UniversalMedicalProcessor")
    sys.exit(1)

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ready",
        "mapping_mode_default": "none",
        "hardcoded_paths": False,
        "version": "1.0.0",
        "universal": True,
        "portable": True
    })


@app.route('/api/process', methods=['POST'])
def process_medical_files():
    """
    Process medical files with universal detection
    
    Body (JSON):
    {
      "source": "/path/to/input_or_zip",
      "dest": "/path/to/organized_output",
      "dry_run": false,
      "roster": null,
      "mapping": null,
      "options": {
        "duplicate_policy": "size_and_module",
        "output_root_style": "container",
        "skip_placeholder_dobs": ["01-01-1900","1900-01-01"]
      }
    }
    """
    try:
        # Parse request
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400
        
        # Validate required fields
        if "source" not in data or "dest" not in data:
            return jsonify({
                "status": "error",
                "message": "Both 'source' and 'dest' are required"
            }), 400
        
        # Build config with defaults
        config = {
            "source": data["source"],
            "dest": data["dest"],
            "dry_run": data.get("dry_run", True),  # Default to dry run
            "roster": data.get("roster"),  # Optional
            "mapping": data.get("mapping"),  # Optional
            "options": data.get("options", {
                "duplicate_policy": "size_and_module",
                "output_root_style": "container",
                "skip_placeholder_dobs": ["01-01-1900", "1900-01-01"]
            })
        }
        
        # Process using universal processor
        processor = UniversalMedicalProcessor()
        result = processor.process_dataset(config)
        
        # Return result
        if result["status"] == "ok":
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Processing error: {str(e)}",
            "mapping_mode": "error"
        }), 500


@app.route('/api/examples', methods=['GET'])
def get_examples():
    """Get example API calls"""
    return jsonify({
        "examples": {
            "pure_auto_mode": {
                "description": "No mapping/roster provided",
                "request": {
                    "source": "/path/to/medical_dataset.zip",
                    "dest": "/path/to/organized_output",
                    "dry_run": False
                },
                "expected_response": {
                    "mapping_mode": "none",
                    "inference": "reading names/DOB from files and folders"
                }
            },
            "roster_only": {
                "description": "Roster with header auto-detection",
                "request": {
                    "source": "/path/to/practice_folder",
                    "dest": "/path/to/organized_output",
                    "dry_run": True,
                    "roster": "/path/to/practice_roster.csv"
                }
            },
            "roster_and_mapping": {
                "description": "Roster + mapping aliases",
                "request": {
                    "source": "/path/to/batch_files.zip",
                    "dest": "/path/to/organized_batch",
                    "dry_run": False,
                    "roster": "/path/to/practice_roster.csv",
                    "mapping": "/path/to/column_aliases.json",
                    "options": {
                        "duplicate_policy": "size_and_module"
                    }
                }
            }
        },
        "validation_messages": {
            "mapping_none": "mapping_mode set to 'none'. Proceeding with filename/folder inference.",
            "mapping_missing": "mapping not found at <path>. Falling back to auto alias detection.",
            "roster_unavailable": "Could not read roster <path>. Continuing in filename-only mode.",
            "no_matches": "Unable to extract name/DOB from provided files. Provide a roster or adjust filename patterns.",
            "zip_detected": "Expanding zip to temp workspace (read-only source preserved)."
        }
    })


@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        "name": "Universal Medical File Processor API",
        "version": "1.0.0",
        "description": "Universal and portable medical file processing with no hardcoded paths",
        "features": [
            "No hardcoded paths (all from user input)",
            "Optional mapping/roster (fallback to filename parsing)",
            "Universal input (directory or ZIP, any file types)",
            "Source is read-only (never modify originals)",
            "Dry-run first option available"
        ],
        "endpoints": {
            "GET /health": "Health check and system info",
            "POST /api/process": "Process medical files",
            "GET /api/examples": "Get example API calls",
            "GET /": "This documentation"
        },
        "detection_order": [
            "1. Roster Match (if provided)",
            "2. Filename/Folder Inference (always available)"
        ],
        "supported_patterns": [
            "Lastname_Firstname_YYYY-MM-DD_*",
            "Firstname Lastname - module (MM/DD/YYYY)",
            "DOE,J,LAB_04221988.*",
            "lastname firstname MM-DD-YYYY",
            "MRN prefix patterns"
        ],
        "mapping_modes": {
            "none": "No mapping provided, using filename inference",
            "file_provided": "Mapping file loaded successfully",
            "file_missing": "Mapping file not found, using auto-detection"
        }
    })


def show_startup_info():
    """Show startup information"""
    print("🌟 UNIVERSAL MEDICAL FILE PROCESSOR API")
    print("=" * 60)
    print("✅ No hardcoded paths - fully portable")
    print("✅ Optional mapping/roster - smart fallbacks")
    print("✅ Universal input support - any dataset format")
    print("✅ Read-only source - never modifies originals")
    print()
    print("🔗 Endpoints:")
    print("   GET  /health          - Health check")
    print("   POST /api/process     - Process medical files")
    print("   GET  /api/examples    - Example API calls")
    print("   GET  /               - API documentation")
    print()
    print("📋 Example API Call:")
    print("   POST http://localhost:8080/api/process")
    print("   {")
    print('     "source": "/path/to/your/dataset.zip",')
    print('     "dest": "/path/to/organized_files",')
    print('     "dry_run": false')
    print("   }")
    print()
    print("🎯 Expected Response:")
    print("   {")
    print('     "status": "ok",')
    print('     "mapping_mode": "none",')
    print('     "inference": "reading names/DOB from files and folders"')
    print("   }")
    print()
    print("=" * 60)


if __name__ == '__main__':
    show_startup_info()
    print("🚀 Starting Universal Medical Processor API on http://localhost:8080")
    print("   (Use Ctrl+C to stop)")
    print()
    
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=False,
        threaded=True
    )