"""
Comprehensive Logging System for Medical ETL
Provides detailed logging for both dry-run and real-run modes
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from config.config import Config

# Custom formatter for structured logging
class ETLFormatter(logging.Formatter):
    """Custom formatter for ETL logging with structured data"""
    
    def format(self, record):
        # Add timestamp
        record.timestamp = datetime.now().isoformat()
        
        # Add context if available
        if hasattr(record, 'context'):
            record.context_info = json.dumps(record.context, default=str)
        else:
            record.context_info = ""
        
        return super().format(record)


class ETLLogger:
    """Comprehensive logging system for ETL operations"""
    
    def __init__(self, run_type: str = "unknown", log_level: str = "INFO", source_path: str = "", max_log_size_mb: int = 50):
        self.config = Config()
        self.run_type = run_type
        self.source_path = source_path
        self.max_log_size_mb = max_log_size_mb
        self.current_log_part = 1
        
        # Generate smart log naming from source path
        self.session_id = self._generate_session_id_from_path(source_path)
        self.log_file_path = self._get_smart_log_path(run_type, self.session_id)
        
        # Initialize logging
        self._setup_logging(log_level)
        
        # Enhanced session tracking
        self.session_stats = {
            'start_time': datetime.now(),
            'end_time': None,
            'run_type': run_type,
            'session_id': self.session_id,
            'source_path': source_path,
            'total_files_processed': 0,
            'total_source_size_mb': 0,
            'total_destination_size_mb': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'skipped_operations': 0,
            'duplicate_files_found': 0,
            'unmapped_files': 0,
            'patients_processed': {},  # Changed to dict to track file counts per patient
            'patient_file_counts': {},  # Track how many files each patient has
            'processing_methods': {
                'mapping_file': 0,
                'filename_parsing': 0, 
                'basic_ocr': 0,
                'deep_pdf_scan': 0,
                'combined_partial': 0,
                'unmapped': 0
            },
            'file_type_counts': {},
            'errors': [],
            'warnings': [],
            'skipped_reasons': {}
        }
        
        # File processing tracking with enhanced details
        self.file_operations = []
        self.patient_operations = {}
        self.error_summary = {}
        
        self.logger = logging.getLogger(f"ETL.{run_type}")
        self._log_session_start()
    
    def _generate_session_id_from_path(self, source_path: str) -> str:
        """Generate session ID from source path following state_practice_mmddyyyyhhmm format"""
        try:
            timestamp = datetime.now().strftime("%m%d%Y%H%M")
            
            if not source_path:
                return f"unknown_unknown_{timestamp}"
            
            # Parse path for state and practice
            # Example: "network/practice record/california(CA)/preethi clinic"
            path_parts = source_path.replace('\\', '/').split('/')
            
            state = "unknown"
            practice = "unknown"
            
            # Look for state patterns
            for part in path_parts:
                part_lower = part.lower().strip()
                
                # Check for state indicators
                if '(' in part and ')' in part:
                    # Extract state abbreviation from parentheses
                    state_match = part.split('(')[1].split(')')[0]
                    if len(state_match) == 2:
                        state = state_match.upper()
                elif any(state_name in part_lower for state_name in [
                    'california', 'texas', 'florida', 'new york', 'illinois', 
                    'pennsylvania', 'ohio', 'georgia', 'north carolina', 'michigan'
                ]):
                    state = part_lower.replace(' ', '').replace('california', 'CA').replace('texas', 'TX').replace('florida', 'FL')[:10]
                
                # Check for practice/clinic indicators
                if any(keyword in part_lower for keyword in [
                    'clinic', 'practice', 'medical', 'hospital', 'center', 'group'
                ]):
                    practice = part.replace(' ', '').replace('-', '').replace('_', '')[:15]
            
            # Clean and format
            state = state.replace(' ', '').replace('-', '').replace('_', '')
            practice = practice.replace(' ', '').replace('-', '').replace('_', '')
            
            return f"{state}_{practice}_{timestamp}"
            
        except Exception as e:
            timestamp = datetime.now().strftime("%m%d%Y%H%M")
            return f"unknown_unknown_{timestamp}"
    
    def _get_smart_log_path(self, run_type: str, session_id: str) -> Path:
        """Get log file path with smart naming"""
        filename = f"{session_id}_{run_type}_part{self.current_log_part}.log"
        return self.config.LOGS_DIR / filename
    
    def _check_log_size_and_rotate(self):
        """Check if log file is too large and rotate to new part"""
        try:
            if self.log_file_path.exists():
                size_mb = self.log_file_path.stat().st_size / (1024 * 1024)
                
                if size_mb > self.max_log_size_mb:
                    # Close current handlers
                    for handler in self.logger.handlers[:]:
                        handler.close()
                        self.logger.removeHandler(handler)
                    
                    # Increment part number and create new log file
                    self.current_log_part += 1
                    self.log_file_path = self._get_smart_log_path(self.run_type, self.session_id)
                    
                    # Recreate file handler
                    file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
                    file_handler.setLevel(logging.DEBUG)
                    
                    detailed_formatter = ETLFormatter(
                        '%(timestamp)s | %(levelname)s | %(name)s | %(message)s | %(context_info)s'
                    )
                    file_handler.setFormatter(detailed_formatter)
                    self.logger.addHandler(file_handler)
                    
                    # Log the rotation
                    self.logger.info(f"Log rotated to part {self.current_log_part} (previous part was {size_mb:.1f}MB)")
                    
        except Exception as e:
            self.logger.warning(f"Error checking log size: {str(e)}")
    
    def log_file_processing_start(self, source_file: Path, file_info: Dict[str, Any]):
        """Log start of file processing with enhanced details"""
        operation_id = f"file_{len(self.file_operations)}"
        
        # Calculate source file size in MB
        source_size_mb = file_info.get('size', 0) / (1024 * 1024)
        self.session_stats['total_source_size_mb'] += source_size_mb
        
        # Track file type
        file_type = file_info.get('suffix', '').lower()
        self.session_stats['file_type_counts'][file_type] = self.session_stats['file_type_counts'].get(file_type, 0) + 1
        
        operation = {
            'operation_id': operation_id,
            'source_file': str(source_file),
            'source_size_mb': round(source_size_mb, 3),
            'file_type': file_type,
            'start_time': datetime.now(),
            'end_time': None,
            'status': 'in_progress',
            'destination_file': '',
            'destination_size_mb': 0,
            'patient_data': {},
            'data_source': 'unknown',
            'processing_method': 'unknown',
            'pages_processed': 0,
            'ocr_confidence': 0,
            'actions_taken': [],
            'errors': [],
            'warnings': [],
            'skipped': False,
            'skip_reason': ''
        }
        
        self.file_operations.append(operation)
        self.session_stats['total_files_processed'] += 1
        
        # Check log size and rotate if needed
        self._check_log_size_and_rotate()
        
        self.logger.info(
            f"Processing file: {source_file.name} ({source_size_mb:.2f}MB)",
            extra={'context': {
                'operation_id': operation_id,
                'source_file': str(source_file),
                'source_size_mb': source_size_mb,
                'file_type': file_type,
                'total_files_processed': self.session_stats['total_files_processed']
            }}
        )
        
        return operation_id
    
    def log_file_processing_end(self, operation_id: str, result: Dict[str, Any]):
        """Log end of file processing with comprehensive details"""
        operation = self._get_operation_by_id(operation_id)
        if not operation:
            self.logger.error(f"Operation {operation_id} not found")
            return
        
        operation['end_time'] = datetime.now()
        operation['status'] = 'completed' if result.get('success', False) else 'failed'
        
        # Enhanced result tracking
        if result.get('destination_path'):
            operation['destination_file'] = str(result['destination_path'])
            try:
                dest_path = Path(result['destination_path'])
                if dest_path.exists():
                    dest_size_mb = dest_path.stat().st_size / (1024 * 1024)
                    operation['destination_size_mb'] = round(dest_size_mb, 3)
                    self.session_stats['total_destination_size_mb'] += dest_size_mb
            except:
                pass
        
        # Track patient data and processing method
        patient_data = result.get('patient_data', {})
        operation['patient_data'] = patient_data
        operation['data_source'] = result.get('data_source', 'unknown')
        
        # Track processing method statistics
        data_source = result.get('data_source', 'unknown')
        if data_source in self.session_stats['processing_methods']:
            self.session_stats['processing_methods'][data_source] += 1
        
        # Track deep scan details
        if result.get('deep_scan_result'):
            deep_scan = result['deep_scan_result']
            operation['pages_processed'] = deep_scan.get('pages_processed', 0)
            operation['processing_method'] = f"deep_scan_found_page_{deep_scan.get('found_on_page', 0)}"
        
        # Track OCR confidence
        if result.get('ocr_result'):
            operation['ocr_confidence'] = result['ocr_result'].get('confidence', 0)
        
        # Track patient file counts
        patient_key = self._get_patient_key(patient_data)
        if patient_key:
            if patient_key not in self.session_stats['patient_file_counts']:
                self.session_stats['patient_file_counts'][patient_key] = 0
            self.session_stats['patient_file_counts'][patient_key] += 1
            
            # Track patient processing details
            if patient_key not in self.session_stats['patients_processed']:
                self.session_stats['patients_processed'][patient_key] = {
                    'first_name': patient_data.get('firstname', ''),
                    'last_name': patient_data.get('lastname', ''),
                    'dob': patient_data.get('dob', ''),
                    'id': patient_data.get('id', ''),
                    'files': [],
                    'total_size_mb': 0
                }
            
            self.session_stats['patients_processed'][patient_key]['files'].append({
                'source_file': operation['source_file'],
                'destination_file': operation['destination_file'],
                'size_mb': operation['source_size_mb'],
                'data_source': data_source
            })
            self.session_stats['patients_processed'][patient_key]['total_size_mb'] += operation['source_size_mb']
        
        # Track status
        if result.get('success', False):
            self.session_stats['successful_operations'] += 1
        else:
            self.session_stats['failed_operations'] += 1
            if result.get('error'):
                operation['errors'].append(result['error'])
                self.session_stats['errors'].append({
                    'operation_id': operation_id,
                    'error': result['error'],
                    'timestamp': datetime.now(),
                    'source_file': operation['source_file']
                })
        
        # Track skipped files
        if result.get('skipped', False):
            operation['skipped'] = True
            operation['skip_reason'] = result.get('skip_reason', 'Unknown')
            self.session_stats['skipped_operations'] += 1
            
            skip_reason = result.get('skip_reason', 'Unknown')
            self.session_stats['skipped_reasons'][skip_reason] = self.session_stats['skipped_reasons'].get(skip_reason, 0) + 1
        
        # Calculate processing duration
        duration = 0
        if operation['start_time'] and operation['end_time']:
            duration = (operation['end_time'] - operation['start_time']).total_seconds()
        
        # Check log size and rotate if needed
        self._check_log_size_and_rotate()
        
        # Comprehensive completion log
        self.logger.info(
            f"File completed: {Path(operation['source_file']).name} -> "
            f"Status: {operation['status']}, Method: {data_source}, "
            f"Duration: {duration:.1f}s, Size: {operation['source_size_mb']:.2f}MB",
            extra={'context': {
                'operation_id': operation_id,
                'status': operation['status'],
                'source_file': operation['source_file'],
                'destination_file': operation['destination_file'],
                'source_size_mb': operation['source_size_mb'],
                'destination_size_mb': operation['destination_size_mb'],
                'data_source': data_source,
                'processing_duration_sec': duration,
                'patient_data': patient_data,
                'pages_processed': operation['pages_processed'],
                'ocr_confidence': operation['ocr_confidence'],
                'skipped': operation['skipped'],
                'skip_reason': operation['skip_reason']
            }}
        )
    
    def log_extraction_operation(self, archive_path: Path, extracted_files: List[Path]):
        """Log file extraction operation"""
        self.logger.info(
            f"Extracted {len(extracted_files)} files from archive: {archive_path.name}",
            extra={'context': {
                'archive_path': str(archive_path),
                'extracted_count': len(extracted_files),
                'extracted_files': [str(f) for f in extracted_files[:10]]  # First 10 files
            }}
        )
    
    def log_ocr_operation(self, file_path: Path, ocr_result: Dict[str, Any]):
        """Log OCR operation"""
        success = ocr_result.get('success', False)
        confidence = ocr_result.get('confidence', 0)
        text_length = len(ocr_result.get('text', ''))
        
        self.logger.info(
            f"OCR processing: {file_path.name} - Success: {success}, Confidence: {confidence:.1f}%",
            extra={'context': {
                'file_path': str(file_path),
                'ocr_success': success,
                'confidence': confidence,
                'text_length': text_length,
                'error': ocr_result.get('error')
            }}
        )
    
    def log_patient_parsing(self, file_path: Path, parsing_result: Dict[str, Any]):
        """Log patient data parsing"""
        confidence = parsing_result.get('confidence', 0)
        method = parsing_result.get('parsing_method', 'unknown')
        
        self.logger.info(
            f"Patient parsing: {file_path.name} - Method: {method}, Confidence: {confidence}%",
            extra={'context': {
                'file_path': str(file_path),
                'parsing_method': method,
                'confidence': confidence,
                'patient_data': {
                    'firstname': parsing_result.get('firstname', ''),
                    'lastname': parsing_result.get('lastname', ''),
                    'dob': parsing_result.get('dob', ''),
                    'id': parsing_result.get('id', '')
                }
            }}
        )
    
    def log_duplicate_detection(self, duplicates_found: Dict[str, List]):
        """Log duplicate detection results"""
        exact_count = len(duplicates_found.get('exact_duplicates', []))
        potential_count = len(duplicates_found.get('potential_duplicates', []))
        
        self.session_stats['duplicate_files_found'] = exact_count + potential_count
        
        self.logger.info(
            f"Duplicate detection completed - Exact: {exact_count}, Potential: {potential_count}",
            extra={'context': {
                'exact_duplicates': exact_count,
                'potential_duplicates': potential_count,
                'patient_variations': len(duplicates_found.get('patient_variations', []))
            }}
        )
    
    def log_file_organization(self, source_path: Path, organization_result: Dict[str, Any]):
        """Log file organization operation"""
        action = organization_result.get('action', 'unknown')
        success = organization_result.get('success', False)
        
        if action == 'moved_to_duplicates':
            self.session_stats['duplicate_files_found'] += 1
        elif action == 'moved_to_unmapped':
            self.session_stats['unmapped_files'] += 1
        
        self.logger.info(
            f"File organization: {source_path.name} - Action: {action}, Success: {success}",
            extra={'context': {
                'source_path': str(source_path),
                'action': action,
                'success': success,
                'destination_path': organization_result.get('destination_path', ''),
                'patient_folder': organization_result.get('patient_folder', ''),
                'new_filename': organization_result.get('new_filename', '')
            }}
        )
    
    def log_mapping_operation(self, mapping_file: Path, mapping_stats: Dict[str, Any]):
        """Log mapping file processing"""
        total_records = mapping_stats.get('total_records', 0)
        identified_fields = mapping_stats.get('identified_fields', {})
        
        self.logger.info(
            f"Mapping file loaded: {mapping_file.name} - Records: {total_records}",
            extra={'context': {
                'mapping_file': str(mapping_file),
                'total_records': total_records,
                'identified_fields': identified_fields,
                'missing_data': mapping_stats.get('missing_data', {})
            }}
        )
    
    def log_error(self, operation: str, error: str, context: Optional[Dict[str, Any]] = None):
        """Log error with context"""
        error_entry = {
            'operation': operation,
            'error': error,
            'timestamp': datetime.now(),
            'context': context or {}
        }
        
        self.session_stats['errors'].append(error_entry)
        
        self.logger.error(
            f"{operation} - Error: {error}",
            extra={'context': context or {}}
        )
    
    def log_warning(self, operation: str, warning: str, context: Optional[Dict[str, Any]] = None):
        """Log warning with context"""
        warning_entry = {
            'operation': operation,
            'warning': warning,
            'timestamp': datetime.now(),
            'context': context or {}
        }
        
        self.session_stats['warnings'].append(warning_entry)
        
        self.logger.warning(
            f"{operation} - Warning: {warning}",
            extra={'context': context or {}}
        )
    
    def log_dry_run_simulation(self, operation: str, details: Dict[str, Any]):
        """Log dry run simulation details"""
        self.logger.info(
            f"DRY RUN - {operation}: {details.get('summary', '')}",
            extra={'context': {
                'dry_run': True,
                'operation': operation,
                'details': details
            }}
        )
    
    def log_patient_summary(self):
        """Log comprehensive patient processing summary"""
        self._check_log_size_and_rotate()
        
        self.logger.info("=" * 80)
        self.logger.info("PATIENT PROCESSING SUMMARY")
        self.logger.info("=" * 80)
        
        total_patients = len(self.session_stats['patients_processed'])
        self.logger.info(f"Total Unique Patients Processed: {total_patients}")
        
        # Log each patient with file counts and details
        for patient_key, patient_info in self.session_stats['patients_processed'].items():
            file_count = len(patient_info['files'])
            total_size = patient_info['total_size_mb']
            
            patient_name = f"{patient_info['last_name']}, {patient_info['first_name']}"
            if patient_info['dob']:
                patient_name += f" ({patient_info['dob']})"
            if patient_info['id']:
                patient_name += f" [ID: {patient_info['id']}]"
            
            self.logger.info(
                f"Patient: {patient_name} - Files: {file_count}, Total Size: {total_size:.2f}MB",
                extra={'context': {
                    'patient_key': patient_key,
                    'patient_name': patient_name,
                    'file_count': file_count,
                    'total_size_mb': total_size,
                    'files': patient_info['files']
                }}
            )
            
            # Log individual files for this patient
            for file_info in patient_info['files']:
                self.logger.info(
                    f"  -> {Path(file_info['source_file']).name} "
                    f"({file_info['size_mb']:.2f}MB, {file_info['data_source']})",
                    extra={'context': file_info}
                )
        
        # Log processing method statistics
        self.logger.info("\nPROCESSING METHODS SUMMARY:")
        for method, count in self.session_stats['processing_methods'].items():
            if count > 0:
                percentage = (count / self.session_stats['total_files_processed']) * 100
                self.logger.info(f"{method}: {count} files ({percentage:.1f}%)")
        
        # Log file type statistics
        self.logger.info("\nFILE TYPE BREAKDOWN:")
        for file_type, count in self.session_stats['file_type_counts'].items():
            percentage = (count / self.session_stats['total_files_processed']) * 100
            self.logger.info(f"{file_type}: {count} files ({percentage:.1f}%)")
        
        # Log skipped files summary
        if self.session_stats['skipped_operations'] > 0:
            self.logger.info(f"\nSKIPPED FILES: {self.session_stats['skipped_operations']}")
            for reason, count in self.session_stats['skipped_reasons'].items():
                self.logger.info(f"  {reason}: {count} files")
    
    def finalize_session(self):
        """Finalize logging session and generate comprehensive summary"""
        self.session_stats['end_time'] = datetime.now()
        duration = self.session_stats['end_time'] - self.session_stats['start_time']
        
        # Log patient summary before finalizing
        self.log_patient_summary()
        
        # Calculate final statistics
        summary = {
            'session_id': self.session_id,
            'run_type': self.run_type,
            'source_path': self.source_path,
            'duration_seconds': duration.total_seconds(),
            'total_files_processed': self.session_stats['total_files_processed'],
            'total_source_size_mb': round(self.session_stats['total_source_size_mb'], 2),
            'total_destination_size_mb': round(self.session_stats['total_destination_size_mb'], 2),
            'successful_operations': self.session_stats['successful_operations'],
            'failed_operations': self.session_stats['failed_operations'],
            'skipped_operations': self.session_stats['skipped_operations'],
            'duplicate_files_found': self.session_stats['duplicate_files_found'],
            'unmapped_files': self.session_stats['unmapped_files'],
            'unique_patients_processed': len(self.session_stats['patients_processed']),
            'total_errors': len(self.session_stats['errors']),
            'total_warnings': len(self.session_stats['warnings']),
            'log_parts_created': self.current_log_part,
            'processing_methods': self.session_stats['processing_methods'],
            'file_type_counts': self.session_stats['file_type_counts'],
            'skipped_reasons': self.session_stats['skipped_reasons']
        }
        
        # Final comprehensive log
        self._check_log_size_and_rotate()
        self.logger.info("=" * 80)
        self.logger.info("ETL SESSION FINAL SUMMARY")
        self.logger.info("=" * 80)
        self.logger.info(f"Session ID: {self.session_id}")
        self.logger.info(f"Duration: {duration}")
        self.logger.info(f"Source Path: {self.source_path}")
        self.logger.info(f"Files Processed: {summary['total_files_processed']}")
        self.logger.info(f"Source Data Size: {summary['total_source_size_mb']:.2f}MB")
        self.logger.info(f"Destination Data Size: {summary['total_destination_size_mb']:.2f}MB")
        self.logger.info(f"Successful: {summary['successful_operations']}")
        self.logger.info(f"Failed: {summary['failed_operations']}")
        self.logger.info(f"Skipped: {summary['skipped_operations']}")
        self.logger.info(f"Unique Patients: {summary['unique_patients_processed']}")
        self.logger.info(f"Log Parts Created: {summary['log_parts_created']}")
        self.logger.info(f"Errors: {summary['total_errors']}")
        self.logger.info(f"Warnings: {summary['total_warnings']}")
        
        # Save session summary to separate file
        self._save_session_summary(summary)
        
        # Export to Excel format (if available)
        self._export_to_excel(summary)
        
        return summary
    
    def _export_to_excel(self, summary: Dict[str, Any]):
        """Export session logs to Excel format"""
        try:
            from modules.excel_manager import ExcelManager
            
            excel_manager = ExcelManager()
            
            # Create Excel log file
            excel_log_path = self.config.LOGS_DIR / f"session_log_{self.session_id}.xlsx"
            session_summary_path = self.config.LOGS_DIR / f"session_summary_{self.session_id}.json"
            
            success = excel_manager.export_session_to_excel(session_summary_path, excel_log_path)
            
            if success:
                self.logger.info(f"Excel log exported to: {excel_log_path}")
            else:
                self.logger.warning("Failed to export Excel log")
                
        except Exception as e:
            self.logger.warning(f"Excel export not available: {str(e)}")
            # Excel export is optional, don't fail the session
    
    def _save_session_summary(self, summary: Dict[str, Any]):
        """Save session summary to JSON file"""
        try:
            summary_file = self.config.LOGS_DIR / f"session_summary_{self.session_id}.json"
            
            # Convert datetime objects and sets to serializable format
            serializable_stats = self.session_stats.copy()
            serializable_stats['start_time'] = serializable_stats['start_time'].isoformat()
            if serializable_stats['end_time']:
                serializable_stats['end_time'] = serializable_stats['end_time'].isoformat()
            serializable_stats['patients_processed'] = list(serializable_stats['patients_processed'])
            
            # Convert datetime in errors and warnings
            for error in serializable_stats['errors']:
                error['timestamp'] = error['timestamp'].isoformat()
            for warning in serializable_stats['warnings']:
                warning['timestamp'] = warning['timestamp'].isoformat()
            
            full_summary = {
                'summary': summary,
                'detailed_stats': serializable_stats,
                'file_operations': self.file_operations
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(full_summary, f, indent=2, default=str)
            
            self.logger.info(f"Session summary saved to: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving session summary: {str(e)}")
    
    def _get_operation_by_id(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get operation by ID"""
        for operation in self.file_operations:
            if operation['operation_id'] == operation_id:
                return operation
        return None
    
    def _get_patient_key(self, patient_data: Dict[str, str]) -> str:
        """Generate patient key for tracking"""
        lastname = patient_data.get('lastname', '').strip()
        firstname = patient_data.get('firstname', '').strip()
        dob = patient_data.get('dob', '').strip()
        patient_id = patient_data.get('id', '').strip()
        
        if patient_id:
            return f"id:{patient_id}"
        elif lastname and firstname:
            key = f"name:{lastname},{firstname}"
            if dob:
                key += f":{dob}"
            return key
        
        return ""
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        current_time = datetime.now()
        duration = current_time - self.session_stats['start_time']
        
        return {
            'session_id': self.session_id,
            'run_type': self.run_type,
            'duration_seconds': duration.total_seconds(),
            'total_files_processed': self.session_stats['total_files_processed'],
            'successful_operations': self.session_stats['successful_operations'],
            'failed_operations': self.session_stats['failed_operations'],
            'duplicate_files_found': self.session_stats['duplicate_files_found'],
            'unmapped_files': self.session_stats['unmapped_files'],
            'unique_patients_processed': len(self.session_stats['patients_processed']),
            'total_errors': len(self.session_stats['errors']),
            'total_warnings': len(self.session_stats['warnings']),
            'log_file': str(self.log_file_path)
        }


