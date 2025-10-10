"""
Main ETL Processor for Medical Files
Orchestrates all components for processing medical records
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add the modules directory to the path
sys.path.append(str(Path(__file__).parent / "modules"))
sys.path.append(str(Path(__file__).parent / "config"))

from modules.file_extractor import FileExtractor
from modules.ocr_processor import OCRProcessor
from modules.patient_parser import PatientParser
from modules.mapping_processor import MappingProcessor
from modules.duplicate_detector import DuplicateDetector
from modules.file_organizer import FileOrganizer
from modules.etl_logger import ETLLogger
from config.config import Config


class MedicalETLProcessor:
    """Main ETL processor for medical files"""
    
    def __init__(self, source_path: Path, destination_path: Path, 
                 mapping_file: Optional[Path] = None, dry_run: bool = False):
        self.config = Config()
        self.source_path = Path(source_path)
        self.destination_path = Path(destination_path)
        self.mapping_file = Path(mapping_file) if mapping_file else None
        self.dry_run = dry_run
        
        # Initialize components
        self.file_extractor = FileExtractor()
        self.ocr_processor = OCRProcessor()
        self.patient_parser = PatientParser()
        self.mapping_processor = MappingProcessor() if mapping_file else None
        self.duplicate_detector = DuplicateDetector()
        self.file_organizer = FileOrganizer(destination_path)
        
        # Initialize logging with smart naming from source path
        run_type = "dry_run" if dry_run else "real_run"
        self.logger = ETLLogger(
            run_type, "INFO", str(source_path), max_log_size_mb=50
        )
        
        # Processing results
        self.processing_results = {
            'total_files_found': 0,
            'total_files_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'mapped_files': 0,
            'unmapped_files': 0,
            'duplicate_files': 0,
            'organized_files': 0,
            'errors': [],
            'warnings': []
        }
    
    def run(self) -> Dict[str, Any]:
        """
        Run the complete ETL process
        
        Returns:
            Dictionary with processing results
        """
        processed_files = []  # Initialize at method level
        
        try:
            self.logger.logger.info(f"Starting ETL process - Source: {self.source_path}, "
                                   f"Destination: {self.destination_path}, Dry Run: {self.dry_run}")
            
            # Validate inputs
            if not self._validate_inputs():
                return self.processing_results
            
            # Load mapping file if provided
            if self.mapping_file and not self._load_mapping_file():
                return self.processing_results
            
            # Step 1: Extract and discover files
            files_to_process = self._discover_and_extract_files()
            self.processing_results['total_files_found'] = len(files_to_process)
            
            if not files_to_process:
                self.logger.log_warning("File Discovery", "No files found to process")
                return self.processing_results
            
            # Step 2: Process each file
            for file_path, original_path in files_to_process:
                try:
                    result = self._process_single_file(file_path, original_path)
                    if result:
                        processed_files.append(result)
                        self.processing_results['total_files_processed'] += 1
                except Exception as e:
                    error_msg = f"Error processing file {file_path}: {str(e)}"
                    self.logger.log_error("File Processing", error_msg, 
                                        {'file_path': str(file_path)})
                    self.processing_results['errors'].append(error_msg)
            
            # Step 3: Detect duplicates
            duplicate_groups = self._detect_duplicates(processed_files)
            
            # Step 4: Organize files
            self._organize_files(processed_files, duplicate_groups)
            
            # Step 5: Generate final report
            final_report = self._generate_final_report()
            
            self.logger.logger.info("ETL process completed successfully")
            return final_report
            
        except Exception as e:
            error_msg = f"Fatal error in ETL process: {str(e)}"
            self.logger.log_error("ETL Process", error_msg)
            self.processing_results['errors'].append(error_msg)
            return self.processing_results
        
        finally:
            # Generate comprehensive patient summaries for logging
            patient_summaries = self._generate_patient_summaries(processed_files)
            
            # Clean up and finalize logging with comprehensive data
            self._cleanup()
            session_summary = {
                'total_files_processed': self.processing_results.get('total_files_processed', 0),
                'successful_extractions': self.processing_results.get('successful_extractions', 0),
                'organized_files': self.processing_results.get('organized_files', 0),
                'patients': patient_summaries,
                'processing_results': self.processing_results
            }
            self.logger.finalize_session(session_summary)
    
    def _validate_inputs(self) -> bool:
        """Validate input parameters"""
        try:
            # Check source path
            if not self.source_path.exists():
                error_msg = f"Source path does not exist: {self.source_path}"
                self.logger.log_error("Input Validation", error_msg)
                self.processing_results['errors'].append(error_msg)
                return False
            
            # Create destination path if it doesn't exist
            if not self.dry_run:
                self.destination_path.mkdir(parents=True, exist_ok=True)
            
            # Check mapping file if provided
            if self.mapping_file and not self.mapping_file.exists():
                error_msg = f"Mapping file does not exist: {self.mapping_file}"
                self.logger.log_error("Input Validation", error_msg)
                self.processing_results['errors'].append(error_msg)
                return False
            
            self.logger.logger.info("Input validation passed")
            return True
            
        except Exception as e:
            error_msg = f"Error during input validation: {str(e)}"
            self.logger.log_error("Input Validation", error_msg)
            self.processing_results['errors'].append(error_msg)
            return False
    
    def _load_mapping_file(self) -> bool:
        """Load and validate mapping file"""
        try:
            success = self.mapping_processor.load_mapping_file(self.mapping_file)
            
            if success:
                stats = self.mapping_processor.get_statistics()
                self.logger.log_mapping_operation(self.mapping_file, stats)
                
                # Validate mapping file structure
                is_valid, issues = self.mapping_processor.validate_mapping_file()
                if not is_valid:
                    for issue in issues:
                        self.logger.log_warning("Mapping Validation", issue)
                        self.processing_results['warnings'].append(f"Mapping issue: {issue}")
                
                return True
            else:
                error_msg = f"Failed to load mapping file: {self.mapping_file}"
                self.logger.log_error("Mapping File", error_msg)
                self.processing_results['errors'].append(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Error loading mapping file: {str(e)}"
            self.logger.log_error("Mapping File", error_msg)
            self.processing_results['errors'].append(error_msg)
            return False
    
    def _discover_and_extract_files(self) -> List[tuple]:
        """Discover and extract all files from source"""
        files_to_process = []
        
        try:
            self.logger.logger.info(f"Discovering files in: {self.source_path}")
            
            # Extract files using the file extractor
            for original_path, extracted_path in self.file_extractor.extract_all_files(self.source_path):
                # Only process supported file types
                if (self.config.is_image_file(extracted_path) or 
                    self.config.is_pdf_file(extracted_path) or
                    not self.config.is_archive_file(extracted_path)):
                    
                    files_to_process.append((extracted_path, original_path))
            
            self.logger.logger.info(f"Found {len(files_to_process)} files to process")
            
            return files_to_process
            
        except Exception as e:
            error_msg = f"Error discovering files: {str(e)}"
            self.logger.log_error("File Discovery", error_msg)
            self.processing_results['errors'].append(error_msg)
            return []
    
    def _process_single_file(self, file_path: Path, original_path: Path) -> Optional[Dict[str, Any]]:
        """Process a single file through the complete pipeline"""
        try:
            # Get file information
            file_info = self.file_extractor.get_file_info(file_path)
            
            # Start logging for this file with source/destination paths
            source_path = str(original_path)
            destination_path = None  # Will be set when file is organized
            operation_id = self.logger.log_file_processing_start(
                source_path, file_info, destination_path
            )
            
            result = {
                'operation_id': operation_id,
                'file_path': file_path,
                'original_path': original_path,
                'file_info': file_info,
                'patient_data': {},
                'ocr_result': {},
                'parsing_result': {},
                'mapping_result': {},
                'deep_scan_result': {},
                'data_source': 'unknown',  # Track where data came from
                'success': False,
                'errors': [],
                'warnings': []
            }

            # LEVEL 1: Try mapping lookup first (if available)
            if self.mapping_processor:
                patient_data = self._try_mapping_lookup(file_path)
                if patient_data:
                    result['mapping_result'] = patient_data
                    result['patient_data'] = patient_data
                    result['data_source'] = 'mapping_file'
                    self.processing_results['mapped_files'] += 1
                    self.logger.logger.info(f"Patient data found in mapping file for {file_path.name}")

            # LEVEL 2: Parse filename for patient data (if not mapped)
            if not result['patient_data']:
                filename_parsing_result = self.patient_parser.parse_filename(file_path.name)
                self.logger.log_patient_parsing(file_path, filename_parsing_result)
                
                if self._has_sufficient_patient_data(filename_parsing_result):
                    result['patient_data'] = filename_parsing_result
                    result['parsing_result'] = filename_parsing_result
                    result['data_source'] = 'filename_parsing'
                    self.logger.logger.info(f"Patient data extracted from filename: {file_path.name}")

            # LEVEL 3: Basic OCR processing (if not mapped and filename insufficient)
            ocr_result = {}
            if not result['patient_data'] and (self.config.is_image_file(file_path) or self.config.is_pdf_file(file_path)):
                # Basic OCR with limited page processing
                ocr_result = self.ocr_processor.extract_text_from_file(file_path, max_pages=3)
                self.logger.log_ocr_operation(file_path, ocr_result)
                result['ocr_result'] = ocr_result
                
                # Parse OCR text for patient data
                if ocr_result.get('success'):
                    ocr_parsing_result = self.patient_parser.parse_ocr_text(ocr_result)
                    self.logger.log_patient_parsing(file_path, ocr_parsing_result)
                    
                    if self._has_sufficient_patient_data(ocr_parsing_result):
                        result['patient_data'] = ocr_parsing_result
                        result['parsing_result'] = ocr_parsing_result
                        result['data_source'] = 'basic_ocr'
                        self.logger.logger.info(f"Patient data found via basic OCR: {file_path.name}")

            # LEVEL 4: Deep scan for PDFs (last resort - up to 20 pages)
            if not result['patient_data'] and self.config.is_pdf_file(file_path):
                self.logger.logger.info(f"Starting deep scan for patient data in {file_path.name} (up to 20 pages)")
                deep_scan_result = self._perform_deep_pdf_scan(file_path)
                result['deep_scan_result'] = deep_scan_result
                
                if deep_scan_result.get('patient_data') and self._has_sufficient_patient_data(deep_scan_result['patient_data']):
                    result['patient_data'] = deep_scan_result['patient_data']
                    result['data_source'] = 'deep_pdf_scan'
                    self.logger.logger.info(f"Patient data found via deep PDF scan: {file_path.name} (pages processed: {deep_scan_result.get('pages_processed', 0)})")

            # LEVEL 5: Combine any partial results if still no complete data
            if not result['patient_data']:
                # Combine filename and OCR results for best guess
                filename_result = self.patient_parser.parse_filename(file_path.name)
                combined_result = self.patient_parser.combine_parsing_results(
                    filename_result, ocr_result.get('parsing_result', {})
                )
                
                if combined_result:
                    result['patient_data'] = combined_result
                    result['parsing_result'] = combined_result
                    result['data_source'] = 'combined_partial'
                    self.logger.logger.warning(f"Using combined partial data for {file_path.name}")
                
                # Mark as unmapped if still insufficient
                if not self._has_sufficient_patient_data(combined_result):
                    self.processing_results['unmapped_files'] += 1
                    result['data_source'] = 'unmapped'
                    self.logger.logger.warning(f"Insufficient patient data found for {file_path.name} - moving to unmapped folder")

            result['success'] = True
            self.processing_results['successful_extractions'] += 1
            
            # Log completion with data source
            self.logger.log_file_processing_end(operation_id, result)
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing file {file_path}: {str(e)}"
            self.logger.log_error("File Processing", error_msg, {'file_path': str(file_path)})
            self.processing_results['failed_extractions'] += 1
            self.processing_results['errors'].append(error_msg)
            
            if 'operation_id' in locals():
                self.logger.log_file_processing_end(operation_id, {'success': False, 'error': error_msg})
            
            return None
    
    def _try_mapping_lookup(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Try to find patient data using mapping file"""
        try:
            filename = file_path.name
            
            # Try lookup by filename
            result = self.mapping_processor.get_patient_by_filename(filename)
            if result:
                return result
            
            # Try lookup by ID extracted from filename
            import re
            id_patterns = self.config.ID_PATTERNS
            for pattern in id_patterns:
                matches = re.findall(pattern, filename)
                for match in matches:
                    result = self.mapping_processor.get_patient_by_id(match)
                    if result:
                        return result
            
            return None
            
        except Exception as e:
            self.logger.log_warning("Mapping Lookup", f"Error in mapping lookup: {str(e)}")
            return None
    
    def _has_sufficient_patient_data(self, patient_data: Dict[str, str]) -> bool:
        """Check if patient data is sufficient for organization"""
        if not patient_data:
            return False
        
        # Need at least firstname and lastname, or a patient ID
        has_names = (patient_data.get('firstname', '').strip() and 
                    patient_data.get('lastname', '').strip())
        has_id = patient_data.get('id', '').strip()
        
        return has_names or has_id
    
    def _detect_duplicates(self, processed_files: List[Dict[str, Any]]) -> Dict[str, List]:
        """Detect duplicates among processed files"""
        try:
            self.logger.logger.info("Starting duplicate detection")
            
            # Add files to duplicate detector
            for result in processed_files:
                if result.get('success'):
                    file_path = result['file_path']
                    patient_data = result['patient_data']
                    original_path = result['original_path']
                    
                    self.duplicate_detector.add_file(file_path, patient_data, original_path)
            
            # Detect duplicates
            duplicate_groups = self.duplicate_detector.detect_duplicates()
            self.logger.log_duplicate_detection(duplicate_groups)
            
            # Count duplicates
            exact_duplicates = len(duplicate_groups.get('exact_duplicates', []))
            potential_duplicates = len(duplicate_groups.get('potential_duplicates', []))
            self.processing_results['duplicate_files'] = exact_duplicates + potential_duplicates
            
            return duplicate_groups
            
        except Exception as e:
            error_msg = f"Error in duplicate detection: {str(e)}"
            self.logger.log_error("Duplicate Detection", error_msg)
            self.processing_results['errors'].append(error_msg)
            return {}
    
    def _organize_files(self, processed_files: List[Dict[str, Any]], 
                       duplicate_groups: Dict[str, List]):
        """Organize files into patient folders"""
        try:
            self.logger.logger.info("Starting file organization")
            
            # Create sets of duplicate file paths for quick lookup
            duplicate_paths = set()
            for group_type, groups in duplicate_groups.items():
                if group_type in ['exact_duplicates', 'potential_duplicates']:
                    for group in groups:
                        for file_info in group[1:]:  # Skip first file in each group
                            duplicate_paths.add(str(file_info.path))
            
            # Organize each file
            for result in processed_files:
                if result.get('success'):
                    file_path = result['file_path']
                    patient_data = result['patient_data']
                    is_duplicate = str(file_path) in duplicate_paths
                    
                    organization_result = self.file_organizer.organize_file(
                        file_path, patient_data, is_duplicate, self.dry_run
                    )
                    
                    # Update the file processing log with destination path
                    if organization_result.get('success'):
                        dest_path = organization_result.get('destination_path')
                        operation_id = result.get('operation_id')
                        if operation_id and dest_path:
                            # Update the log entry with destination path
                            self.logger.log_file_processing_end(
                                operation_id, 
                                {'success': True, 'destination_path': str(dest_path)}
                            )
                    
                    self.logger.log_file_organization(file_path, organization_result)
                    
                    if organization_result.get('success'):
                        self.processing_results['organized_files'] += 1
            
            # Handle patient file series (like 0000_1, 0000_2, 0000_3)
            self._handle_patient_series(processed_files)
            
        except Exception as e:
            error_msg = f"Error in file organization: {str(e)}"
            self.logger.log_error("File Organization", error_msg)
            self.processing_results['errors'].append(error_msg)
    
    def _handle_patient_series(self, processed_files: List[Dict[str, Any]]):
        """Handle patient file series"""
        try:
            # Group files by patient
            patient_groups = {}
            
            for result in processed_files:
                if result.get('success'):
                    patient_data = result['patient_data']
                    if self._has_sufficient_patient_data(patient_data):
                        patient_key = self._create_patient_key(patient_data)
                        if patient_key not in patient_groups:
                            patient_groups[patient_key] = []
                        patient_groups[patient_key].append(result)
            
            # Process series for each patient
            for patient_key, patient_files in patient_groups.items():
                if len(patient_files) > 1:
                    # Check if it's a numbered series
                    series_files = [(r['file_path'], r['patient_data']) for r in patient_files]
                    
                    if self._is_file_series(series_files):
                        self.logger.logger.info(f"Processing file series for patient: {patient_key}")
                        self.file_organizer.handle_patient_file_series(series_files, self.dry_run)
            
        except Exception as e:
            error_msg = f"Error handling patient series: {str(e)}"
            self.logger.log_error("Patient Series", error_msg)
            self.processing_results['errors'].append(error_msg)
    
    def _create_patient_key(self, patient_data: Dict[str, str]) -> str:
        """Create patient key for grouping"""
        firstname = patient_data.get('firstname', '').strip()
        lastname = patient_data.get('lastname', '').strip()
        dob = patient_data.get('dob', '').strip()
        patient_id = patient_data.get('id', '').strip()
        
        if patient_id:
            return f"id_{patient_id}"
        elif firstname and lastname:
            key = f"{lastname}_{firstname}"
            if dob:
                key += f"_{dob}"
            return key
        
        return "unknown"
    
    def _is_file_series(self, files: List[tuple]) -> bool:
        """Check if files form a numbered series"""
        if len(files) < 2:
            return False
        
        import re
        
        # Check for numbered patterns in filenames
        numbered_files = 0
        for file_path, _ in files:
            filename = file_path.stem
            if re.search(r'_\d+$|_\(\d+\)$|-\d+$', filename):
                numbered_files += 1
        
        # If more than half the files are numbered, consider it a series
        return numbered_files >= len(files) // 2
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate final processing report"""
        try:
            # Get component statistics
            extractor_stats = self.file_extractor.get_extraction_statistics()
            ocr_stats = self.ocr_processor.get_processing_statistics()
            duplicate_report = self.duplicate_detector.get_duplicate_report()
            organizer_stats = self.file_organizer.get_organization_statistics()
            
            # Combine all results
            final_report = {
                'session_info': self.logger.get_current_stats(),
                'processing_summary': self.processing_results,
                'component_statistics': {
                    'file_extraction': extractor_stats,
                    'ocr_processing': ocr_stats,
                    'duplicate_detection': duplicate_report,
                    'file_organization': organizer_stats
                },
                'dry_run': self.dry_run,
                'source_path': str(self.source_path),
                'destination_path': str(self.destination_path),
                'mapping_file': str(self.mapping_file) if self.mapping_file else None
            }
            
            self.logger.logger.info("Final report generated successfully")
            return final_report
            
        except Exception as e:
            error_msg = f"Error generating final report: {str(e)}"
            self.logger.log_error("Report Generation", error_msg)
            self.processing_results['errors'].append(error_msg)
            return {'error': error_msg}
    
    def _generate_patient_summaries(self, processed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive patient summaries for logging"""
        patient_summaries = {}
        
        for result in processed_files:
            if not result.get('success'):
                continue
                
            patient_data = result.get('patient_data', {})
            if not self._has_sufficient_patient_data(patient_data):
                continue
            
            patient_key = self._create_patient_key(patient_data)
            
            if patient_key not in patient_summaries:
                patient_summaries[patient_key] = {
                    'patient_info': patient_data,
                    'files': [],
                    'total_files': 0,
                    'total_size_mb': 0,
                    'processing_methods': set(),
                    'success_count': 0,
                    'error_count': 0
                }
            
            summary = patient_summaries[patient_key]
            summary['files'].append({
                'file_path': str(result['file_path']),
                'original_path': str(result['original_path']),
                'file_size_mb': result['file_info'].get('size', 0) / (1024 * 1024),
                'data_source': result.get('data_source', 'unknown'),
                'success': result['success']
            })
            
            summary['total_files'] += 1
            summary['total_size_mb'] += result['file_info'].get('size', 0) / (1024 * 1024)
            summary['processing_methods'].add(result.get('data_source', 'unknown'))
            
            if result['success']:
                summary['success_count'] += 1
            else:
                summary['error_count'] += 1
        
        # Convert sets to lists for JSON serialization
        for summary in patient_summaries.values():
            summary['processing_methods'] = list(summary['processing_methods'])
        
        return patient_summaries
    
    def _cleanup(self):
        """Clean up temporary files and resources"""
        try:
            # Clean up file extractor temporary files
            self.file_extractor.cleanup_temp_files()
            
            # Clear processor caches
            self.ocr_processor.clear_cache()
            self.duplicate_detector.clear_cache()
            self.file_organizer.clear_statistics()
            
            self.logger.logger.info("Cleanup completed successfully")
            
        except Exception as e:
            error_msg = f"Error during cleanup: {str(e)}"
            self.logger.log_error("Cleanup", error_msg)

    def _perform_deep_pdf_scan(self, file_path: Path) -> Dict[str, Any]:
        """
        Perform deep scan of PDF file up to 20 pages to find patient data
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with deep scan results
        """
        result = {
            'patient_data': {},
            'pages_processed': 0,
            'total_pages': 0,
            'found_on_page': 0,
            'success': False,
            'method': 'deep_pdf_scan'
        }
        
        try:
            self.logger.logger.info(f"Starting deep PDF scan for {file_path.name}")
            
            # Extract text from up to 20 pages
            ocr_result = self.ocr_processor.extract_text_from_file(
                file_path, max_pages=20, deep_scan=True
            )
            
            if not ocr_result.get('success'):
                self.logger.logger.warning(f"OCR failed during deep scan: {file_path.name}")
                return result
            
            result['pages_processed'] = len(ocr_result.get('pages', []))
            result['total_pages'] = ocr_result.get('total_pages', 0)
            
            # Try to parse patient data from each page individually
            best_patient_data = {}
            best_confidence = 0
            found_page = 0
            
            for page_info in ocr_result.get('pages', []):
                if not page_info.get('text', '').strip():
                    continue
                
                # Create a mock OCR result for this page
                page_ocr_result = {
                    'text': page_info['text'],
                    'confidence': page_info.get('confidence', 0),
                    'success': True
                }
                
                # Parse this page for patient data
                page_patient_data = self.patient_parser.parse_ocr_text(page_ocr_result)
                
                if self._has_sufficient_patient_data(page_patient_data):
                    # Calculate completeness score
                    completeness = self._calculate_patient_data_completeness(page_patient_data)
                    
                    if completeness > best_confidence:
                        best_patient_data = page_patient_data
                        best_confidence = completeness
                        found_page = page_info.get('page', 0)
                        
                        # If we found complete data, no need to continue
                        if completeness >= 0.8:  # 80% complete
                            break
            
            if best_patient_data:
                result['patient_data'] = best_patient_data
                result['found_on_page'] = found_page
                result['success'] = True
                
                self.logger.logger.info(
                    f"Deep scan successful for {file_path.name}: "
                    f"Found patient data on page {found_page} "
                    f"(scanned {result['pages_processed']} pages)"
                )
            else:
                self.logger.logger.warning(
                    f"Deep scan completed for {file_path.name}: "
                    f"No patient data found in {result['pages_processed']} pages"
                )
            
        except Exception as e:
            error_msg = f"Error during deep PDF scan of {file_path}: {str(e)}"
            self.logger.log_error("Deep PDF Scan", error_msg)
            result['error'] = error_msg
        
        return result
    
    def _calculate_patient_data_completeness(self, patient_data: Dict[str, str]) -> float:
        """
        Calculate completeness score for patient data
        
        Args:
            patient_data: Patient data dictionary
            
        Returns:
            Completeness score between 0.0 and 1.0
        """
        if not patient_data:
            return 0.0
        
        required_fields = ['firstname', 'lastname']
        optional_fields = ['dob', 'id']
        
        score = 0.0
        total_possible = len(required_fields) + len(optional_fields)
        
        # Required fields are worth more
        for field in required_fields:
            if patient_data.get(field, '').strip():
                score += 0.6  # 60% of total for required fields
        
        # Optional fields add bonus points
        for field in optional_fields:
            if patient_data.get(field, '').strip():
                score += 0.2  # 20% each for optional fields
        
        return min(score / total_possible, 1.0)


