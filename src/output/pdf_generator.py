"""
PDF generation module for tender analyzer output.
"""

import os
from datetime import datetime
from pathlib import Path
from loguru import logger

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from utils.error_handler import error_handler, OutputError
from utils.config import Config
from utils.helpers import generate_output_filename, strip_extension


class OutputPdfGenerator:
    """
    Class to generate output PDF files with extracted key points.
    """
    
    def __init__(self):
        """Initialize the PDF generator."""
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        logger.debug("OutputPdfGenerator initialized")
    
    @error_handler
    def _create_custom_styles(self):
        """Create custom paragraph styles for the PDF."""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue,
        )
        
        # Heading style
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=16,
            textColor=colors.darkblue,
        )
        
        # Normal text style
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            spaceBefore=6,
            spaceAfter=6,
        )
        
        # Info box style
        self.info_style = ParagraphStyle(
            'InfoBox',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            leftIndent=20,
            rightIndent=20,
            spaceBefore=8,
            spaceAfter=8,
            backColor=colors.lightgrey,
            borderWidth=1,
            borderColor=colors.grey,
            borderPadding=8,
        )
    
    @error_handler
    def generate(self, key_points, output_dir=None, input_filename=None):
        """
        Generate a PDF file with the extracted key points.
        
        Args:
            key_points (dict): Dictionary containing extracted key points.
            output_dir (str, optional): Directory to save the output PDF.
            input_filename (str, optional): Original input filename.
            
        Returns:
            str: Path to the generated PDF file.
        """
        # Ensure output directory exists
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = Config.OUTPUT_DIR
        
        output_path.mkdir(exist_ok=True, parents=True)
        
        # Generate output filename
        if input_filename:
            base_name = strip_extension(input_filename)
            filename = generate_output_filename(base_name, "analysis")
        else:
            filename = generate_output_filename("tender", "analysis")
        
        # Full path to the output file
        output_file = output_path / filename
        
        logger.info(f"Generating output PDF: {output_file}")
        
        # Generate PDF
        self._create_pdf(key_points, output_file)
        
        return str(output_file)
    
    @error_handler
    def _create_pdf(self, key_points, output_file):
        """
        Create the PDF file with extracted key points.
        
        Args:
            key_points (dict): Dictionary containing extracted key points.
            output_file (Path): Output file path.
        """
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_file),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Content elements
            elements = []
            
            # Add title
            title = Paragraph("Tender Document Analysis", self.title_style)
            elements.append(title)
            
            # Add timestamp
            timestamp = Paragraph(
                f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                self.styles["Italic"]
            )
            elements.append(timestamp)
            elements.append(Spacer(1, 20))
            
            # Add summary table
            elements.append(Paragraph("Summary of Key Points", self.heading_style))
            elements.append(Spacer(1, 10))
            
            # Create a summary table
            summary_data = [
                ["Key Point", "Availability"],
            ]
            
            for key, content in key_points.items():
                availability = "Available" if content and "not available" not in content.lower() else "Not Available"
                summary_data.append([key, availability])
            
            summary_table = Table(summary_data, colWidths=[300, 150])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]))
            
            elements.append(summary_table)
            elements.append(Spacer(1, 30))
            
            # Add detailed sections for each key point
            for key, content in key_points.items():
                elements.append(Paragraph(f"{key}", self.heading_style))
                
                # Split content by lines and create paragraphs
                if content:
                    # Process content to identify list items
                    lines = content.split("\n")
                    current_paragraph = []
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            # Empty line - end previous paragraph if it exists
                            if current_paragraph:
                                para_text = " ".join(current_paragraph)
                                elements.append(Paragraph(para_text, self.normal_style))
                                current_paragraph = []
                        elif line.startswith(("- ", "• ", "* ")):
                            # This is a list item
                            # First end any current paragraph
                            if current_paragraph:
                                para_text = " ".join(current_paragraph)
                                elements.append(Paragraph(para_text, self.normal_style))
                                current_paragraph = []
                            
                            # Then add the list item
                            elements.append(Paragraph(f"• {line[2:]}", self.normal_style))
                        elif line.startswith(("#", "##", "###")) and ":" in line:
                            # This is a header
                            if current_paragraph:
                                para_text = " ".join(current_paragraph)
                                elements.append(Paragraph(para_text, self.normal_style))
                                current_paragraph = []
                            
                            # Extract header text
                            header_text = line.split(":", 1)[1].strip()
                            elements.append(Paragraph(header_text, self.styles["Heading3"]))
                        else:
                            # Regular line - add to current paragraph
                            current_paragraph.append(line)
                    
                    # Add any remaining paragraph text
                    if current_paragraph:
                        para_text = " ".join(current_paragraph)
                        elements.append(Paragraph(para_text, self.normal_style))
                else:
                    elements.append(Paragraph("Information not available in the document.", self.info_style))
                
                elements.append(Spacer(1, 20))
            
            # Build PDF
            doc.build(elements)
            logger.info(f"PDF generated successfully: {output_file}")
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise OutputError(f"Failed to generate PDF: {str(e)}") 