# Utility functions for SSIS integration
def create_ssis_log_entry(operation: str, source_file: str, destination_file: str, 
                         patient_data: Dict[str, str], status: str, 
                         error: Optional[str] = None) -> Dict[str, Any]:
    """Create SSIS-compatible log entry"""
    return {
        'timestamp': datetime.now().isoformat(),
        'operation': operation,
        'source_file': source_file,
        'destination_file': destination_file,
        'patient_id': patient_data.get('id', ''),
        'patient_firstname': patient_data.get('firstname', ''),
        'patient_lastname': patient_data.get('lastname', ''),
        'patient_dob': patient_data.get('dob', ''),
        'status': status,
        'error_message': error or '',
        'file_size': 0,  # Can be filled by caller
        'processing_duration_ms': 0  # Can be filled by caller
    }


def export_logs_for_ssis(log_file_path: Path, output_csv_path: Path):
    """Export logs in CSV format for SSIS consumption"""
    try:
        import pandas as pd
        
        # Read log file and extract structured data
        log_entries = []
        
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    # Parse structured log entries
                    # This would need to be implemented based on the log format
                    pass
                except:
                    continue
        
        # Convert to DataFrame and save as CSV
        if log_entries:
            df = pd.DataFrame(log_entries)
            df.to_csv(output_csv_path, index=False)
            
    except Exception as e:
        logging.error(f"Error exporting logs for SSIS: {str(e)}")