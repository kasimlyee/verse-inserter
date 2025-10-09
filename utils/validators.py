"""
Input validation utilities.

Provides comprehensive validation functions for file paths,
configuration values, and user input.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

from pathlib import Path
from typing import Optional


def validate_file_path(
    path: Path,
    must_exist: bool = False,
    extension: Optional[str] = None,
) -> None:
    """
    Validate file path with optional existence and extension checks.
    
    Args:
        path: Path to validate
        must_exist: Whether file must exist
        extension: Required file extension (e.g., ".docx")
        
    Raises:
        FileNotFoundError: If must_exist=True and file doesn't exist
        ValueError: If extension doesn't match or path is invalid
    """
    if not isinstance(path, Path):
        path = Path(path)
    
    # Check extension
    if extension and path.suffix.lower() != extension.lower():
        raise ValueError(
            f"Invalid file extension: expected {extension}, got {path.suffix}"
        )
    
    # Check existence
    if must_exist and not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    # Check if path is a file (not directory)
    if path.exists() and not path.is_file():
        raise ValueError(f"Path is not a file: {path}")


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if format appears valid
    """
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Basic validation - API.Bible keys are typically hex strings
    api_key = api_key.strip()
    return len(api_key) >= 32 and api_key.replace("-", "").isalnum()


def validate_translation_name(name: str) -> bool:
    """
    Validate Bible translation name.
    
    Args:
        name: Translation name to validate
        
    Returns:
        True if valid translation name
    """
    valid_translations = ["NIV", "KJV", "ESV", "NKJV", "NLT"]
    return name.upper() in valid_translations