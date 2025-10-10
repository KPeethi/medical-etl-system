"""
OCR Processing Module for Medical ETL System
Handles text extraction from images and PDFs using Tesseract
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image
import pytesseract
import pdf2image
from config.config import Config

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Handles OCR processing for images and PDFs"""
    
    def __init__(self):
        self.config = Config()
        self._setup_tesseract()
        self.processed_files = []
        
    def _setup_tesseract(self):
        """Setup Tesseract OCR configuration"""
        try:
            # Set Tesseract executable path
            if self.config.TESSERACT_CMD:
                pytesseract.pytesseract.tesseract_cmd = self.config.TESSERACT_CMD
            
            # Test Tesseract installation
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
            
        except Exception as e:
            logger.error(f"Error setting up Tesseract: {str(e)}")
            logger.error("Please ensure Tesseract OCR is properly installed")
    
    def extract_text_from_file(self, file_path: Path, max_pages: int = None, deep_scan: bool = False) -> Dict[str, any]:
        """
        Extract text from image or PDF file
        
        Args:
            file_path: Path to the file
            max_pages: Maximum number of pages to process (None for all)
            deep_scan: Whether this is a deep scan operation
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        result = {
            'file_path': str(file_path),
            'text': '',
            'confidence': 0,
            'pages': [],
            'success': False,
            'error': None
        }
        
        try:
            if self.config.is_image_file(file_path):
                result = self._extract_from_image(file_path)
            elif self.config.is_pdf_file(file_path):
                result = self._extract_from_pdf(file_path, max_pages, deep_scan)
            else:
                result['error'] = f"Unsupported file type: {file_path.suffix}"
                logger.warning(result['error'])
            
            self.processed_files.append(result)
            return result
            
        except Exception as e:
            error_msg = f"Error processing file {file_path}: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
            return result
    
    def _extract_from_image(self, image_path: Path) -> Dict[str, any]:
        """Extract text from image file"""
        result = {
            'file_path': str(image_path),
            'text': '',
            'confidence': 0,
            'pages': [],
            'success': False,
            'error': None
        }
        
        try:
            # Open and preprocess image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Enhance image quality for better OCR
            enhanced_image = self._enhance_image(image)
            
            # Extract text with confidence scores
            text_data = pytesseract.image_to_data(
                enhanced_image,
                output_type=pytesseract.Output.DICT,
                lang='+'.join(self.config.OCR_LANGUAGES)
            )
            
            # Process OCR results
            text_blocks = []
            confidences = []
            
            for i in range(len(text_data['text'])):
                if int(text_data['conf'][i]) > 0:
                    word = text_data['text'][i].strip()
                    if word:
                        text_blocks.append(word)
                        confidences.append(int(text_data['conf'][i]))
            
            # Combine text and calculate average confidence
            result['text'] = ' '.join(text_blocks)
            result['confidence'] = sum(confidences) / len(confidences) if confidences else 0
            result['pages'] = [{'text': result['text'], 'confidence': result['confidence']}]
            result['success'] = len(text_blocks) > 0
            
            logger.debug(f"Extracted {len(text_blocks)} words from {image_path}")
            
        except Exception as e:
            error_msg = f"Error extracting text from image {image_path}: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
        
        return result
    
    def _extract_from_pdf(self, pdf_path: Path, max_pages: int = None, deep_scan: bool = False) -> Dict[str, any]:
        """Extract text from PDF file with optional page limits"""
        result = {
            'file_path': str(pdf_path),
            'text': '',
            'confidence': 0,
            'pages': [],
            'total_pages': 0,
            'pages_processed': 0,
            'success': False,
            'error': None
        }
        
        try:
            # Convert PDF pages to images
            pages = pdf2image.convert_from_path(
                pdf_path,
                dpi=300,  # High DPI for better OCR
                fmt='PNG'
            )
            
            result['total_pages'] = len(pages)
            
            # Determine how many pages to process
            pages_to_process = len(pages)
            if max_pages is not None:
                pages_to_process = min(max_pages, len(pages))
            
            if deep_scan:
                logger.info(f"Deep scanning PDF {pdf_path.name}: processing {pages_to_process} of {len(pages)} pages")
            
            all_text = []
            all_confidences = []
            
            for page_num, page_image in enumerate(pages[:pages_to_process], 1):
                try:
                    # Extract text from each page
                    page_result = self._process_pdf_page(page_image, page_num)
                    result['pages'].append(page_result)
                    
                    if page_result['text'].strip():
                        all_text.append(page_result['text'])
                        all_confidences.append(page_result['confidence'])
                        
                        if deep_scan:
                            logger.debug(f"Page {page_num}: Found {len(page_result['text'])} characters")
                    
                except Exception as e:
                    logger.warning(f"Error processing page {page_num} of {pdf_path}: {str(e)}")
                    result['pages'].append({
                        'page': page_num,
                        'text': '',
                        'confidence': 0,
                        'error': str(e)
                    })
            
            result['pages_processed'] = pages_to_process
            
            # Combine all pages
            result['text'] = '\n'.join(all_text)
            result['confidence'] = sum(all_confidences) / len(all_confidences) if all_confidences else 0
            result['success'] = len(all_text) > 0
            
            if deep_scan:
                logger.info(f"Deep scan completed for {pdf_path.name}: {len(all_text)} pages with text found")
            else:
                logger.debug(f"Extracted text from {pages_to_process} pages of {pdf_path}")
            
        except Exception as e:
            error_msg = f"Error extracting text from PDF {pdf_path}: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
        
        return result
        
        return result
    
    def _process_pdf_page(self, page_image: Image.Image, page_num: int) -> Dict[str, any]:
        """Process a single PDF page"""
        page_result = {
            'page': page_num,
            'text': '',
            'confidence': 0,
            'error': None
        }
        
        try:
            # Enhance image quality
            enhanced_image = self._enhance_image(page_image)
            
            # Extract text with confidence
            text_data = pytesseract.image_to_data(
                enhanced_image,
                output_type=pytesseract.Output.DICT,
                lang='+'.join(self.config.OCR_LANGUAGES)
            )
            
            # Process results
            text_blocks = []
            confidences = []
            
            for i in range(len(text_data['text'])):
                if int(text_data['conf'][i]) > 0:
                    word = text_data['text'][i].strip()
                    if word:
                        text_blocks.append(word)
                        confidences.append(int(text_data['conf'][i]))
            
            page_result['text'] = ' '.join(text_blocks)
            page_result['confidence'] = sum(confidences) / len(confidences) if confidences else 0
            
        except Exception as e:
            page_result['error'] = str(e)
        
        return page_result
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Enhance image quality for better OCR results"""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Resize if image is too small (improve OCR accuracy)
            width, height = image.size
            if width < 1000 or height < 1000:
                scale_factor = max(1000 / width, 1000 / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            logger.warning(f"Error enhancing image: {str(e)}")
            return image
    
    def extract_patient_data(self, text: str) -> Dict[str, List[str]]:
        """
        Extract patient information from OCR text
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with extracted patient data
        """
        extracted_data = {
            'names': [],
            'dates': [],
            'ids': [],
            'potential_lastnames': [],
            'potential_firstnames': []
        }
        
        try:
            # Extract names using patterns
            for pattern in self.config.NAME_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:  # lastname, firstname
                        lastname, firstname = match
                        if self._is_valid_name(lastname) and self._is_valid_name(firstname):
                            extracted_data['names'].append((lastname.strip(), firstname.strip()))
                            extracted_data['potential_lastnames'].append(lastname.strip())
                            extracted_data['potential_firstnames'].append(firstname.strip())
            
            # Extract dates
            for pattern in self.config.DATE_PATTERNS:
                matches = re.findall(pattern, text)
                for match in matches:
                    date_str = '/'.join(match) if isinstance(match, tuple) else match
                    if self._is_valid_date_format(date_str):
                        extracted_data['dates'].append(date_str)
            
            # Extract IDs
            for pattern in self.config.ID_PATTERNS:
                matches = re.findall(pattern, text)
                for match in matches:
                    if self._is_valid_id(match):
                        extracted_data['ids'].append(match)
            
            # Remove duplicates
            for key in extracted_data:
                if isinstance(extracted_data[key], list):
                    extracted_data[key] = list(set(extracted_data[key]))
            
        except Exception as e:
            logger.error(f"Error extracting patient data from text: {str(e)}")
        
        return extracted_data
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if extracted name is valid"""
        if not name or len(name) < 2:
            return False
        
        # Check for common OCR errors and invalid patterns
        invalid_patterns = [
            r'^\d+$',  # Only numbers
            r'^[^a-zA-Z]*$',  # No letters
            r'[<>{}[\]|\\]',  # Special characters
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, name):
                return False
        
        return True
    
    def _is_valid_date_format(self, date_str: str) -> bool:
        """Check if extracted date is in valid format"""
        try:
            # Basic validation for date patterns
            if re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$', date_str):
                parts = re.split(r'[/-]', date_str)
                if len(parts) == 3:
                    month, day, year = map(int, parts)
                    return 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2030
            return False
        except:
            return False
    
    def _is_valid_id(self, id_str: str) -> bool:
        """Check if extracted ID is valid"""
        if not id_str or len(id_str) < 3:
            return False
        
        # Filter out common OCR noise
        if id_str.lower() in ['the', 'and', 'for', 'you', 'are', 'not']:
            return False
        
        return True
    
    def get_processing_statistics(self) -> Dict[str, any]:
        """Get statistics about OCR processing"""
        total_files = len(self.processed_files)
        successful_files = sum(1 for f in self.processed_files if f['success'])
        total_confidence = sum(f['confidence'] for f in self.processed_files if f['success'])
        
        return {
            'total_files_processed': total_files,
            'successful_extractions': successful_files,
            'failed_extractions': total_files - successful_files,
            'success_rate': (successful_files / total_files * 100) if total_files > 0 else 0,
            'average_confidence': (total_confidence / successful_files) if successful_files > 0 else 0,
            'total_pages_processed': sum(len(f['pages']) for f in self.processed_files)
        }
    
    def clear_cache(self):
        """Clear processed files cache"""
        self.processed_files.clear()
        logger.debug("OCR processor cache cleared")