"""
Configuration utilities for the tender analyzer application.
"""

import os
import sys
from pathlib import Path
from loguru import logger


def setup_logging(level="INFO"):
    """
    Set up logging configuration for the application.
    
    Args:
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parents[2] / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file logger
    logger.add(
        logs_dir / "tender_analyzer_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # New file daily at midnight
        retention="7 days",  # Keep logs for a week
        level="DEBUG",  # Always record debug info to file
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        backtrace=True,
        diagnose=True
    )
    
    logger.debug(f"Logging initialized with level {level}")


def get_project_root():
    """
    Get the project root directory.
    
    Returns:
        Path: Path to the project root directory.
    """
    return Path(__file__).parents[2]


# Constants and configuration values
class Config:
    """Configuration constants for the application."""
    
    # Paths
    PROJECT_ROOT = get_project_root()
    OUTPUT_DIR = PROJECT_ROOT / "src" / "output"
    
    # OCR configuration
    OCR_LANG = "eng"
    OCR_DPI = 300
    
    # Chunking configuration
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # LLM configuration
    OLLAMA_MODEL = "llama3.2"
    OLLAMA_API_BASE = "http://localhost:11434"
    
    # Key points to extract
    KEY_POINTS = [
        "Deadline",
        "Project Requirement",
        "Cost",
        "Quality Checking",
    ]
    
    @classmethod
    def ensure_output_dir(cls):
        """Ensure the output directory exists."""
        cls.OUTPUT_DIR.mkdir(exist_ok=True, parents=True) 