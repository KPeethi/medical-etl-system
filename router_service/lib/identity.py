import re
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any

class PatientIdentity:
    """Patient identification from rosters, filenames, and folder structure"""
    
    def __init__(self, roster_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.roster: Dict[str, Dict[str, Any]] = {}
        self.config = config or {}
        
        if roster_path:
            self.load_roster(roster_path)
    
    def load_roster(self, roster_path: str):
        """Load patient roster from Excel file"""
        try:
            wb = openpyxl.load_workbook(roster_path, read_only=True, data_only=True)
            ws: Worksheet = wb.active  # type: ignore
            
            headers = []
            data_rows = []
            
            for row_idx, row in enumerate(ws.iter_rows(values_only=True), 1):
                if row_idx == 1 or not headers:
                    potential_headers = [str(cell).lower().strip() if cell else '' for cell in row]
                    if self._looks_like_header_row(potential_headers):
                        headers = potential_headers
                        continue
                
                if headers and any(row):
                    data_rows.append(row)
            
            header_map = self._map_headers(headers)
            
            for row in data_rows:
                patient = self._parse_roster_row(row, headers, header_map)
                if patient:
                    patient_key = self._make_patient_key(
                        patient.get('last', ''),
                        patient.get('first', ''),
                        patient.get('dob')
                    )
                    if patient_key:
                        self.roster[patient_key] = patient
            
            wb.close()
        except Exception as e:
            print(f"Warning: Could not load roster from {roster_path}: {e}")
    
    def _looks_like_header_row(self, row: List[str]) -> bool:
        """Check if row looks like headers"""
        hints = self.config.get('identity', {}).get('roster', {}).get('hints', {})
        all_hints = []
        for hint_list in hints.values():
            all_hints.extend(hint_list)
        
        for cell in row:
            if any(hint in cell.lower() for hint in all_hints):
                return True
        return False
    
    def _map_headers(self, headers: List[str]) -> Dict[str, int]:
        """Map column names to indices using hints"""
        hints = self.config.get('identity', {}).get('roster', {}).get('hints', {})
        header_map = {}
        
        for field, hint_list in hints.items():
            for idx, header in enumerate(headers):
                if any(hint in header for hint in hint_list):
                    header_map[field] = idx
                    break
        
        return header_map
    
    def _parse_roster_row(self, row: tuple, headers: List[str], header_map: Dict[str, int]) -> Optional[Dict]:
        """Parse a roster row into patient data"""
        try:
            patient = {}
            
            if 'last' in header_map and header_map['last'] < len(row):
                patient['last'] = self._clean_name(row[header_map['last']])
            
            if 'first' in header_map and header_map['first'] < len(row):
                patient['first'] = self._clean_name(row[header_map['first']])
            
            if 'dob' in header_map and header_map['dob'] < len(row):
                patient['dob'] = self._parse_dob(row[header_map['dob']])
            
            if patient.get('last') and patient.get('first'):
                return patient
            
            return None
        except Exception:
            return None
    
    def _clean_name(self, name: Any) -> str:
        """Clean and normalize name"""
        if not name:
            return ''
        name_str = str(name).strip()
        name_str = re.sub(r'[^\w\s\-\']', '', name_str)
        return name_str.title()
    
    def _parse_dob(self, dob: Any) -> Optional[str]:
        """Parse date of birth to YYYY-MM-DD format"""
        if not dob:
            return None
        
        if isinstance(dob, datetime):
            return dob.strftime('%Y-%m-%d')
        
        dob_str = str(dob).strip()
        
        date_formats = [
            '%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y',
            '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(dob_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def identify_from_filename(self, filename: str, folder_path: str = '') -> Optional[Dict]:
        """Extract patient identity from filename patterns"""
        patterns = [
            r'([A-Z][a-z]+)[_\s,]+([A-Z][a-z]+)[\s_]*([\d\-/]+)',
            r'(\w+),\s*(\w+)\s+([\d\-/]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                candidate = {
                    'last': self._clean_name(match.group(1)),
                    'first': self._clean_name(match.group(2)),
                    'dob': self._parse_dob(match.group(3)),
                    'source': 'filename'
                }
                
                if candidate.get('last') and candidate.get('first'):
                    return candidate
        
        return None
    
    def match_to_roster(self, last: str, first: str, dob: Optional[str] = None) -> Optional[Dict]:
        """Match patient to roster"""
        patient_key = self._make_patient_key(last, first, dob)
        
        if patient_key in self.roster:
            return {**self.roster[patient_key], 'source': 'roster_exact'}
        
        fuzzy_key = self._make_patient_key(last, first, None)
        for key, patient in self.roster.items():
            if key.startswith(fuzzy_key):
                return {**patient, 'source': 'roster_fuzzy'}
        
        return None
    
    def _make_patient_key(self, last: Optional[str], first: Optional[str], dob: Optional[str]) -> str:
        """Create normalized patient key"""
        if not last or not first:
            return ''
        
        last_clean = re.sub(r'[^\w]', '', last.upper())
        first_clean = re.sub(r'[^\w]', '', first.upper())
        
        if dob:
            return f"{last_clean}_{first_clean}_{dob}"
        return f"{last_clean}_{first_clean}"
    
    def format_patient_folder(self, patient: Dict) -> str:
        """Format patient folder name"""
        template = self.config.get('naming', {}).get('patient_folder', '{Last}, {First} {DOB_MM}-{DOB_DD}-{DOB_YYYY}')
        
        last = patient.get('last', 'Unknown')
        first = patient.get('first', 'Unknown')
        dob = patient.get('dob', '')
        
        if dob:
            try:
                dt = datetime.strptime(dob, '%Y-%m-%d')
                folder_name = template.format(
                    Last=last,
                    First=first,
                    DOB_MM=dt.strftime('%m'),
                    DOB_DD=dt.strftime('%d'),
                    DOB_YYYY=dt.strftime('%Y')
                )
            except ValueError:
                folder_name = f"{last}, {first}"
        else:
            folder_name = f"{last}, {first}"
        
        return folder_name
