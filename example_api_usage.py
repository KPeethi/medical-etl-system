#!/usr/bin/env python3
"""
Example usage of the Medical ETL System API
This script demonstrates how to interact with the API programmatically
"""

import requests
import json
from pathlib import Path
import zipfile
import tempfile
import time


class MedicalETLAPIClient:
    """Client for interacting with the Medical ETL System API"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def health_check(self):
        """Check if the API is healthy"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def inspect_dataset(self, file_path):
        """Inspect a ZIP file by path"""
        response = requests.post(
            f"{self.base_url}/api/v1/dataset/inspect",
            json={"file_path": str(file_path)}
        )
        return response.json()
    
    def upload_and_inspect(self, file_path):
        """Upload and inspect a ZIP file"""
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'application/zip')}
            response = requests.post(
                f"{self.base_url}/api/v1/dataset/upload-and-inspect",
                files=files
            )
        return response.json()
    
    def run_etl(self, source_path, destination_path, mapping_file=None, dry_run=True):
        """Run the ETL process"""
        data = {
            "source_path": str(source_path),
            "destination_path": str(destination_path),
            "dry_run": dry_run
        }
        if mapping_file:
            data["mapping_file"] = str(mapping_file)
        
        response = requests.post(
            f"{self.base_url}/api/v1/etl/run",
            json=data
        )
        return response.json()


def create_sample_dataset():
    """Create a sample dataset for demonstration"""
    temp_dir = tempfile.mkdtemp()
    zip_path = Path(temp_dir) / "sample_medical_records.zip"
    
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Add sample patient records
        zf.writestr(
            "records/Smith_John_19800115.pdf",
            b"%PDF-1.4 Sample medical record for John Smith DOB: 01/15/1980"
        )
        zf.writestr(
            "records/Johnson_Mary_19750322.jpg",
            b"JPEG Sample image for Mary Johnson DOB: 03/22/1975"
        )
        zf.writestr(
            "xrays/2023_Brown_Bob_19851205_xray.tiff",
            b"TIFF Sample x-ray for Bob Brown DOB: 12/05/1985"
        )
        zf.writestr(
            "labs/Williams_Sue_19900610_labs.pdf",
            b"%PDF-1.4 Lab results for Sue Williams DOB: 06/10/1990"
        )
        zf.writestr(
            "nested/archive.zip",
            b"PK Nested archive content"
        )
    
    return zip_path, temp_dir


