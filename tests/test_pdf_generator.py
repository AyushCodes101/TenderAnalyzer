"""
Tests for the PDF generator module.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from output.pdf_generator import OutputPdfGenerator
from utils.error_handler import OutputError


class TestPdfGenerator(unittest.TestCase):
    """Tests for the OutputPdfGenerator class."""
    
    def setUp(self):
        """Set up test environment."""
        self.pdf_generator = OutputPdfGenerator()
        self.test_key_points = {
            "Deadline": "Submission deadline: 31st December 2023",
            "Project Requirement": "Build a web application with user authentication",
            "Cost": "Total budget: $50,000",
            "Quality Checking": "Software testing requirements: unit tests, integration tests"
        }
    
    def test_initialization(self):
        """Test initialization of the PDF generator."""
        # Assert that styles are initialized
        self.assertIsNotNone(self.pdf_generator.styles)
        self.assertIsNotNone(self.pdf_generator.title_style)
        self.assertIsNotNone(self.pdf_generator.heading_style)
        self.assertIsNotNone(self.pdf_generator.normal_style)
        self.assertIsNotNone(self.pdf_generator.info_style)
    
    @patch("output.pdf_generator.SimpleDocTemplate")
    @patch("output.pdf_generator.Paragraph")
    @patch("output.pdf_generator.Table")
    def test_create_pdf(self, mock_table, mock_paragraph, mock_doc):
        """Test PDF creation with mocked ReportLab components."""
        # Arrange
        mock_doc_instance = MagicMock()
        mock_doc.return_value = mock_doc_instance
        
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        
        # Create a temp file to use as output
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            output_file = Path(temp_file.name)
        
        try:
            # Act
            self.pdf_generator._create_pdf(self.test_key_points, output_file)
            
            # Assert
            mock_doc.assert_called_once()
            mock_doc_instance.build.assert_called_once()
            mock_table.assert_called_once()
            mock_table_instance.setStyle.assert_called_once()
            
            # Check that Paragraph was called multiple times (title, sections, etc.)
            self.assertGreater(mock_paragraph.call_count, 5)
            
        finally:
            # Clean up
            if output_file.exists():
                os.remove(output_file)
    
    @patch("output.pdf_generator.OutputPdfGenerator._create_pdf")
    @patch("pathlib.Path.mkdir")
    def test_generate(self, mock_mkdir, mock_create_pdf):
        """Test generate method."""
        # Arrange
        output_dir = "test_output"
        input_filename = "test_input.pdf"
        
        # Act
        with patch("utils.helpers.generate_output_filename") as mock_generate_filename:
            mock_generate_filename.return_value = "test_output_file.pdf"
            result = self.pdf_generator.generate(
                self.test_key_points,
                output_dir=output_dir,
                input_filename=input_filename
            )
            
            # Assert
            mock_mkdir.assert_called_once_with(exist_ok=True, parents=True)
            mock_create_pdf.assert_called_once()
            self.assertTrue(result.endswith("test_output_file.pdf"))
    
    @patch("output.pdf_generator.SimpleDocTemplate")
    def test_create_pdf_error_handling(self, mock_doc):
        """Test error handling during PDF creation."""
        # Arrange
        mock_doc.side_effect = Exception("PDF creation error")
        
        # Create a temp file to use as output
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            output_file = Path(temp_file.name)
        
        try:
            # Act and Assert
            with self.assertRaises(OutputError):
                self.pdf_generator._create_pdf(self.test_key_points, output_file)
                
        finally:
            # Clean up
            if output_file.exists():
                os.remove(output_file)


if __name__ == "__main__":
    unittest.main() 