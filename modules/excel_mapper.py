"""Excel Mapping Handler for Medical ETL System"""
# pyright: reportMissingTypeStubs=false

import pandas as pd  # type: ignore
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ExcelMapper:
    """Excel mapping processor with smart column detection"""

    @staticmethod
    def load_excel_mapping(file_path: Path) -> Dict[str, Dict[str, Any]]:
        """
        Load Excel mapping file and convert to patient data dictionary

        Args:
            file_path: Path to Excel mapping file

        Returns:
            Dictionary mapping patient IDs to their information
        """
        try:
            df = pd.read_excel(file_path)
            mapping = {}

            # Expected column mappings (case-insensitive)
            column_mappings = {
                'id': ['PatientID', 'Patient_ID', 'ID', 'patient_id'],
                'lastname': ['LastName', 'Last Name', 'Surname', 'last_name'],
                'firstname': [
                    'FirstName', 'First Name', 'GivenName', 'first_name'
                ],
                'dob': ['DOB', 'DateOfBirth', 'BirthDate', 'Date of Birth']
            }

            # First try exact column names from demographics.xlsx
            known_mappings = {
                'PatientID': 'id',
                'LastName': 'lastname',
                'FirstName': 'firstname',
                'DOB': 'dob'
            }

            # Find actual column names in DataFrame
            df_columns = df.columns
            found_columns = {}

            # First try exact matches we expect
            for col in df_columns:
                if col in known_mappings:
                    found_columns[known_mappings[col]] = col

            # Then try other possible names for any missing fields
            for field, possible_names in column_mappings.items():
                if field not in found_columns:
                    for col in df_columns:
                        if col in possible_names:
                            found_columns[field] = col
                            break

            # Verify we found all required columns
            missing = [f for f in column_mappings if f not in found_columns]
            if missing:
                msg = f"Missing columns: {', '.join(missing)}"
                raise ValueError(msg)

            # Convert to patient mapping dictionary using found column names
            for _, row in df.iterrows():
                patient_id = str(row[found_columns['id']]).strip()
                if patient_id and pd.notna(patient_id):
                    try:
                        # Ensure numeric patient ID is properly formatted
                        patient_id = str(int(float(patient_id)))
                    except ValueError:
                        pass

                    patient_info = {'id': patient_id}

                    # Handle LastName - capitalize first letter
                    ln = str(row[found_columns['lastname']]).strip()
                    lastname = ln.title()
                    patient_info['lastname'] = lastname
                    # Also store with original casing
                    patient_info['LastName'] = lastname

                    # Handle FirstName - capitalize first letter
                    fn = str(row[found_columns['firstname']]).strip()
                    firstname = fn.title()
                    patient_info['firstname'] = firstname
                    # Also store with original casing
                    patient_info['FirstName'] = firstname

                    # Handle DOB - normalize to MM-DD-YYYY format
                    dob_raw = str(row[found_columns['dob']]).strip()
                    try:
                        # Try parsing common date formats
                        date_formats = [
                            "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y",
                            "%m/%d/%y", "%m-%d-%y"
                        ]
                        dob = None
                        for fmt in date_formats:
                            try:
                                dob_date = datetime.strptime(dob_raw, fmt)
                                dob = dob_date.strftime("%m-%d-%Y")
                                patient_info['dob'] = dob
                                # Also store with original casing
                                patient_info['DOB'] = dob
                                break
                            except ValueError:
                                continue
                        # If parsing fails, store raw value
                        if not dob:
                            patient_info['dob'] = dob_raw
                            patient_info['DOB'] = dob_raw
                    except Exception as e:
                        msg = f"Error formatting DOB for patient {patient_id}"
                        logger.warning(f"{msg}: {str(e)}")
                        patient_info['dob'] = dob_raw
                        patient_info['DOB'] = dob_raw

                    # Add any additional columns as lowercase
                    mapped_cols = [found_columns[k] for k in found_columns]
                    for col in df_columns:
                        if col not in mapped_cols:
                            value = str(row[col]).strip()
                            patient_info[col.lower()] = value

                    # Generate formatted names for display
                    name_fmt = f"{firstname} {lastname}"
                    folder_fmt = f"{lastname}, {firstname}"
                    patient_info['full_name'] = name_fmt
                    patient_info['folder_name'] = folder_fmt
                    
                    # Add DOB to folder name if available
                    if 'dob' in patient_info:
                        folder_name = f"{folder_fmt} {patient_info['dob']}"
                        patient_info['folder_name'] = folder_name

                    mapping[patient_id] = patient_info

            return mapping

        except Exception as e:
            logger.error(f"Error loading Excel mapping {file_path}: {str(e)}")
            raise
