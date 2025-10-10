"""
Simple test to demonstrate current logging capabilities
"""

import sys
from pathlib import Path

# Add modules to path
sys.path.append(str(Path(__file__).parent / "modules"))
sys.path.append(str(Path(__file__).parent / "config"))

# Import only the logger to avoid dependency issues
from config.config import Config
import logging
import json
from datetime import datetime

def test_simple_logging():
    """Test basic logging without complex imports"""
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create a simple log file
    timestamp = datetime.now().strftime("%m%d%Y%H%M")
    log_file = logs_dir / f"Texas_Houston_{timestamp}.log"
    
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("ETL_Test")
    
    print(f"Creating log file: {log_file}")
    
    # Log various types of information
    logger.info("=== ETL SESSION START ===")
    logger.info(f"Session ID: ETL_SESSION_{timestamp}")
    logger.info("Source Path: C:/Projects/MedicalRecords/Texas_Houston_Clinic/2024_Records")
    logger.info("Destination Path: C:/ProcessedRecords/Texas_Houston")
    logger.info("Run Type: test_run")
    
    # File processing example
    logger.info("=== FILE PROCESSING START ===")
    file_info = {
        'source_path': 'C:/source/patient_001_xray.pdf',
        'destination_path': 'C:/destination/John_Doe/patient_001_xray.pdf',
        'file_size_mb': 2.048,
        'file_type': 'pdf',
        'operation_id': 'OP_001'
    }
    logger.info(f"Processing File: {json.dumps(file_info, indent=2)}")
    
    # Patient data parsing
    patient_data = {
        'first_name': 'John',
        'last_name': 'Doe', 
        'dob': '1985-05-15',
        'patient_id': 'P001234',
        'parsing_method': 'filename_extraction'
    }
    logger.info(f"Patient Data Extracted: {json.dumps(patient_data, indent=2)}")
    
    # Processing methods tracking
    logger.info("Processing Method: filename_parsing - SUCCESS")
    logger.info("File Size - Source: 2.048 MB, Destination: 2.048 MB")
    logger.info("File Organization: SUCCESS - Moved to patient folder")
    
    # Error example
    logger.error("ERROR: Unable to parse patient data from file: corrupted_file.pdf")
    logger.warning("WARNING: File size larger than 50MB - consider compression")
    
    # Patient summary
    patient_summary = {
        'patient_key': 'John_Doe_1985-05-15',
        'total_files': 3,
        'total_size_mb': 6.144,
        'processing_methods': ['filename_parsing', 'ocr_extraction'],
        'success_count': 2,
        'error_count': 1,
        'files': [
            {'file': 'patient_001_xray.pdf', 'size_mb': 2.048, 'status': 'success'},
            {'file': 'patient_002_lab.pdf', 'size_mb': 1.024, 'status': 'success'}, 
            {'file': 'patient_003_scan.pdf', 'size_mb': 3.072, 'status': 'error'}
        ]
    }
    logger.info(f"=== PATIENT SUMMARY ===")
    logger.info(f"Patient: {json.dumps(patient_summary, indent=2)}")
    
    # Session summary
    session_summary = {
        'total_files_processed': 5,
        'successful_extractions': 4,
        'failed_extractions': 1,
        'organized_files': 4,
        'unique_patients': 2,
        'total_source_size_mb': 15.36,
        'total_destination_size_mb': 12.288,
        'skipped_files': 1,
        'duplicate_files': 0,
        'processing_time_minutes': 5.5
    }
    logger.info("=== SESSION SUMMARY ===")
    logger.info(f"Session Results: {json.dumps(session_summary, indent=2)}")
    
    logger.info("=== ETL SESSION END ===")
    
    return log_file

if __name__ == "__main__":
    log_path = test_simple_logging()
    print(f"\nLog file created: {log_path}")
    print(f"File size: {log_path.stat().st_size} bytes")