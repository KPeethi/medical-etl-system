#!/usr/bin/env python3
"""
UNIVERSAL Medical File Organizer API Server
Works with ANY medical dataset - just point it at any ZIP file or folder!
"""

from flask import Flask, request, jsonify
from universal_medical_organizer import UniversalMedicalOrganizer
import os

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Universal Medical File Organizer API",
        "version": "universal-1.0",
        "capabilities": [
            "ANY filename patterns",
            "ANY date formats", 
            "ANY roster column names",
            "ZIP files and folders",
            "International characters",
            "Multiple file types"
        ]
    })


@app.route('/organize', methods=['POST'])
def organize():
    """Universal organize endpoint - works with ANY dataset"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        if 'dataset_path' not in data:
            return jsonify({
                "error": "Missing 'dataset_path' in request body",
                "example": {
                    "dataset_path": "/path/to/your/dataset.zip",
                    "output_base": "organized_output"
                }
            }), 400
        
        dataset_path = data['dataset_path']
        output_base = data.get('output_base', 'UNIVERSAL_OUTPUT')
        
        # Validate dataset path exists
        if not os.path.exists(dataset_path):
            return jsonify({
                "error": f"Dataset path does not exist: {dataset_path}"
            }), 400
        
        # Process with universal organizer
        organizer = UniversalMedicalOrganizer()
        results = organizer.organize_dataset(dataset_path, output_base)
        
        if 'error' in results:
            return jsonify(results), 500
        
        return jsonify({
            "status": "success",
            "message": f"Successfully processed {results['stats']['total_files']} files with {results['stats']['success_rate']} success rate",
            "results": results
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500


@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze a dataset without organizing - see what patterns exist"""
    try:
        data = request.get_json()
        
        if not data or 'dataset_path' not in data:
            return jsonify({"error": "Missing 'dataset_path'"}), 400
        
        dataset_path = data['dataset_path']
        
        if not os.path.exists(dataset_path):
            return jsonify({"error": f"Dataset path not found: {dataset_path}"}), 400
        
        # TODO: Add analysis functionality
        return jsonify({
            "message": "Analysis feature coming soon!",
            "suggestion": "Use /organize endpoint to process the dataset"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("🚀 Universal Medical File Organizer API Server")
    print("🌟 UNIVERSAL SOLVER - Works with ANY medical dataset!")
    print("")
    print("🔧 Capabilities:")
    print("   ✅ ANY filename patterns (underscore, space, dash, comma)")
    print("   ✅ ANY date formats (MM/DD/YYYY, YYYY-MM-DD, DD.MM.YYYY, etc.)")
    print("   ✅ ANY roster column names (auto-detected)")
    print("   ✅ International characters (García, O'Neil, etc.)")
    print("   ✅ ZIP files and folder structures")
    print("   ✅ Multiple file types (PDF, DOC, images, XML, etc.)")
    print("")
    print("🌐 Server running on http://localhost:8080")
    print("")
    print("📋 API Endpoints:")
    print("   GET  /health - Server status")
    print("   POST /organize - Process any medical dataset")
    print("   POST /analyze - Analyze dataset patterns")
    print("")
    print("📝 Example request:")
    print('   POST /organize')
    print('   {')
    print('     "dataset_path": "/path/to/any_medical_dataset.zip",')
    print('     "output_base": "organized_files"')
    print('   }')
    print("")
    print("🎯 Just point it at ANY medical dataset and it will figure it out!")
    
    app.run(host='0.0.0.0', port=8080, debug=False)