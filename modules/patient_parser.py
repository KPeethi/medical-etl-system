"""
Patient Parser for Medical ETL System.
Handles parsing patient information from filenames and OCR text.
"""

import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from medical_etl_system.config.config import Config

logger = logging.getLogger(__name__)

class PatientParser:
    """Parses patient information from various sources"""

    def __init__(self):
        self.config = Config()

    def parse_filename(self, filename: str) -> Dict[str, Any]:
        """Parse patient information from filename"""
        try:
            filename = Path(filename).stem  # Remove extension

            # Extract potential ID from filename
            id_patterns = [
                r'.*?(\d{4}).*',  # Any 4-digit number
                r'.*?(P\d{3,}).*',  # P followed by 3+ digits
                r'.*?(PT\d+).*'  # PT followed by digits
            ]

            patient_info = {}

            # Look for patient ID in filename
            for pattern in id_patterns:
                match = re.match(pattern, filename)
                if match:
                    patient_info['id'] = match.group(1)
                    break

            # Clean filename for further parsing
            clean_name = re.sub(r'\(.*?\)', '', filename)  # Remove content in ()
            clean_name = re.sub(r'\[.*?\]', '', clean_name)  # Remove content in []
            clean_name = re.sub(r'\d+', ' ', clean_name)  # Remove numbers
            clean_name = re.sub(r'[^\w\s,.-]', ' ', clean_name)  # Remove special chars

            # Look for name patterns
            name_patterns = [
                r'([\w]+)[,\s_.]+(\w+)',  # lastname, firstname or lastname_firstname
                r'(\w+)\s*[,_.]\s*(\w+)',  # lastname,firstname or last.first
                r'(\w+),\s*(\w+)',  # strict lastname, firstname
            ]

            for pattern in name_patterns:
                match = re.search(pattern, clean_name)
                if match:
                    # Normalize and clean names
                    last = self._clean_name(match.group(1))
                    first = self._clean_name(match.group(2))
                    
                    if last and first and len(last) > 1 and len(first) > 1:
                        patient_info['lastname'] = last
                        patient_info['firstname'] = first
                        patient_info['LastName'] = last  # Also store original casing
                        patient_info['FirstName'] = first  # Also store original casing
                        break

            # Look for date of birth patterns
            dob_patterns = [
                r'(\d{1,2})[-/_](\d{1,2})[-/_](\d{2,4})',  # MM-DD-YYYY
                r'(\d{4})[-/_](\d{1,2})[-/_](\d{1,2})'  # YYYY-MM-DD
            ]

            # Extract and normalize date if found
            for pattern in dob_patterns:
                matches = re.findall(pattern, filename)
                if matches:
                    dob = None
                    for match in matches:
                        try:
                            if len(match[2]) == 4:  # YYYY
                                dob = datetime(int(match[2]), int(match[0]), int(match[1]))
                            elif len(match[0]) == 4:  # YYYY-MM-DD
                                dob = datetime(int(match[0]), int(match[1]), int(match[2]))
                            else:
                                year = int(match[2])
                                if year < 100:
                                    year = 1900 + year if year > 30 else 2000 + year
                                dob = datetime(year, int(match[0]), int(match[1]))
                            
                            formatted_dob = dob.strftime("%m-%d-%Y")
                            patient_info['dob'] = formatted_dob
                            patient_info['DOB'] = formatted_dob  # Also store original
                            break
                        except (ValueError, IndexError):
                            continue

            if patient_info:
                # Add formatted display names if we have enough info
                if 'firstname' in patient_info and 'lastname' in patient_info:
                    name_fmt = f"{patient_info['firstname']} {patient_info['lastname']}"
                    folder_fmt = f"{patient_info['lastname']}, {patient_info['firstname']}"
                    patient_info['full_name'] = name_fmt
                    patient_info['folder_name'] = folder_fmt
                    
                    # Add DOB to folder name if available
                    if 'dob' in patient_info:
                        folder_name = f"{folder_fmt} {patient_info['dob']}"
                        patient_info['folder_name'] = folder_name

            return patient_info

        except Exception as e:
            logger.error(f"Error parsing filename {filename}: {str(e)}")
            return {}

    def parse_ocr_text(self, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse patient information from OCR text"""
        patient_info = {}

        try:
            if not ocr_result.get('success') or not ocr_result.get('text'):
                return patient_info

            text = ocr_result['text']

            # Look for patient ID patterns
            id_patterns = [
                r'(?:Patient|ID|MRN|Chart)[\s#:]*(\d{3,})',
                r'(?:Patient|ID|MRN|Chart)[\s#:]*([A-Z]{1,2}\d{3,})'
            ]

            for pattern in id_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    patient_info['id'] = match.group(1)
                    break

            # Look for name patterns
            name_patterns = [
                r'Name:?\s*([\w\s-]+),\s*([\w\s-]+)',  # Name: lastname, firstname
                r'Patient:?\s*([\w\s-]+),\s*([\w\s-]+)',  # Patient: lastname, firstname
                r'(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s*([\w\s-]+),\s*([\w\s-]+)'  # Title lastname, firstname
            ]

            for pattern in name_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    last = self._clean_name(match.group(1))
                    first = self._clean_name(match.group(2))
                    
                    if last and first and len(last) > 1 and len(first) > 1:
                        patient_info['lastname'] = last
                        patient_info['firstname'] = first
                        patient_info['LastName'] = last
                        patient_info['FirstName'] = first
                        break

            # Look for DOB patterns
            dob_patterns = [
                r'(?:DOB|Birth|Born)[:;\s]+(\d{1,2})[-/_](\d{1,2})[-/_](\d{2,4})',
                r'(?:DOB|Birth|Born)[:;\s]+(\d{4})[-/_](\d{1,2})[-/_](\d{1,2})'
            ]

            for pattern in dob_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        dob = None
                        if len(match.group(3)) == 4:  # MM-DD-YYYY
                            dob = datetime(
                                int(match.group(3)),
                                int(match.group(1)),
                                int(match.group(2))
                            )
                        elif len(match.group(1)) == 4:  # YYYY-MM-DD
                            dob = datetime(
                                int(match.group(1)),
                                int(match.group(2)),
                                int(match.group(3))
                            )
                        else:  # MM-DD-YY
                            year = int(match.group(3))
                            if year < 100:
                                year = 1900 + year if year > 30 else 2000 + year
                            dob = datetime(year, int(match.group(1)), int(match.group(2)))
                        
                        formatted_dob = dob.strftime("%m-%d-%Y")
                        patient_info['dob'] = formatted_dob
                        patient_info['DOB'] = formatted_dob
                    except (ValueError, IndexError):
                        continue

            if patient_info:
                # Add formatted display names if we have enough info
                if 'firstname' in patient_info and 'lastname' in patient_info:
                    name_fmt = f"{patient_info['firstname']} {patient_info['lastname']}"
                    folder_fmt = f"{patient_info['lastname']}, {patient_info['firstname']}"
                    patient_info['full_name'] = name_fmt
                    patient_info['folder_name'] = folder_fmt
                    
                    # Add DOB to folder name if available
                    if 'dob' in patient_info:
                        folder_name = f"{folder_fmt} {patient_info['dob']}"
                        patient_info['folder_name'] = folder_name

        except Exception as e:
            logger.error(f"Error parsing OCR text: {str(e)}")

        return patient_info

    def combine_parsing_results(self, filename_data: Dict[str, Any], 
                              ocr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Combine and normalize patient data from multiple sources"""
        combined = {}

        try:
            # Prioritize OCR data for most fields since it's usually more reliable
            if ocr_data:
                combined.update(ocr_data)
            
            # Fill in gaps from filename data
            if filename_data:
                for field in ['id', 'lastname', 'firstname', 'dob']:
                    if field not in combined and field in filename_data:
                        combined[field] = filename_data[field]
                        # Copy alternate case versions too
                        if field == 'lastname':
                            combined['LastName'] = filename_data[field]
                        elif field == 'firstname':
                            combined['FirstName'] = filename_data[field]
                        elif field == 'dob':
                            combined['DOB'] = filename_data[field]

            if combined:
                # Generate formatted display names if we have enough info
                if 'firstname' in combined and 'lastname' in combined:
                    name_fmt = f"{combined['firstname']} {combined['lastname']}"
                    folder_fmt = f"{combined['lastname']}, {combined['firstname']}"
                    combined['full_name'] = name_fmt
                    combined['folder_name'] = folder_fmt
                    
                    # Add DOB to folder name if available
                    if 'dob' in combined:
                        folder_name = f"{folder_fmt} {combined['dob']}"
                        combined['folder_name'] = folder_name

        except Exception as e:
            logger.error(f"Error combining parsing results: {str(e)}")

        return combined

    def _clean_name(self, name: str) -> str:
        """Clean and normalize a name"""
        if not name:
            return ""

        # Remove extra whitespace
        name = ' '.join(name.split())

        # Capitalize first letter of each word
        name = name.title()

        # Remove invalid characters
        name = re.sub(r'[^a-zA-Z\s-]', '', name)

        # Handle hyphenated names
        parts = [p.strip().title() for p in name.split('-')]
        name = '-'.join(p for p in parts if p)

        return name.strip()
