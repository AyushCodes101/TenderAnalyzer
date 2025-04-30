"""
Error handling utilities for the tender analyzer application.
"""

from functools import wraps
from loguru import logger

class TenderAnalyzerError(Exception):
    """Base exception class for all application-specific errors."""
    pass


class DocumentError(TenderAnalyzerError):
    """Exception raised for errors related to document handling."""
    pass


class ExtractionError(TenderAnalyzerError):
    """Exception raised for errors during text extraction."""
    pass


class ChunkingError(TenderAnalyzerError):
    """Exception raised for errors during text chunking."""
    pass


class AnalysisError(TenderAnalyzerError):
    """Exception raised for errors during LLM analysis."""
    pass


class OutputError(TenderAnalyzerError):
    """Exception raised for errors during output generation."""
    pass


def error_handler(func):
    """
    Decorator for handling exceptions in a consistent way.
    
    Args:
        func: The function to wrap with error handling.
        
    Returns:
        The wrapped function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TenderAnalyzerError as e:
            # Log and re-raise application-specific errors
            logger.error(f"{type(e).__name__}: {str(e)}")
            raise
        except Exception as e:
            # Wrap and re-raise other exceptions as application-specific errors
            logger.exception(f"Unexpected error in {func.__name__}:")
            error_type = TenderAnalyzerError
            if "extract" in func.__name__.lower():
                error_type = ExtractionError
            elif "chunk" in func.__name__.lower():
                error_type = ChunkingError
            elif "analy" in func.__name__.lower() or "extract_key" in func.__name__.lower():
                error_type = AnalysisError
            elif "output" in func.__name__.lower() or "generate" in func.__name__.lower():
                error_type = OutputError
            raise error_type(f"Error in {func.__name__}: {str(e)}") from e
    
    return wrapper 