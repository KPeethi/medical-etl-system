"""
Test script to demonstrate current logging capabilities
"""

import sys
from pathlib import Path

# Add modules to path
sys.path.append(str(Path(__file__).parent / "modules"))
sys.path.append(str(Path(__file__).parent / "config"))

from modules.etl_logger import ETLLogger

def test_logging():
    """Test the current logging system"""
    
    # Create a test logger with sample source path
    test_source = "<configurable_test_source>"
    logger = ETLLogger("test_run", "INFO", test_source, max_log_size_mb=50)
    
    print(f"Log file created at: {logger.log_file_path}")
    print(f"Session ID: {logger.session_id}")
    
    # Test different types of logging
    logger.logger.info("Starting test logging demonstration")
    
    # Test file processing logging
    test_file_info = {
        'name': 'patient_001_xray.pdf',
        'size': 2048576,  # 2MB
        'type': 'pdf',
        'created': '2024-10-09T10:30:00'
    }
    
    operation_id = logger.log_file_processing_start(
        source_path="C:/source/patient_001_xray.pdf",
        file_info=test_file_info,
        destination_path="C:/destination/John_Doe/patient_001_xray.pdf"
    )
    
    # Test patient parsing logging
    test_patient_data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'dob': '1985-05-15',
        'patient_id': 'P001234'
    }
    
    logger.log_patient_parsing("patient_001_xray.pdf", test_patient_data)
    
    # Test error logging
    logger.log_error("Test Error", "This is a test error message", {
        'file': 'test_file.pdf',
        'error_code': 'TEST_001'
    })
    
    # Test warning logging
    logger.log_warning("Test Warning", "This is a test warning message")
    
    # Test file processing completion
    logger.log_file_processing_end(operation_id, {
        'success': True,
        'destination_path': "C:/destination/John_Doe/patient_001_xray.pdf",
        'processing_method': 'filename_parsing'
    })
    
    # Test patient summary
    test_patients = {
        'John_Doe_1985-05-15': {
            'patient_info': test_patient_data,
            'files': [
                {
                    'file_path': 'patient_001_xray.pdf',
                    'file_size_mb': 2.0,
                    'data_source': 'filename_parsing',
                    'success': True
                }
            ],
            'total_files': 1,
            'total_size_mb': 2.0,
            'processing_methods': ['filename_parsing'],
            'success_count': 1,
            'error_count': 0
        }
    }
    
    # Test session finalization
    session_summary = {
        'total_files_processed': 1,
        'successful_extractions': 1,
        'organized_files': 1,
        'patients': test_patients,
        'processing_results': {
            'total_files_found': 1,
            'errors': [],
            'warnings': ['Test warning message']
        }
    }
    
    logger.finalize_session(session_summary)
    
    return logger.log_file_path

if __name__ == "__main__":
    log_path = test_logging()
    print(f"\nTest completed. Check log file at: {log_path}")