def example_1_health_check(client):
    """Example 1: Check API health"""
    print("\n" + "=" * 60)
    print("Example 1: Health Check")
    print("=" * 60)
    
    try:
        result = client.health_check()
        print(f"✓ API is healthy")
        print(f"  Status: {result['status']}")
        print(f"  Version: {result['version']}")
        print(f"  Timestamp: {result['timestamp']}")
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def example_2_inspect_dataset(client, zip_path):
    """Example 2: Inspect a dataset"""
    print("\n" + "=" * 60)
    print("Example 2: Inspect Dataset")
    print("=" * 60)
    
    try:
        result = client.inspect_dataset(zip_path)
        
        if result.get('status') == 'success':
            print(f"✓ Dataset inspected successfully")
            print(f"\n  Dataset: {Path(result['file_path']).name}")
            print(f"  Total files: {result['total_files']}")
            print(f"  Total size: {result['total_size_mb']} MB")
            print(f"\n  Files found:")
            for i, file_info in enumerate(result['files'][:5], 1):
                file_type = []
                if file_info['is_pdf']:
                    file_type.append('PDF')
                if file_info['is_image']:
                    file_type.append('Image')
                if file_info['is_archive']:
                    file_type.append('Archive')
                type_str = ', '.join(file_type) if file_type else 'Other'
                print(f"    {i}. {file_info['name']}")
                print(f"       Size: {file_info['size']} bytes, Type: {type_str}")
            
            if result['total_files'] > 5:
                print(f"    ... and {result['total_files'] - 5} more files")
            
            return True
        else:
            print(f"✗ Inspection failed: {result}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def example_3_upload_and_inspect(client, zip_path):
    """Example 3: Upload and inspect a dataset"""
    print("\n" + "=" * 60)
    print("Example 3: Upload and Inspect Dataset")
    print("=" * 60)
    
    try:
        result = client.upload_and_inspect(zip_path)
        
        if result.get('status') == 'success':
            print(f"✓ Dataset uploaded and inspected successfully")
            print(f"\n  Dataset: {result['file_path']}")
            print(f"  Total files: {result['total_files']}")
            print(f"  Total size: {result['total_size_mb']} MB")
            
            # Show archive structure
            if 'archive_structure' in result:
                print(f"\n  Directory structure:")
                _print_structure(result['archive_structure'], indent=4)
            
            return True
        else:
            print(f"✗ Upload failed: {result}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def _print_structure(structure, indent=0):
    """Helper to print directory structure"""
    prefix = " " * indent
    
    if 'directories' in structure:
        for dir_name, dir_content in structure['directories'].items():
            print(f"{prefix}📁 {dir_name}/")
            _print_structure(dir_content, indent + 2)
    
    if 'files' in structure:
        for file_info in structure['files']:
            print(f"{prefix}📄 {file_info['name']} ({file_info['size']} bytes)")


def example_4_run_etl_dry_run(client):
    """Example 4: Run ETL in dry-run mode (no actual files needed)"""
    print("\n" + "=" * 60)
    print("Example 4: Run ETL Process (Dry Run)")
    print("=" * 60)
    
    # This example shows the request format, but won't actually run
    # since we don't have real source files
    print("This example demonstrates the API call format.")
    print("To actually run, you need real source and destination paths.")
    print("\nExample request:")
    print(json.dumps({
        "source_path": "/path/to/medical/records",
        "destination_path": "/path/to/organized/output",
        "mapping_file": "/path/to/mapping.xlsx",  # Optional
        "dry_run": True
    }, indent=2))
    
    print("\nExpected response structure:")
    print(json.dumps({
        "status": "success",
        "session_id": "abc123...",
        "message": "ETL process completed successfully",
        "results": {
            "total_files_found": 100,
            "total_files_processed": 95,
            "successful_extractions": 90,
            "organized_files": 85
        }
    }, indent=2))
    
    return True


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("Medical ETL System API - Usage Examples")
    print("=" * 60)
    
    # Note: API must be running for these examples to work
    print("\n⚠️  NOTE: Make sure the API server is running:")
    print("   python api.py")
    print("   OR")
    print("   uvicorn api:app --reload")
    
    # Create client
    client = MedicalETLAPIClient()
    
    # Check if API is running
    try:
        health = client.health_check()
        print(f"\n✓ API server is running (version {health['version']})")
    except Exception as e:
        print(f"\n✗ API server is not running or not reachable")
        print(f"   Error: {str(e)}")
        print("\n   Please start the API server and try again.")
        return 1
    
    # Create sample dataset
    print("\nCreating sample dataset...")
    zip_path, temp_dir = create_sample_dataset()
    print(f"✓ Sample dataset created: {zip_path}")
    
    try:
        # Run examples
        results = []
        results.append(("Health Check", example_1_health_check(client)))
        results.append(("Inspect Dataset", example_2_inspect_dataset(client, zip_path)))
        results.append(("Upload and Inspect", example_3_upload_and_inspect(client, zip_path)))
        results.append(("ETL Dry Run (demo)", example_4_run_etl_dry_run(client)))
        
        # Summary
        print("\n" + "=" * 60)
        print("Example Summary")
        print("=" * 60)
        
        for name, passed in results:
            status = "✓ SUCCESS" if passed else "✗ FAILED"
            print(f"{status:12} - {name}")
        
        print("\n" + "=" * 60)
        print("Additional Information")
        print("=" * 60)
        print("\nFor more examples, see:")
        print("  - API_README.md - Complete API documentation")
        print("  - Medical_ETL_API.postman_collection.json - Postman collection")
        print("  - http://localhost:8000/docs - Interactive API docs")
        
    finally:
        # Cleanup
        import os
        import shutil
        if os.path.exists(zip_path):
            os.unlink(zip_path)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    return 0


if __name__ == "__main__":
    exit(main())
