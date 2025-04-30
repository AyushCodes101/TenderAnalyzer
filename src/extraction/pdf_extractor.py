"""
PDF extraction module with OCR capabilities.
"""

import os
from pathlib import Path
import tempfile
from loguru import logger
from tqdm import tqdm

import pytesseract
from pdf2image import convert_from_path
from pypdf import PdfReader

from utils.error_handler import error_handler, ExtractionError
from utils.config import Config


class PdfExtractor:
    """
    Class to extract text from PDF documents using OCR techniques.
    """
    
    def __init__(self):
        """Initialize the PDF extractor."""
        self.temp_dir = None
        logger.debug("PdfExtractor initialized")
        
    @error_handler
    def extract(self, pdf_path):
        """
        Extract text from a PDF file using OCR and direct text extraction.
        
        Args:
            pdf_path (str): Path to the PDF file.
            
        Returns:
            str: Extracted text from the PDF.
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise ExtractionError(f"PDF file not found: {pdf_path}")
        
        # Handle .txt files for testing
        if pdf_path.suffix.lower() == '.txt':
            logger.info(f"Detected text file: {pdf_path}. Reading directly.")
            return self._extract_from_text_file(pdf_path)
        
        logger.info(f"Extracting text from PDF: {pdf_path}")
        
        # Try direct text extraction first
        direct_text = self._extract_text_direct(pdf_path)
        
        # If we got sufficient text, return it
        if direct_text and len(direct_text) > 100:
            logger.info("Successfully extracted text directly from PDF")
            return direct_text
        
        # Otherwise, use OCR
        logger.info("Direct text extraction insufficient, falling back to OCR")
        ocr_text = self._extract_text_ocr(pdf_path)
        
        if not ocr_text:
            raise ExtractionError("Failed to extract text from PDF using both direct extraction and OCR")
        
        return ocr_text
    
    @error_handler
    def _extract_from_text_file(self, file_path):
        """
        Extract text from a plain text file (for testing purposes).
        
        Args:
            file_path (Path): Path to the text file.
            
        Returns:
            str: Text content of the file.
        """
        try:
            logger.debug(f"Reading text from file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Format to look similar to PDF extraction
            lines = text.split('\n')
            formatted_text = ""
            
            # Group text into pages (for simulation purposes)
            page_size = 50  # lines per page
            for i in range(0, len(lines), page_size):
                page_num = (i // page_size) + 1
                page_lines = lines[i:i+page_size]
                formatted_text += f"\n\n--- Page {page_num} ---\n\n" + "\n".join(page_lines)
                
            return formatted_text.strip()
            
        except Exception as e:
            logger.error(f"Failed to read text file: {str(e)}")
            raise ExtractionError(f"Failed to read text file: {str(e)}")
    
    @error_handler
    def _extract_text_direct(self, pdf_path):
        """
        Extract text directly from PDF without OCR.
        
        Args:
            pdf_path (Path): Path to the PDF file.
            
        Returns:
            str: Extracted text or empty string if extraction failed.
        """
        try:
            logger.debug("Attempting direct text extraction")
            reader = PdfReader(pdf_path)
            text = ""
            
            for i, page in enumerate(tqdm(reader.pages, desc="Extracting text directly")):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n\n--- Page {i+1} ---\n\n{page_text}"
            
            return text.strip()
        except Exception as e:
            logger.warning(f"Direct text extraction failed: {str(e)}")
            return ""
    
    @error_handler
    def _extract_text_ocr(self, pdf_path):
        """
        Extract text from PDF using OCR.
        
        Args:
            pdf_path (Path): Path to the PDF file.
            
        Returns:
            str: Extracted text from OCR.
        """
        try:
            # Create a temporary directory for images
            with tempfile.TemporaryDirectory() as temp_dir:
                self.temp_dir = temp_dir
                logger.debug(f"Created temporary directory for OCR: {temp_dir}")
                
                # Convert PDF to images
                logger.debug("Converting PDF to images")
                images = convert_from_path(
                    pdf_path, 
                    dpi=Config.OCR_DPI,
                    output_folder=temp_dir,
                    fmt="png"
                )
                
                # Extract text from each image
                logger.debug(f"Performing OCR on {len(images)} pages")
                full_text = ""
                
                for i, image in enumerate(tqdm(images, desc="Performing OCR")):
                    page_text = pytesseract.image_to_string(image, lang=Config.OCR_LANG)
                    full_text += f"\n\n--- Page {i+1} ---\n\n{page_text}"
                
                return full_text.strip()
                
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            raise ExtractionError(f"OCR extraction failed: {str(e)}")
        finally:
            self.temp_dir = None 