def main():
    """Main entry point for the ETL processor"""
    parser = argparse.ArgumentParser(description='Medical ETL Processor')
    
    parser.add_argument('source', help='Source directory or file path')
    parser.add_argument('destination', help='Destination directory path')
    parser.add_argument('--mapping', '-m', help='Mapping file path (Excel/CSV)')
    parser.add_argument('--dry-run', '-d', action='store_true', 
                       help='Perform dry run (no actual file operations)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    try:
        # Validate paths
        source_path = Path(args.source)
        destination_path = Path(args.destination)
        mapping_file = Path(args.mapping) if args.mapping else None
        
        if not source_path.exists():
            print(f"Error: Source path does not exist: {source_path}")
            sys.exit(1)
        
        if mapping_file and not mapping_file.exists():
            print(f"Error: Mapping file does not exist: {mapping_file}")
            sys.exit(1)
        
        # Initialize and run ETL processor
        processor = MedicalETLProcessor(
            source_path=source_path,
            destination_path=destination_path,
            mapping_file=mapping_file,
            dry_run=args.dry_run
        )
        
        print(f"Starting Medical ETL Process...")
        print(f"Source: {source_path}")
        print(f"Destination: {destination_path}")
        print(f"Mapping File: {mapping_file or 'None'}")
        print(f"Mode: {'Dry Run' if args.dry_run else 'Real Run'}")
        print("-" * 50)
        
        # Run the ETL process
        results = processor.run()
        
        # Print summary
        print("\nETL Process Completed!")
        print("-" * 50)
        print(f"Files Found: {results['processing_summary']['total_files_found']}")
        print(f"Files Processed: {results['processing_summary']['total_files_processed']}")
        print(f"Successfully Extracted: {results['processing_summary']['successful_extractions']}")
        print(f"Failed Extractions: {results['processing_summary']['failed_extractions']}")
        print(f"Mapped Files: {results['processing_summary']['mapped_files']}")
        print(f"Unmapped Files: {results['processing_summary']['unmapped_files']}")
        print(f"Duplicate Files: {results['processing_summary']['duplicate_files']}")
        print(f"Organized Files: {results['processing_summary']['organized_files']}")
        print(f"Errors: {len(results['processing_summary']['errors'])}")
        print(f"Warnings: {len(results['processing_summary']['warnings'])}")
        
        if results['processing_summary']['errors']:
            print("\nErrors encountered:")
            for error in results['processing_summary']['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(results['processing_summary']['errors']) > 5:
                print(f"  ... and {len(results['processing_summary']['errors']) - 5} more")
        
        print(f"\nSession ID: {results['session_info']['session_id']}")
        print(f"Log File: {results['session_info']['log_file']}")
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()