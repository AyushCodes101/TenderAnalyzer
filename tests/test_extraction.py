"""
Tests for the PDF extraction module.
"""

import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from extraction.pdf_extractor import PdfExtractor
from utils.error_handler import ExtractionError


class TestPdfExtractor(unittest.TestCase):
    """Tests for the PdfExtractor class."""
    
    def setUp(self):
        """Set up test environment."""
        self.extractor = PdfExtractor()
        self.test_pdf_path = Path("tests/sample_data/sample.pdf")
    
    @patch("extraction.pdf_extractor.PdfReader")
    def test_extract_text_direct(self, mock_pdf_reader):
        """Test direct text extraction from PDF."""
        # Mock PdfReader
        mock_reader = MagicMock()
        mock_pdf_reader.return_value = mock_reader
        
        # Mock page with text
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample text content"
        mock_reader.pages = [mock_page, mock_page]
        
        # Call the method
        with patch("pathlib.Path.exists", return_value=True):
            result = self.extractor._extract_text_direct(self.test_pdf_path)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertTrue("Sample text content" in result)
    
    @patch("extraction.pdf_extractor.convert_from_path")
    @patch("extraction.pdf_extractor.pytesseract.image_to_string")
    def test_extract_text_ocr(self, mock_image_to_string, mock_convert):
        """Test OCR text extraction from PDF."""
        # Mock convert_from_path
        mock_image1 = MagicMock()
        mock_image2 = MagicMock()
        mock_convert.return_value = [mock_image1, mock_image2]
        
        # Mock pytesseract.image_to_string
        mock_image_to_string.side_effect = ["OCR text page 1", "OCR text page 2"]
        
        # Call the method
        with patch("pathlib.Path.exists", return_value=True):
            result = self.extractor._extract_text_ocr(self.test_pdf_path)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertTrue("OCR text page 1" in result)
        self.assertTrue("OCR text page 2" in result)
    
    @patch.object(PdfExtractor, "_extract_text_direct")
    @patch.object(PdfExtractor, "_extract_text_ocr")
    def test_extract_with_direct_success(self, mock_ocr, mock_direct):
        """Test extraction with successful direct extraction."""
        # Mock direct extraction with good result
        mock_direct.return_value = "Good direct text " * 20  # More than 100 chars
        
        # Call the method
        with patch("pathlib.Path.exists", return_value=True):
            result = self.extractor.extract(self.test_pdf_path)
        
        # Assertions
        self.assertEqual(result, mock_direct.return_value)
        mock_ocr.assert_not_called()  # OCR should not be called
    
    @patch.object(PdfExtractor, "_extract_text_direct")
    @patch.object(PdfExtractor, "_extract_text_ocr")
    def test_extract_with_ocr_fallback(self, mock_ocr, mock_direct):
        """Test extraction with fallback to OCR."""
        # Mock direct extraction with poor result
        mock_direct.return_value = "Short text"  # Less than 100 chars
        
        # Mock OCR extraction
        mock_ocr.return_value = "Good OCR text result"
        
        # Call the method
        with patch("pathlib.Path.exists", return_value=True):
            result = self.extractor.extract(self.test_pdf_path)
        
        # Assertions
        self.assertEqual(result, mock_ocr.return_value)
        mock_direct.assert_called_once()
        mock_ocr.assert_called_once()
    
    def test_extract_file_not_found(self):
        """Test extraction with non-existent file."""
        with patch("pathlib.Path.exists", return_value=False):
            with self.assertRaises(ExtractionError):
                self.extractor.extract("nonexistent.pdf")
    
    @patch.object(PdfExtractor, "_extract_text_direct")
    @patch.object(PdfExtractor, "_extract_text_ocr")
    def test_extract_both_methods_fail(self, mock_ocr, mock_direct):
        """Test extraction when both methods fail."""
        # Mock both extraction methods to fail
        mock_direct.return_value = ""
        mock_ocr.return_value = ""
        
        # Call the method
        with patch("pathlib.Path.exists", return_value=True):
            with self.assertRaises(ExtractionError):
                self.extractor.extract(self.test_pdf_path)


if __name__ == "__main__":
    unittest.main() 