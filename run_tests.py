#!/usr/bin/env python3
"""
Script to run all unit tests for the tender analyzer application.
"""

import os
import sys
import unittest
from loguru import logger

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Configure logging
logger.remove()  # Remove default handler
logger.add(sys.stderr, level="ERROR")  # Only show errors during tests


def run_tests():
    """
    Discover and run all tests in the tests directory.
    
    Returns:
        bool: True if all tests passed, False otherwise.
    """
    # Discover all tests
    start_dir = os.path.join(os.path.dirname(__file__), "tests")
    test_suite = unittest.defaultTestLoader.discover(start_dir, pattern="test_*.py")
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return True if successful, False otherwise
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running Tender Analyzer tests...")
    
    success = run_tests()
    
    if success:
        print("\nAll tests passed successfully!")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1) 