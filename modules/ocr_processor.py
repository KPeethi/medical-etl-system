"""
OCR Processor with graceful degradation.
Attempts to use Tesseract via pytesseract and pdf2image for PDFs.
If dependencies are missing, returns success=False without crashing.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from medical_etl_system.config.config import Config

logger = logging.getLogger(__name__)


class OCRProcessor:
    def __init__(self):
        self.config = Config()
        self._tesseract_ok = False
        self._pytesseract = None
        self._pdf2image = None
        self._pillow_image = None

        try:
            import pytesseract  # type: ignore
            from PIL import Image  # type: ignore
            self._pytesseract = pytesseract
            self._pillow_image = Image
            # Wire tesseract path if detected in config
            if self.config.TESSERACT_CMD:
                pytesseract.pytesseract.tesseract_cmd = (
                    self.config.TESSERACT_CMD
                )
            self._tesseract_ok = True
        except Exception:
            logger.error(
                "Error setting up Tesseract: not installed or not in PATH. "
                "See README for installation instructions."
            )

        try:
            import pdf2image  # type: ignore
            self._pdf2image = pdf2image
        except Exception:
            # optional dependency
            self._pdf2image = None

    def get_processing_statistics(self) -> Dict[str, Any]:
        return {
            'tesseract_available': self._tesseract_ok,
            'pdf2image_available': self._pdf2image is not None
        }

    def extract_text_from_file(
        self, file_path: Path, max_pages: int = 3, deep_scan: bool = False
    ) -> Dict[str, Any]:
        """Extract text; graceful fallback when OCR unavailable."""
        result: Dict[str, Any] = {
            'success': False,
            'text': '',
            'pages': [],
            'total_pages': 0,
            'error': ''
        }

        try:
            if not self._tesseract_ok:
                result['error'] = 'tesseract_not_available'
                return result

            suffix = file_path.suffix.lower()
            if suffix == '.pdf':
                if not self._pdf2image:
                    result['error'] = 'pdf2image_not_available'
                    return result
                return self._extract_pdf_text(file_path, max_pages)
            else:
                return self._extract_image_text(file_path)
        except Exception as e:
            result['error'] = str(e)
            return result

    def _extract_image_text(self, file_path: Path) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            'success': False, 'text': '', 'pages': [], 'total_pages': 1
        }
        try:
            if not self._pillow_image or not self._pytesseract:
                out['error'] = 'dependencies_missing'
                return out
            img = self._pillow_image.open(file_path)
            text = self._pytesseract.image_to_string(img)
            out['success'] = True
            out['text'] = text
            out['pages'] = [{'page': 1, 'text': text, 'confidence': 0}]
            return out
        except Exception as e:
            out['error'] = str(e)
            return out

    def _extract_pdf_text(
        self, file_path: Path, max_pages: int
    ) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            'success': False, 'text': '', 'pages': [], 'total_pages': 0
        }
        try:
            assert (
                self._pdf2image is not None and self._pytesseract is not None
            )
            pages = self._pdf2image.convert_from_path(str(file_path))
            out['total_pages'] = len(pages)
            pages_to_ocr = pages[:max_pages]
            all_text: List[str] = []
            for i, img in enumerate(pages_to_ocr, start=1):
                text = self._pytesseract.image_to_string(img)
                out['pages'].append({'page': i, 'text': text, 'confidence': 0})
                all_text.append(text)
            out['text'] = '\n'.join(all_text)
            out['success'] = True
            return out
        except Exception as e:
            out['error'] = str(e)
            return out

    def clear_cache(self):
        # no-op stub for now
        return
