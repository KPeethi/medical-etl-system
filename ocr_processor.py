#!/usr/bin/env python3
"""
OCR Processor for Medical Files
Extracts patient names and DOB from PDFs when other methods fail
"""

import os
import re
import logging
import tempfile
from datetime import datetime
from pathlib import Path

try:
    import cv2
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    import numpy as np
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

class MedicalOCRProcessor:
    """OCR processor for extracting patient info from medical documents"""
    
    def __init__(self):
        if not OCR_AVAILABLE:
            raise ImportError(
                "OCR dependencies not installed. Run: "
                "pip install pytesseract pdf2image opencv-python Pillow"
            )
        
        # Set Tesseract path (adjust for your installation)
        if os.name == 'nt':  # Windows
            tesseract_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Tesseract-OCR\tesseract.exe'
            ]
            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
        
        # Name patterns for medical documents
        self.name_patterns = [
            r'Patient[:\s]+([A-Z][a-z]+)[,\s]+([A-Z][a-z]+)',
            r'Name[:\s]+([A-Z][a-z]+)[,\s]+([A-Z][a-z]+)',
            r'([A-Z][a-z]+)[,\s]+([A-Z][a-z]+)\s+DOB',
            r'MR[N#]?\s*\d+\s+([A-Z][a-z]+)[,\s]+([A-Z][a-z]+)',
            r'([A-Z]{2,})[,\s]+([A-Z]{2,})',  # All caps names
        ]
        
        # DOB patterns
        self.dob_patterns = [
            r'DOB[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'Birth[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'Born[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'DOB[:\s]+(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        ]

    def extract_patient_from_pdf(self, pdf_path, max_pages=20):
        """Extract patient info from PDF using OCR"""
        
        if not OCR_AVAILABLE:
            return None
            
        try:
            logging.info(f"Starting OCR processing for: {pdf_path}")
            
            # Convert PDF pages to images
            with tempfile.TemporaryDirectory() as temp_dir:
                images = convert_from_path(
                    pdf_path, 
                    first_page=1, 
                    last_page=max_pages,
                    dpi=300,
                    output_folder=temp_dir
                )
                
                patient_info = None
                
                for page_num, image in enumerate(images, 1):
                    logging.info(f"OCR processing page {page_num}")
                    
                    # Enhance image for better OCR
                    enhanced_image = self._enhance_image_for_ocr(image)
                    
                    # Extract text using OCR
                    text = pytesseract.image_to_string(
                        enhanced_image, 
                        config='--psm 6'
                    )
                    
                    # Search for patient info
                    patient_info = self._extract_patient_from_text(text, page_num)
                    
                    if patient_info:
                        logging.info(f"Patient found on page {page_num}: {patient_info}")
                        break
                
                return patient_info
                
        except Exception as e:
            logging.error(f"OCR processing failed for {pdf_path}: {str(e)}")
            return None

    def _enhance_image_for_ocr(self, pil_image):
        """Enhance image quality for better OCR accuracy"""
        
        try:
            # Convert PIL to OpenCV
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Increase contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Noise reduction
            denoised = cv2.medianBlur(enhanced, 3)
            
            # Convert back to PIL
            return Image.fromarray(denoised)
            
        except Exception as e:
            logging.warning(f"Image enhancement failed: {e}")
            return pil_image

    def _extract_patient_from_text(self, text, page_num):
        """Extract patient name and DOB from OCR text"""
        
        # Clean up text
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('\n', ' ')
        
        # Search for patient name
        patient_name = self._find_patient_name(text)
        
        # Search for DOB
        patient_dob = self._find_patient_dob(text)
        
        if patient_name:
            result = {
                'last': patient_name['last'],
                'first': patient_name['first'],
                'dob': patient_dob if patient_dob else 'unknown',
                'source': 'ocr',
                'page': page_num,
                'confidence': self._calculate_confidence(patient_name, patient_dob)
            }
            return result
        
        return None

    def _find_patient_name(self, text):
        """Find patient name using regex patterns"""
        
        for pattern in self.name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2:
                    return {
                        'last': match.group(1).title(),
                        'first': match.group(2).title()
                    }
        
        return None

    def _find_patient_dob(self, text):
        """Find date of birth using regex patterns"""
        
        for pattern in self.dob_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dob_str = match.group(1)
                return self._normalize_dob(dob_str)
        
        return None

    def _normalize_dob(self, dob_str):
        """Normalize DOB to YYYY-MM-DD format"""
        
        formats = [
            '%m/%d/%Y', '%m-%d-%Y',
            '%Y/%m/%d', '%Y-%m-%d',
            '%d/%m/%Y', '%d-%m-%Y',
        ]
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(dob_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return dob_str

    def _calculate_confidence(self, name_info, dob_info):
        """Calculate confidence score for OCR results"""
        
        confidence = 0
        
        if name_info:
            confidence += 0.6
            if len(name_info['first']) > 2 and len(name_info['last']) > 2:
                confidence += 0.2
        
        if dob_info and dob_info != 'unknown':
            confidence += 0.3
        
        return min(confidence, 1.0)

def test_ocr_setup():
    """Test if OCR is properly configured"""
    try:
        if not OCR_AVAILABLE:
            print("❌ OCR dependencies not installed")
            return False
        
        # Test Tesseract
        test_image = Image.new('RGB', (100, 30), color='white')
        pytesseract.image_to_string(test_image)
        print("✅ OCR setup is working")
        return True
        
    except Exception as e:
        print(f"❌ OCR setup failed: {e}")
        return False

if __name__ == '__main__':
    # Test OCR setup
    test_ocr_setup()