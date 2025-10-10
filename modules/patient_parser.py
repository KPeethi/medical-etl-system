"""
Patient Data Parser for Medical ETL System
Extracts and normalizes patient information from filenames and OCR text
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from config.config import Config

logger = logging.getLogger(__name__)


class PatientParser:
    """Parses and normalizes patient information"""
    
    def __init__(self):
        self.config = Config()
        
    def parse_filename(self, filename: str) -> Dict[str, any]:
        """
        Parse patient information from filename
        
        Args:
            filename: Name of the file
            
        Returns:
            Dictionary with parsed patient data
        """
        result = {
            'firstname': '',
            'lastname': '',
            'dob': '',
            'id': '',
            'additional_info': [],
            'confidence': 0,
            'parsing_method': 'filename'
        }
        
        try:
            # Clean filename - remove extension and common prefixes/suffixes
            clean_name = self._clean_filename(filename)
            
            # Try different parsing strategies
            strategies = [
                self._parse_lastname_firstname_dob,
                self._parse_firstname_lastname_dob,
                self._parse_with_separators,
                self._parse_id_based,
                self._parse_partial_info
            ]
            
            best_result = result.copy()
            best_confidence = 0
            
            for strategy in strategies:
                try:
                    parsed = strategy(clean_name)
                    if parsed and parsed.get('confidence', 0) > best_confidence:
                        best_result = parsed
                        best_confidence = parsed.get('confidence', 0)
                except Exception as e:
                    logger.debug(f"Strategy failed for {filename}: {str(e)}")
                    continue
            
            # Normalize the best result
            if best_confidence > 0:
                best_result = self._normalize_patient_data(best_result)
            
            logger.debug(f"Parsed filename '{filename}' with confidence {best_confidence}")
            return best_result
            
        except Exception as e:
            logger.error(f"Error parsing filename {filename}: {str(e)}")
            return result
    
    def _clean_filename(self, filename: str) -> str:
        """Clean and prepare filename for parsing"""
        # Remove file extension
        clean_name = Path(filename).stem
        
        # Remove common prefixes and suffixes
        prefixes_to_remove = ['chart', 'document', 'doc', 'file', 'patient', 'record']
        suffixes_to_remove = ['chart', 'document', 'doc', 'file', 'copy', 'final']
        
        # Split by common delimiters
        parts = re.split(r'[_\-\s\.]+', clean_name.lower())
        
        # Filter out common words
        filtered_parts = []
        for part in parts:
            if part and part not in prefixes_to_remove and part not in suffixes_to_remove:
                if not (part.isdigit() and len(part) < 3):  # Keep longer numeric strings
                    filtered_parts.append(part)
        
        return ' '.join(filtered_parts)
    
    def _parse_lastname_firstname_dob(self, filename: str) -> Dict[str, any]:
        """Parse format: lastname, firstname dob"""
        patterns = [
            r'([a-zA-Z]+),?\s*([a-zA-Z]+)\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'([a-zA-Z]+),?\s*([a-zA-Z]+)\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                lastname, firstname, dob = match.groups()
                return {
                    'lastname': lastname.strip().title(),
                    'firstname': firstname.strip().title(),
                    'dob': self._normalize_date(dob),
                    'id': '',
                    'confidence': 90,
                    'parsing_method': 'lastname_firstname_dob'
                }
        
        return None
    
    def _parse_firstname_lastname_dob(self, filename: str) -> Dict[str, any]:
        """Parse format: firstname lastname dob"""
        patterns = [
            r'([a-zA-Z]+)\s+([a-zA-Z]+)\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'([a-zA-Z]+)\s+([a-zA-Z]+)\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                firstname, lastname, dob = match.groups()
                return {
                    'firstname': firstname.strip().title(),
                    'lastname': lastname.strip().title(),
                    'dob': self._normalize_date(dob),
                    'id': '',
                    'confidence': 85,
                    'parsing_method': 'firstname_lastname_dob'
                }
        
        return None
    
    def _parse_with_separators(self, filename: str) -> Dict[str, any]:
        """Parse using various separators"""
        # Split by common separators
        parts = re.split(r'[,\s_\-\.]+', filename)
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) < 2:
            return None
        
        firstname = ''
        lastname = ''
        dob = ''
        id_val = ''
        
        # Look for date patterns
        date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}'
        for part in parts:
            if re.match(date_pattern, part):
                dob = self._normalize_date(part)
                break
        
        # Look for ID patterns
        id_pattern = r'\d{4,}'
        for part in parts:
            if re.match(id_pattern, part) and part != dob.replace('-', '').replace('/', ''):
                id_val = part
                break
        
        # Identify name parts (non-date, non-id alphabetic strings)
        name_parts = []
        for part in parts:
            if (part.isalpha() and len(part) > 1 and 
                not re.match(date_pattern, part) and 
                part != id_val):
                name_parts.append(part.title())
        
        if len(name_parts) >= 2:
            # Assume first is firstname, last is lastname
            firstname = name_parts[0]
            lastname = name_parts[-1]
            confidence = 70 if dob else 50
            
            return {
                'firstname': firstname,
                'lastname': lastname,
                'dob': dob,
                'id': id_val,
                'confidence': confidence,
                'parsing_method': 'separator_based'
            }
        
        return None
    
    def _parse_id_based(self, filename: str) -> Dict[str, any]:
        """Parse ID-based filenames"""
        # Look for numeric IDs
        id_patterns = [
            r'(\d{4,})',  # 4+ digits
            r'([A-Za-z]\d+)',  # Letter + digits
            r'(\d+[A-Za-z]+)',  # Digits + letters
        ]
        
        for pattern in id_patterns:
            match = re.search(pattern, filename)
            if match:
                id_val = match.group(1)
                return {
                    'firstname': '',
                    'lastname': '',
                    'dob': '',
                    'id': id_val,
                    'confidence': 30,
                    'parsing_method': 'id_based'
                }
        
        return None
    
    def _parse_partial_info(self, filename: str) -> Dict[str, any]:
        """Parse partial information from filename"""
        # Extract any names and dates found
        name_pattern = r'\b([A-Za-z]{2,})\b'
        date_pattern = r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b'
        
        names = re.findall(name_pattern, filename)
        dates = re.findall(date_pattern, filename)
        
        if names or dates:
            result = {
                'firstname': '',
                'lastname': '',
                'dob': '',
                'id': '',
                'confidence': 20,
                'parsing_method': 'partial'
            }
            
            if names:
                # Filter out common words
                common_words = {'chart', 'document', 'file', 'patient', 'record', 'copy'}
                valid_names = [name for name in names if name.lower() not in common_words]
                
                if len(valid_names) >= 1:
                    result['firstname'] = valid_names[0].title()
                    if len(valid_names) >= 2:
                        result['lastname'] = valid_names[1].title()
                        result['confidence'] = 40
            
            if dates:
                result['dob'] = self._normalize_date(dates[0])
                result['confidence'] += 20
            
            return result
        
        return None
    
    def parse_ocr_text(self, ocr_data: Dict[str, any]) -> Dict[str, any]:
        """
        Parse patient information from OCR extracted text
        
        Args:
            ocr_data: OCR result dictionary
            
        Returns:
            Dictionary with parsed patient data
        """
        result = {
            'firstname': '',
            'lastname': '',
            'dob': '',
            'id': '',
            'additional_info': [],
            'confidence': 0,
            'parsing_method': 'ocr'
        }
        
        if not ocr_data.get('success') or not ocr_data.get('text'):
            return result
        
        try:
            text = ocr_data['text']
            
            # Extract structured data
            extracted = self._extract_structured_data(text)
            
            # Find best matches
            best_name = self._find_best_name_match(extracted.get('names', []))
            best_date = self._find_best_date_match(extracted.get('dates', []))
            best_id = self._find_best_id_match(extracted.get('ids', []))
            
            if best_name:
                result['lastname'], result['firstname'] = best_name
                result['confidence'] += 40
            
            if best_date:
                result['dob'] = best_date
                result['confidence'] += 30
            
            if best_id:
                result['id'] = best_id
                result['confidence'] += 20
            
            # Factor in OCR confidence
            ocr_confidence = ocr_data.get('confidence', 0)
            result['confidence'] = int(result['confidence'] * (ocr_confidence / 100))
            
            result = self._normalize_patient_data(result)
            
            logger.debug(f"Parsed OCR text with confidence {result['confidence']}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing OCR text: {str(e)}")
            return result
    
    def _extract_structured_data(self, text: str) -> Dict[str, List]:
        """Extract structured data from text"""
        extracted = {
            'names': [],
            'dates': [],
            'ids': []
        }
        
        # Extract name patterns
        name_patterns = [
            r'(?:patient|name):\s*([A-Za-z]+),?\s*([A-Za-z]+)',
            r'([A-Za-z]+),\s*([A-Za-z]+)',
            r'\b([A-Za-z]{2,})\s+([A-Za-z]{2,})\b'
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) == 2 and self._is_valid_name_pair(match):
                    extracted['names'].append(match)
        
        # Extract dates
        date_patterns = [
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b',
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2})\b',
            r'(?:dob|birth|born):\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            extracted['dates'].extend(matches)
        
        # Extract IDs
        id_patterns = [
            r'(?:id|patient|mrn|chart):\s*(\d+)',
            r'\b(\d{4,})\b'
        ]
        
        for pattern in id_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            extracted['ids'].extend(matches)
        
        return extracted
    
    def _is_valid_name_pair(self, name_pair: Tuple[str, str]) -> bool:
        """Check if name pair is valid"""
        firstname, lastname = name_pair
        
        # Basic validation
        if not firstname or not lastname:
            return False
        
        if len(firstname) < 2 or len(lastname) < 2:
            return False
        
        # Check for common OCR errors
        invalid_words = {'and', 'the', 'for', 'you', 'are', 'not', 'can', 'will'}
        if firstname.lower() in invalid_words or lastname.lower() in invalid_words:
            return False
        
        # Must be alphabetic
        if not firstname.isalpha() or not lastname.isalpha():
            return False
        
        return True
    
    def _find_best_name_match(self, names: List[Tuple[str, str]]) -> Optional[Tuple[str, str]]:
        """Find the best name match from extracted names"""
        if not names:
            return None
        
        # Score names based on various criteria
        scored_names = []
        for name_pair in names:
            score = self._score_name_pair(name_pair)
            scored_names.append((score, name_pair))
        
        # Return highest scoring name
        if scored_names:
            scored_names.sort(reverse=True)
            return scored_names[0][1]
        
        return None
    
    def _score_name_pair(self, name_pair: Tuple[str, str]) -> int:
        """Score a name pair for quality"""
        firstname, lastname = name_pair
        score = 0
        
        # Length bonus
        if 3 <= len(firstname) <= 15:
            score += 10
        if 3 <= len(lastname) <= 20:
            score += 10
        
        # Common name patterns
        if firstname[0].isupper() and firstname[1:].islower():
            score += 5
        if lastname[0].isupper() and lastname[1:].islower():
            score += 5
        
        # Penalty for very short or very long names
        if len(firstname) < 3 or len(firstname) > 15:
            score -= 5
        if len(lastname) < 3 or len(lastname) > 20:
            score -= 5
        
        return score
    
    def _find_best_date_match(self, dates: List[str]) -> Optional[str]:
        """Find the best date match from extracted dates"""
        if not dates:
            return None
        
        valid_dates = []
        for date_str in dates:
            normalized = self._normalize_date(date_str)
            if normalized and self._is_reasonable_birth_date(normalized):
                valid_dates.append(normalized)
        
        # Return first valid date (could be enhanced with better logic)
        return valid_dates[0] if valid_dates else None
    
    def _find_best_id_match(self, ids: List[str]) -> Optional[str]:
        """Find the best ID match from extracted IDs"""
        if not ids:
            return None
        
        # Filter and score IDs
        valid_ids = []
        for id_str in ids:
            if self._is_valid_patient_id(id_str):
                valid_ids.append(id_str)
        
        # Return first valid ID (could be enhanced)
        return valid_ids[0] if valid_ids else None
    
    def _is_valid_patient_id(self, id_str: str) -> bool:
        """Check if ID is a valid patient ID"""
        if not id_str or len(id_str) < 3:
            return False
        
        # Must contain at least some digits
        if not any(c.isdigit() for c in id_str):
            return False
        
        # Reasonable length
        if len(id_str) > 20:
            return False
        
        return True
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to MM-DD-YYYY format"""
        if not date_str:
            return ''
        
        try:
            # Try different date formats
            for date_format in self.config.INPUT_DATE_FORMATS:
                try:
                    parsed_date = datetime.strptime(date_str, date_format)
                    return parsed_date.strftime(self.config.OUTPUT_DATE_FORMAT)
                except ValueError:
                    continue
            
            # Handle MM/DD/YY format (assume 20xx for YY < 30, 19xx otherwise)
            if re.match(r'\d{1,2}[-/]\d{1,2}[-/]\d{2}$', date_str):
                parts = re.split(r'[-/]', date_str)
                if len(parts) == 3:
                    month, day, year = parts
                    year_int = int(year)
                    if year_int < 30:
                        year = f"20{year}"
                    else:
                        year = f"19{year}"
                    
                    full_date = f"{month}/{day}/{year}"
                    parsed_date = datetime.strptime(full_date, "%m/%d/%Y")
                    return parsed_date.strftime(self.config.OUTPUT_DATE_FORMAT)
            
        except Exception as e:
            logger.debug(f"Error normalizing date {date_str}: {str(e)}")
        
        return ''
    
    def _is_reasonable_birth_date(self, date_str: str) -> bool:
        """Check if date is a reasonable birth date"""
        try:
            date_obj = datetime.strptime(date_str, self.config.OUTPUT_DATE_FORMAT)
            current_year = datetime.now().year
            birth_year = date_obj.year
            
            # Reasonable age range: 0-120 years
            age = current_year - birth_year
            return 0 <= age <= 120
            
        except Exception:
            return False
    
    def _normalize_patient_data(self, data: Dict[str, any]) -> Dict[str, any]:
        """Normalize patient data format"""
        normalized = data.copy()
        
        # Normalize names
        if normalized.get('firstname'):
            normalized['firstname'] = self._normalize_name(normalized['firstname'])
        
        if normalized.get('lastname'):
            normalized['lastname'] = self._normalize_name(normalized['lastname'])
        
        # Ensure date is normalized
        if normalized.get('dob'):
            normalized['dob'] = self._normalize_date(normalized['dob'])
        
        return normalized
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a name string"""
        if not name:
            return ''
        
        # Remove extra whitespace and title case
        normalized = ' '.join(name.strip().split()).title()
        
        # Handle special cases (e.g., O'Connor, McDonald)
        normalized = re.sub(r"(\w)'(\w)", r"\1'\2", normalized)
        normalized = re.sub(r"\bMc([a-z])", r"Mc\1", normalized)
        normalized = re.sub(r"\bMac([a-z])", r"Mac\1", normalized)
        
        return normalized
    
    def combine_parsing_results(self, filename_result: Dict[str, any], 
                              ocr_result: Dict[str, any]) -> Dict[str, any]:
        """
        Combine results from filename and OCR parsing
        
        Args:
            filename_result: Result from filename parsing
            ocr_result: Result from OCR parsing
            
        Returns:
            Combined result with best information from both sources
        """
        combined = {
            'firstname': '',
            'lastname': '',
            'dob': '',
            'id': '',
            'additional_info': [],
            'confidence': 0,
            'parsing_method': 'combined',
            'sources': []
        }
        
        # Combine data from both sources, preferring higher confidence
        for field in ['firstname', 'lastname', 'dob', 'id']:
            filename_value = filename_result.get(field, '')
            ocr_value = ocr_result.get(field, '')
            filename_conf = filename_result.get('confidence', 0)
            ocr_conf = ocr_result.get('confidence', 0)
            
            if filename_value and ocr_value:
                # Both sources have data - choose higher confidence
                if filename_conf >= ocr_conf:
                    combined[field] = filename_value
                else:
                    combined[field] = ocr_value
            elif filename_value:
                combined[field] = filename_value
            elif ocr_value:
                combined[field] = ocr_value
        
        # Calculate combined confidence
        max_conf = max(filename_result.get('confidence', 0), 
                      ocr_result.get('confidence', 0))
        if filename_result.get('confidence', 0) > 0 and ocr_result.get('confidence', 0) > 0:
            # Bonus for having both sources
            combined['confidence'] = min(100, max_conf + 10)
        else:
            combined['confidence'] = max_conf
        
        # Track sources
        if filename_result.get('confidence', 0) > 0:
            combined['sources'].append('filename')
        if ocr_result.get('confidence', 0) > 0:
            combined['sources'].append('ocr')
        
        return combined