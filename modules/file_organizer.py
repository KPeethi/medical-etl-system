"""
File Organizer for Medical ETL System
Organizes files into patient folders with normalized naming
"""

import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from config.config import Config

logger = logging.getLogger(__name__)


class FileOrganizer:
    """Organizes medical files into patient-specific folders"""
    
    def __init__(self, destination_root: Path):
        self.config = Config()
        self.destination_root = Path(destination_root)
        self.duplicates_folder = self.destination_root / self.config.DUPLICATE_FOLDER_NAME
        self.unmapped_folder = self.destination_root / self.config.UNMAPPED_FOLDER_NAME
        
        # Ensure base directories exist
        self._ensure_directories()
        
        # Track organized files
        self.organized_files = []
        self.skipped_files = []
        self.duplicate_files = []
        
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        try:
            self.destination_root.mkdir(parents=True, exist_ok=True)
            self.duplicates_folder.mkdir(parents=True, exist_ok=True)
            self.unmapped_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Destination directories created: {self.destination_root}")
        except Exception as e:
            logger.error(f"Error creating directories: {str(e)}")
            raise
    
    def organize_file(self, source_path: Path, patient_data: Dict[str, str], 
                     is_duplicate: bool = False, dry_run: bool = False) -> Dict[str, any]:
        """
        Organize a single file into appropriate patient folder
        
        Args:
            source_path: Source file path
            patient_data: Parsed patient information
            is_duplicate: Whether file is identified as duplicate
            dry_run: If True, only simulate the operation
            
        Returns:
            Dictionary with organization result
        """
        result = {
            'source_path': str(source_path),
            'destination_path': '',
            'action': '',
            'success': False,
            'error': None,
            'patient_folder': '',
            'new_filename': ''
        }
        
        try:
            if is_duplicate:
                destination_path = self._get_duplicate_path(source_path, patient_data)
                result['action'] = 'moved_to_duplicates'
            elif not self._has_sufficient_patient_data(patient_data):
                destination_path = self._get_unmapped_path(source_path)
                result['action'] = 'moved_to_unmapped'
            else:
                destination_path = self._get_patient_file_path(source_path, patient_data)
                result['action'] = 'organized_to_patient_folder'
            
            result['destination_path'] = str(destination_path)
            result['patient_folder'] = str(destination_path.parent)
            result['new_filename'] = destination_path.name
            
            if not dry_run:
                # Ensure destination directory exists
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Handle file name conflicts
                final_destination = self._resolve_filename_conflict(destination_path)
                
                # Copy file (don't move to preserve source)
                shutil.copy2(source_path, final_destination)
                result['destination_path'] = str(final_destination)
                result['new_filename'] = final_destination.name
                
                logger.debug(f"Organized file: {source_path} -> {final_destination}")
            
            result['success'] = True
            
            # Track the organized file
            if is_duplicate:
                self.duplicate_files.append(result)
            elif not self._has_sufficient_patient_data(patient_data):
                self.skipped_files.append(result)
            else:
                self.organized_files.append(result)
            
            return result
            
        except Exception as e:
            error_msg = f"Error organizing file {source_path}: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
            return result
    
    def _has_sufficient_patient_data(self, patient_data: Dict[str, str]) -> bool:
        """Check if patient data is sufficient for organization"""
        # Need at least lastname and firstname, or a valid ID
        has_name = (patient_data.get('lastname', '').strip() and 
                   patient_data.get('firstname', '').strip())
        has_id = patient_data.get('id', '').strip()
        
        return has_name or has_id
    
    def _get_patient_file_path(self, source_path: Path, patient_data: Dict[str, str]) -> Path:
        """Generate patient file path with normalized naming"""
        # Create patient folder name
        patient_folder_name = self._create_patient_folder_name(patient_data)
        patient_folder = self.destination_root / patient_folder_name
        
        # Create normalized filename
        new_filename = self._create_normalized_filename(source_path, patient_data)
        
        return patient_folder / new_filename
    
    def _create_patient_folder_name(self, patient_data: Dict[str, str]) -> str:
        """Create normalized patient folder name: lastname, firstname dob"""
        lastname = patient_data.get('lastname', '').strip()
        firstname = patient_data.get('firstname', '').strip()
        dob = patient_data.get('dob', '').strip()
        patient_id = patient_data.get('id', '').strip()
        
        # Normalize names
        lastname = self._normalize_name_for_folder(lastname)
        firstname = self._normalize_name_for_folder(firstname)
        
        if lastname and firstname:
            folder_name = f"{lastname}, {firstname}"
            if dob:
                folder_name += f" {dob}"
        elif patient_id:
            # Fallback to ID if names not available
            folder_name = f"Patient_{patient_id}"
            if dob:
                folder_name += f" {dob}"
        else:
            # Last resort - use current timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = f"Unknown_Patient_{timestamp}"
        
        # Clean folder name for filesystem
        folder_name = self._clean_folder_name(folder_name)
        
        return folder_name
    
    def _normalize_name_for_folder(self, name: str) -> str:
        """Normalize name for use in folder names"""
        if not name:
            return ""
        
        # Remove extra whitespace and normalize case
        normalized = ' '.join(name.strip().split()).title()
        
        # Handle special cases
        normalized = normalized.replace("'", "")
        normalized = normalized.replace('"', "")
        
        # Remove any middle names/initials for folder naming
        name_parts = normalized.split()
        if len(name_parts) > 1:
            # Take first word only (remove middle names)
            normalized = name_parts[0]
        
        return normalized
    
    def _clean_folder_name(self, folder_name: str) -> str:
        """Clean folder name for filesystem compatibility"""
        # Replace invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in invalid_chars:
            folder_name = folder_name.replace(char, '_')
        
        # Replace multiple spaces/underscores with single underscore
        folder_name = ' '.join(folder_name.split())
        
        # Limit length
        if len(folder_name) > 100:
            folder_name = folder_name[:100].strip()
        
        return folder_name
    
    def _create_normalized_filename(self, source_path: Path, patient_data: Dict[str, str]) -> str:
        """Create normalized filename without patient name repetition"""
        base_name = source_path.stem
        extension = source_path.suffix
        
        # Extract year/date information from original filename
        year_info = self._extract_year_from_filename(base_name)
        
        # Check for chart/document type and module information
        doc_type = self._extract_document_type(base_name)
        module_info = self._extract_module_info(base_name)
        
        # Start with base document name (remove patient info from filename)
        cleaned_base = self._remove_patient_info_from_filename(base_name, patient_data)
        
        # Build filename components - ALWAYS include year if found to avoid conflicts
        filename_parts = []
        
        # Add year FIRST if found (this is crucial for same-size files from different years)
        if year_info:
            filename_parts.append(year_info)
        
        # Add document type/module
        if module_info:
            filename_parts.append(module_info)
        elif doc_type:
            filename_parts.append(doc_type)
        elif cleaned_base:
            filename_parts.append(cleaned_base)
        else:
            # Fallback to original name if nothing else found
            filename_parts.append(base_name)
        
        # Combine parts
        if filename_parts:
            new_name = "_".join(filename_parts)
        else:
            new_name = base_name
        
        # Clean and format
        new_name = self._clean_filename(new_name)
        
        return f"{new_name}{extension}"
    
    def _extract_year_from_filename(self, filename: str) -> str:
        """Extract year information from filename"""
        import re
        
        # Look for 4-digit years
        year_pattern = r'\b(20\d{2}|19\d{2})\b'
        matches = re.findall(year_pattern, filename)
        
        if matches:
            return matches[0]
        
        return ""
    
    def _extract_document_type(self, filename: str) -> str:
        """Extract document type from filename"""
        filename_lower = filename.lower()
        
        # Common document types
        doc_types = [
            'chart', 'report', 'lab', 'xray', 'scan', 'image', 
            'document', 'record', 'test', 'result', 'summary'
        ]
        
        for doc_type in doc_types:
            if doc_type in filename_lower:
                return doc_type
        
        return ""
    
    def _extract_module_info(self, filename: str) -> str:
        """Extract module/chart information from filename"""
        import re
        
        filename_lower = filename.lower()
        
        # Look for chart/module patterns like chart1, chart2, module1, etc.
        module_patterns = [
            r'(chart\d+)',
            r'(module\d+)',
            r'(part\d+)',
            r'(section\d+)',
            r'(page\d+)',
            r'(doc\d+)',
            r'(file\d+)'
        ]
        
        for pattern in module_patterns:
            matches = re.findall(pattern, filename_lower)
            if matches:
                return matches[0]
        
        return ""
    
    def _remove_patient_info_from_filename(self, filename: str, patient_data: Dict[str, str]) -> str:
        """Remove patient information from filename to get clean base name"""
        import re
        
        cleaned = filename.lower()
        
        # Remove patient names if present
        firstname = patient_data.get('firstname', '').strip().lower()
        lastname = patient_data.get('lastname', '').strip().lower()
        
        if firstname:
            cleaned = re.sub(rf'\b{re.escape(firstname)}\b', '', cleaned)
        if lastname:
            cleaned = re.sub(rf'\b{re.escape(lastname)}\b', '', cleaned)
        
        # Remove common separators and clean up
        cleaned = re.sub(r'[_\-\s,]+', '_', cleaned)
        cleaned = cleaned.strip('_')
        
        # Remove date patterns
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'
        ]
        
        for pattern in date_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # Final cleanup
        cleaned = re.sub(r'[_\-\s]+', '_', cleaned)
        cleaned = cleaned.strip('_')
        
        return cleaned if cleaned else filename
    
    def _clean_filename(self, filename: str) -> str:
        """Clean filename for filesystem compatibility"""
        # Replace invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Replace multiple spaces/underscores with single space
        filename = ' '.join(filename.split())
        filename = filename.replace('_', ' ')
        filename = ' '.join(filename.split())
        
        # Limit length
        if len(filename) > 150:
            filename = filename[:150].strip()
        
        return filename
    
    def _resolve_filename_conflict(self, destination_path: Path) -> Path:
        """Resolve filename conflicts by adding sequence numbers"""
        if not destination_path.exists():
            return destination_path
        
        base_name = destination_path.stem
        extension = destination_path.suffix
        parent_dir = destination_path.parent
        
        counter = 1
        while True:
            new_name = f"{base_name}_{counter:03d}{extension}"
            new_path = parent_dir / new_name
            
            if not new_path.exists():
                return new_path
            
            counter += 1
            
            # Prevent infinite loop
            if counter > 999:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_name = f"{base_name}_{timestamp}{extension}"
                return parent_dir / new_name
    
    def _get_duplicate_path(self, source_path: Path, patient_data: Dict[str, str]) -> Path:
        """Get path for duplicate files"""
        # Create subfolder based on patient if available
        if self._has_sufficient_patient_data(patient_data):
            patient_folder = self._create_patient_folder_name(patient_data)
            duplicate_subfolder = self.duplicates_folder / patient_folder
        else:
            duplicate_subfolder = self.duplicates_folder / "unidentified"
        
        # Keep original filename for duplicates
        return duplicate_subfolder / source_path.name
    
    def _get_unmapped_path(self, source_path: Path) -> Path:
        """Get path for unmapped files"""
        # Group unmapped files by extension
        extension = source_path.suffix.lower()
        extension_folder = extension[1:] if extension else "no_extension"
        unmapped_subfolder = self.unmapped_folder / extension_folder
        
        return unmapped_subfolder / source_path.name
    
    def handle_patient_file_series(self, files: List[Tuple[Path, Dict[str, str]]], 
                                 dry_run: bool = False) -> List[Dict[str, any]]:
        """
        Handle multiple files for the same patient (e.g., 0000_1, 0000_2, 0000_3)
        
        Args:
            files: List of (file_path, patient_data) tuples
            dry_run: If True, only simulate the operation
            
        Returns:
            List of organization results
        """
        results = []
        
        if not files:
            return results
        
        try:
            # Group files by patient
            patient_groups = {}
            for file_path, patient_data in files:
                patient_key = self._create_patient_folder_name(patient_data)
                if patient_key not in patient_groups:
                    patient_groups[patient_key] = []
                patient_groups[patient_key].append((file_path, patient_data))
            
            # Process each patient group
            for patient_key, patient_files in patient_groups.items():
                # Sort files by name to maintain order
                patient_files.sort(key=lambda x: x[0].name)
                
                for i, (file_path, patient_data) in enumerate(patient_files, 1):
                    # Modify filename to include sequence for series
                    if len(patient_files) > 1:
                        # Add series information to patient data
                        modified_patient_data = patient_data.copy()
                        original_filename = file_path.stem
                        
                        # Check if it's a numbered series
                        if self._is_numbered_series(original_filename):
                            series_info = f"part_{i:02d}"
                        else:
                            series_info = f"{original_filename}"
                        
                        modified_patient_data['series_info'] = series_info
                        
                        result = self._organize_series_file(file_path, modified_patient_data, dry_run)
                    else:
                        result = self.organize_file(file_path, patient_data, dry_run=dry_run)
                    
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error handling patient file series: {str(e)}")
            return results
    
    def _is_numbered_series(self, filename: str) -> bool:
        """Check if filename is part of a numbered series"""
        import re
        
        # Look for patterns like _1, _2, _3 or (1), (2), (3)
        series_patterns = [
            r'_\d+$',  # ends with _1, _2, etc.
            r'\(\d+\)$',  # ends with (1), (2), etc.
            r'-\d+$',  # ends with -1, -2, etc.
        ]
        
        for pattern in series_patterns:
            if re.search(pattern, filename):
                return True
        
        return False
    
    def _organize_series_file(self, source_path: Path, patient_data: Dict[str, str], 
                            dry_run: bool = False) -> Dict[str, any]:
        """Organize a file that's part of a series"""
        result = {
            'source_path': str(source_path),
            'destination_path': '',
            'action': 'organized_series_file',
            'success': False,
            'error': None,
            'patient_folder': '',
            'new_filename': ''
        }
        
        try:
            # Create patient folder
            patient_folder_name = self._create_patient_folder_name(patient_data)
            patient_folder = self.destination_root / patient_folder_name
            
            # Create filename without patient name repetition
            base_name = source_path.stem
            extension = source_path.suffix
            series_info = patient_data.get('series_info', '')
            
            # Extract year and document type
            year_info = self._extract_year_from_filename(base_name)
            doc_type = self._extract_document_type(base_name)
            module_info = self._extract_module_info(base_name)
            
            # Build filename parts
            filename_parts = []
            
            if year_info:
                filename_parts.append(year_info)
            
            if doc_type:
                filename_parts.append(doc_type)
            elif module_info:
                filename_parts.append(module_info)
            elif series_info:
                filename_parts.append(series_info)
            else:
                # Clean base name
                cleaned_base = self._remove_patient_info_from_filename(base_name, patient_data)
                if cleaned_base:
                    filename_parts.append(cleaned_base)
                else:
                    filename_parts.append(base_name)
            
            # Create final filename
            if filename_parts:
                new_filename = "_".join(filename_parts) + extension
            else:
                new_filename = f"{base_name}{extension}"
            
            new_filename = self._clean_filename(new_filename)
            destination_path = patient_folder / new_filename
            
            result['destination_path'] = str(destination_path)
            result['patient_folder'] = str(patient_folder)
            result['new_filename'] = new_filename
            
            if not dry_run:
                # Ensure directory exists
                patient_folder.mkdir(parents=True, exist_ok=True)
                
                # Handle conflicts
                final_destination = self._resolve_filename_conflict(destination_path)
                
                # Copy file
                shutil.copy2(source_path, final_destination)
                result['destination_path'] = str(final_destination)
                result['new_filename'] = final_destination.name
            
            result['success'] = True
            self.organized_files.append(result)
            
            return result
            
        except Exception as e:
            error_msg = f"Error organizing series file {source_path}: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
            return result
    
    def get_organization_statistics(self) -> Dict[str, any]:
        """Get statistics about file organization"""
        return {
            'total_organized': len(self.organized_files),
            'total_duplicates': len(self.duplicate_files),
            'total_unmapped': len(self.skipped_files),
            'total_processed': len(self.organized_files) + len(self.duplicate_files) + len(self.skipped_files),
            'destination_root': str(self.destination_root),
            'duplicates_folder': str(self.duplicates_folder),
            'unmapped_folder': str(self.unmapped_folder)
        }
    
    def generate_organization_report(self) -> Dict[str, any]:
        """Generate detailed organization report"""
        stats = self.get_organization_statistics()
        
        report = {
            'summary': stats,
            'organized_files': self.organized_files,
            'duplicate_files': self.duplicate_files,
            'unmapped_files': self.skipped_files,
            'patient_folders_created': []
        }
        
        # Get list of patient folders created
        if self.destination_root.exists():
            patient_folders = [
                str(folder) for folder in self.destination_root.iterdir()
                if folder.is_dir() and folder.name not in [
                    self.config.DUPLICATE_FOLDER_NAME,
                    self.config.UNMAPPED_FOLDER_NAME
                ]
            ]
            report['patient_folders_created'] = patient_folders
        
        return report
    
    def clear_statistics(self):
        """Clear organization statistics"""
        self.organized_files.clear()
        self.duplicate_files.clear()
        self.skipped_files.clear()
        logger.debug("File organizer statistics cleared")