"""
Helper utilities for the tender analyzer application.
"""

import os
import hashlib
from datetime import datetime
from pathlib import Path

def get_timestamp():
    """
    Get a formatted timestamp string.
    
    Returns:
        str: Formatted timestamp string (YYYY-MM-DD_HHMMSS).
    """
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def get_file_hash(file_path):
    """
    Generate a short hash for a file to use in output naming.
    
    Args:
        file_path (str or Path): Path to the file.
        
    Returns:
        str: Short hash of the file.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return "unknown"
    
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        # Read first 8KB for quick hashing
        chunk = f.read(8192)
        hasher.update(chunk)
    
    return hasher.hexdigest()[:8]


def generate_output_filename(input_filename, suffix="analyzed"):
    """
    Generate a filename for output based on input filename.
    
    Args:
        input_filename (str): Original input filename.
        suffix (str, optional): Suffix to add to filename. Defaults to "analyzed".
        
    Returns:
        str: Generated output filename.
    """
    base_name = Path(input_filename).stem
    timestamp = get_timestamp()
    return f"{base_name}_{suffix}_{timestamp}.pdf"


def strip_extension(filename):
    """
    Remove the extension from a filename.
    
    Args:
        filename (str): Filename with extension.
        
    Returns:
        str: Filename without extension.
    """
    return Path(filename).stem 