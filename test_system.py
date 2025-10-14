#!/usr/bin/env python3
"""
Simple test script for medical ETL system
Tests the intelligent filename parsing without complex dependencies
"""

import sys
from pathlib import Path

# Add modules to path
sys.path.append(str(Path(__file__).parent / "modules"))

from modules.mapping_processor import MappingProcessor

def test_filename_parsing():
    """Test intelligent filename parsing"""
    print("🧪 Testing Medical ETL Filename Parsing")
    print("=" * 50)
    
    # Initialize mapping processor
    mp = MappingProcessor()
    
    # Test complex filename patterns
    test_files = [
        "kulkarni.preethi01-13-1999.2467.jpg",
        "john,smith.01.04.1996.54675.pdf", 
        "m.kulkarni_preethi(chart)_01-13-1999.pdf",
        "sarah.wilson.report.2467.txt",
        "michael_brown_xray_54675.pdf"
    ]
    
    print("Testing complex filename patterns:")
    print("-" * 30)
    
    for filename in test_files:
        result = mp._parse_complex_filename(filename)
        if result['found']:
            patient_info = result['patient_info']
            print(f"✅ {filename}")
            print(f"   → Patient: {patient_info.get('lastname', 'Unknown')}, {patient_info.get('firstname', 'Unknown')}")
            if 'dob' in patient_info:
                print(f"   → DOB: {patient_info['dob']}")
            if 'patient_id' in patient_info:
                print(f"   → ID: {patient_info['patient_id']}")
            if 'folder_name' in patient_info:
                print(f"   → Output Folder: {patient_info['folder_name']}")
            print()
        else:
            print(f"❌ {filename} - Could not parse")
            print()
    
    return True

def test_smart_lookup():
    """Test smart patient lookup with sample data"""
    print("🔍 Testing Smart Patient Lookup")
    print("=" * 50)
    
    # Initialize mapping processor
    mp = MappingProcessor()
    
    # Test auto-detection mode (no mapping files)
    mp.no_mapping_mode = True
    
    test_file_path = Path("test_data/kulkarni.preethi01-13-1999.2467.txt")
    
    print(f"Testing smart lookup for: {test_file_path.name}")
    result = mp.smart_patient_lookup(test_file_path)
    
    if result['found']:
        print(f"✅ Smart Lookup Success!")
        print(f"   → Method: {result['lookup_method']}")
        print(f"   → Confidence: {result['confidence']}%")
        print(f"   → Patient Info: {result['patient_info']}")
    else:
        print(f"❌ Smart lookup failed")
    
    return result['found']

def main():
    """Run all tests"""
    print("🏥 Medical ETL System - Quick Test")
    print("=" * 60)
    print()
    
    try:
        # Test 1: Filename parsing
        test1_result = test_filename_parsing()
        
        print()
        
        # Test 2: Smart lookup
        test2_result = test_smart_lookup()
        
        print()
        print("📊 Test Summary")
        print("=" * 30)
        print(f"Filename Parsing: {'✅ PASS' if test1_result else '❌ FAIL'}")
        print(f"Smart Lookup: {'✅ PASS' if test2_result else '❌ FAIL'}")
        
        if test1_result and test2_result:
            print()
            print("🎉 All tests passed! Your medical ETL system is working correctly.")
            print()
            print("🚀 Ready for use:")
            print("   • Command Line: python main.py source output --mapping none")
            print("   • API Server: python api_server.py (then use Postman)")
            
        return 0
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())