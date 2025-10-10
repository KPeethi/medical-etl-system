"""
Data Mapping Processor for Medical ETL System
Handles Excel/CSV mapping files with various field synonyms
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from config.config import Config

logger = logging.getLogger(__name__)


class MappingProcessor:
    """Processes mapping files to extract patient data"""
    
    def __init__(self):
        self.config = Config()
        self.mapping_data = None
        self.field_mappings = {}
        
    def load_mapping_file(self, mapping_file_path: Path) -> bool:
        """
        Load mapping file (Excel or CSV) and identify field types
        
        Args:
            mapping_file_path: Path to the mapping file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Loading mapping file: {mapping_file_path}")
            
            if not mapping_file_path.exists():
                logger.error(f"Mapping file not found: {mapping_file_path}")
                return False
            
            # Read the file based on extension
            if mapping_file_path.suffix.lower() in ['.xlsx', '.xls']:
                self.mapping_data = pd.read_excel(mapping_file_path)
            elif mapping_file_path.suffix.lower() in ['.csv', '.tsv']:
                separator = '\t' if mapping_file_path.suffix.lower() == '.tsv' else ','
                self.mapping_data = pd.read_csv(mapping_file_path, sep=separator)
            else:
                logger.error(f"Unsupported mapping file format: {mapping_file_path.suffix}")
                return False
            
            # Identify field mappings
            self._identify_field_mappings()
            
            logger.info(f"Successfully loaded mapping file with {len(self.mapping_data)} records")
            logger.info(f"Identified field mappings: {self.field_mappings}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading mapping file {mapping_file_path}: {str(e)}")
            return False
    
    def _identify_field_mappings(self):
        """Identify which columns correspond to which field types"""
        self.field_mappings = {}
        
        for column in self.mapping_data.columns:
            field_type = self.config.get_field_type(column)
            if field_type != 'unknown':
                self.field_mappings[field_type] = column
                logger.debug(f"Mapped column '{column}' to field type '{field_type}'")
    
    def get_patient_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Get patient information by ID
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Dict with patient information or None if not found
        """
        if self.mapping_data is None or 'id' not in self.field_mappings:
            return None
        
        try:
            # Convert patient_id to string for comparison
            patient_id_str = str(patient_id).strip()
            
            # Search for exact match first
            id_column = self.field_mappings['id']
            mask = self.mapping_data[id_column].astype(str).str.strip() == patient_id_str
            matches = self.mapping_data[mask]
            
            if len(matches) > 0:
                patient_data = matches.iloc[0].to_dict()
                return self._normalize_patient_data(patient_data)
            
            # If no exact match, try partial matches
            mask = self.mapping_data[id_column].astype(str).str.contains(patient_id_str, na=False, case=False)
            matches = self.mapping_data[mask]
            
            if len(matches) > 0:
                logger.warning(f"Found partial match for ID {patient_id}")
                patient_data = matches.iloc[0].to_dict()
                return self._normalize_patient_data(patient_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching for patient ID {patient_id}: {str(e)}")
            return None
    
    def get_patient_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get patient information by filename
        
        Args:
            filename: Filename to search for
            
        Returns:
            Dict with patient information or None if not found
        """
        if self.mapping_data is None or 'filename' not in self.field_mappings:
            return None
        
        try:
            filename_clean = Path(filename).stem.lower()
            filename_column = self.field_mappings['filename']
            
            # Search for exact filename match
            mask = self.mapping_data[filename_column].astype(str).str.lower().str.contains(filename_clean, na=False)
            matches = self.mapping_data[mask]
            
            if len(matches) > 0:
                patient_data = matches.iloc[0].to_dict()
                return self._normalize_patient_data(patient_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching for filename {filename}: {str(e)}")
            return None
    
    def get_patient_by_name(self, first_name: str, last_name: str) -> Optional[Dict[str, Any]]:
        """
        Get patient information by name
        
        Args:
            first_name: Patient's first name
            last_name: Patient's last name
            
        Returns:
            Dict with patient information or None if not found
        """
        if self.mapping_data is None:
            return None
        
        try:
            matches = self.mapping_data.copy()
            
            # Filter by last name if mapping exists
            if 'lastname' in self.field_mappings:
                lastname_column = self.field_mappings['lastname']
                mask = matches[lastname_column].astype(str).str.lower().str.contains(last_name.lower(), na=False)
                matches = matches[mask]
            
            # Filter by first name if mapping exists
            if 'firstname' in self.field_mappings and len(matches) > 0:
                firstname_column = self.field_mappings['firstname']
                mask = matches[firstname_column].astype(str).str.lower().str.contains(first_name.lower(), na=False)
                matches = matches[mask]
            
            if len(matches) > 0:
                patient_data = matches.iloc[0].to_dict()
                return self._normalize_patient_data(patient_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching for patient name {first_name} {last_name}: {str(e)}")
            return None
    
    def _normalize_patient_data(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize patient data to standard format
        
        Args:
            patient_data: Raw patient data from mapping file
            
        Returns:
            Normalized patient data dictionary
        """
        normalized = {
            'id': '',
            'firstname': '',
            'lastname': '',
            'dob': '',
            'filename': '',
            'raw_data': patient_data
        }
        
        # Extract data based on field mappings
        for field_type, column_name in self.field_mappings.items():
            if column_name in patient_data and pd.notna(patient_data[column_name]):
                value = str(patient_data[column_name]).strip()
                
                if field_type == 'dob':
                    # Normalize date format
                    normalized_date = self._normalize_date(value)
                    normalized[field_type] = normalized_date if normalized_date else value
                else:
                    normalized[field_type] = value
        
        return normalized
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """
        Normalize date to MM-DD-YYYY format
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Normalized date string or None if parsing fails
        """
        import datetime
        
        for date_format in self.config.INPUT_DATE_FORMATS:
            try:
                parsed_date = datetime.datetime.strptime(date_str, date_format)
                return parsed_date.strftime(self.config.OUTPUT_DATE_FORMAT)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def search_all_patients(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for patients across all fields
        
        Args:
            search_term: Term to search for
            
        Returns:
            List of matching patient records
        """
        if self.mapping_data is None:
            return []
        
        matches = []
        search_term_lower = search_term.lower()
        
        try:
            for _, row in self.mapping_data.iterrows():
                row_dict = row.to_dict()
                
                # Search across all mapped fields
                for field_type, column_name in self.field_mappings.items():
                    if column_name in row_dict and pd.notna(row_dict[column_name]):
                        value = str(row_dict[column_name]).lower()
                        if search_term_lower in value:
                            normalized_data = self._normalize_patient_data(row_dict)
                            if normalized_data not in matches:
                                matches.append(normalized_data)
                            break
            
            return matches
            
        except Exception as e:
            logger.error(f"Error searching for term {search_term}: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the mapping data
        
        Returns:
            Dictionary with mapping statistics
        """
        if self.mapping_data is None:
            return {}
        
        stats = {
            'total_records': len(self.mapping_data),
            'identified_fields': self.field_mappings,
            'columns': list(self.mapping_data.columns),
            'missing_data': {}
        }
        
        # Calculate missing data statistics
        for field_type, column_name in self.field_mappings.items():
            if column_name in self.mapping_data.columns:
                missing_count = self.mapping_data[column_name].isna().sum()
                stats['missing_data'][field_type] = {
                    'column': column_name,
                    'missing_count': int(missing_count),
                    'missing_percentage': round((missing_count / len(self.mapping_data)) * 100, 2)
                }
        
        return stats
    
    def validate_mapping_file(self) -> Tuple[bool, List[str]]:
        """
        Validate the mapping file structure
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        if self.mapping_data is None:
            return False, ["No mapping data loaded"]
        
        # Check if at least one identification field is present
        id_fields = ['id', 'filename']
        has_id_field = any(field in self.field_mappings for field in id_fields)
        
        if not has_id_field:
            issues.append("No identification field found (ID or filename)")
        
        # Check if name fields are present
        name_fields = ['firstname', 'lastname']
        missing_name_fields = [field for field in name_fields if field not in self.field_mappings]
        
        if missing_name_fields:
            issues.append(f"Missing name fields: {', '.join(missing_name_fields)}")
        
        # Check for empty data
        if len(self.mapping_data) == 0:
            issues.append("Mapping file is empty")
        
        # Check for duplicate IDs if ID field exists
        if 'id' in self.field_mappings:
            id_column = self.field_mappings['id']
            duplicate_count = self.mapping_data.duplicated(subset=[id_column]).sum()
            if duplicate_count > 0:
                issues.append(f"Found {duplicate_count} duplicate IDs")
        
        return len(issues) == 0, issues