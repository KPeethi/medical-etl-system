#!/usr/bin/env python3
"""
Test script for Medical ETL API
Demonstrates API functionality without requiring actual files
"""

import zipfile
import tempfile
import os
from pathlib import Path
import json

# Create a test ZIP file with sample structure
def create_test_zip():
    """Create a test ZIP file for demonstration"""
    temp_dir = tempfile.mkdtemp()
    zip_path = Path(temp_dir) / "test_dataset.zip"
    
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Add some sample file entries (empty but with names)
        zf.writestr("patient_records/Smith_John_01-15-1980.pdf", b"Sample PDF content")
        zf.writestr("patient_records/Johnson_Mary_03-22-1975.jpg", b"Sample image content")
        zf.writestr("patient_records/nested/Brown_Bob_12-05-1985.pdf", b"Sample nested file")
        zf.writestr("patient_records/Williams_Sue_06-10-1990.tiff", b"Sample TIFF content")
    
    return zip_path, temp_dir


def test_inspect_function():
    """Test the file_extractor inspect_archive method"""
    from modules.file_extractor import FileExtractor
    
    print("=" * 60)
    print("Testing FileExtractor.inspect_archive() method")
    print("=" * 60)
    
    # Create test ZIP
    zip_path, temp_dir = create_test_zip()
    
    try:
        # Create FileExtractor instance
        extractor = FileExtractor()
        
        # Inspect the ZIP file
        print(f"\nInspecting: {zip_path}")
        result = extractor.inspect_archive(zip_path)
        
        print(f"\n✓ Archive inspection successful!")
        print(f"  Archive type: {result['archive_type']}")
        print(f"  Total files: {result['total_files']}")
        print(f"  Total size: {result['total_size_mb']} MB")
        print(f"\n  Files found:")
        for file_info in result['files']:
            print(f"    - {file_info['name']} ({file_info['size']} bytes)")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if os.path.exists(zip_path):
            os.unlink(zip_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


def test_api_models():
    """Test API request/response models"""
    from api import ETLRequest, InspectRequest, InspectResponse, FileInfo
    
    print("\n" + "=" * 60)
    print("Testing API Models")
    print("=" * 60)
    
    try:
        # Test ETLRequest
        etl_req = ETLRequest(
            source_path="/path/to/source",
            destination_path="/path/to/dest",
            dry_run=True
        )
        print(f"\n✓ ETLRequest model valid:")
        print(f"  Source: {etl_req.source_path}")
        print(f"  Destination: {etl_req.destination_path}")
        print(f"  Mapping: {etl_req.mapping_file}")
        print(f"  Dry run: {etl_req.dry_run}")
        
        # Test InspectRequest
        inspect_req = InspectRequest(file_path="/path/to/file.zip")
        print(f"\n✓ InspectRequest model valid:")
        print(f"  File path: {inspect_req.file_path}")
        
        # Test FileInfo
        file_info = FileInfo(
            name="test.pdf",
            size=1024,
            path="records/test.pdf",
            is_archive=False,
            is_image=False,
            is_pdf=True
        )
        print(f"\n✓ FileInfo model valid:")
        print(f"  Name: {file_info.name}")
        print(f"  Size: {file_info.size}")
        print(f"  Is PDF: {file_info.is_pdf}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_errors():
    """Test validation error handling"""
    from api import ETLRequest, InspectRequest
    from pydantic import ValidationError
    
    print("\n" + "=" * 60)
    print("Testing Validation Error Handling")
    print("=" * 60)
    
    try:
        # Test empty source path
        try:
            ETLRequest(source_path="", destination_path="/dest")
            print("\n✗ Should have raised validation error for empty source path")
            return False
        except ValidationError as e:
            print("\n✓ Validation error correctly raised for empty source path")
            print(f"  Error: {e.errors()[0]['msg']}")
        
        # Test empty file path
        try:
            InspectRequest(file_path="")
            print("\n✗ Should have raised validation error for empty file path")
            return False
        except ValidationError as e:
            print("\n✓ Validation error correctly raised for empty file path")
            print(f"  Error: {e.errors()[0]['msg']}")
        
        # Test missing required fields
        try:
            ETLRequest(source_path="/source")
            print("\n✗ Should have raised validation error for missing destination")
            return False
        except ValidationError as e:
            print("\n✓ Validation error correctly raised for missing destination")
            print(f"  Error: {e.errors()[0]['msg']}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def print_api_info():
    """Print API information"""
    from api import app
    
    print("\n" + "=" * 60)
    print("API Information")
    print("=" * 60)
    
    print(f"\nTitle: {app.title}")
    print(f"Description: {app.description}")
    print(f"Version: {app.version}")
    
    print("\nAvailable Endpoints:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods - {'HEAD', 'OPTIONS'})
            print(f"  {methods:6} {route.path}")
    
    print("\nTo start the API server, run:")
    print("  python api.py")
    print("  OR")
    print("  uvicorn api:app --reload")
    
    print("\nOnce running, access:")
    print("  - API docs: http://localhost:8000/docs")
    print("  - Alternative docs: http://localhost:8000/redoc")
    print("  - Health check: http://localhost:8000/health")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Medical ETL System API - Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("API Models", test_api_models()))
    results.append(("Validation Errors", test_validation_errors()))
    results.append(("Archive Inspection", test_inspect_function()))
    
    # Print API info
    print_api_info()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status:10} - {name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
