"""
File handling utilities.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import Union

from .logger import get_logger

logger = get_logger(__name__)


def create_backup(file_path: Union[str, Path]) -> Path:
    """
    Create a backup copy of a file.
    
    Args:
        file_path: Path to file to backup
        
    Returns:
        Path to backup file
        
    Raises:
        FileNotFoundError: If source file doesn't exist
        IOError: If backup creation fails
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_name(
        f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
    )
    
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        raise IOError(f"Failed to create backup: {e}")


def ensure_directory_exists(directory: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path
        
    Returns:
        Path object for the directory
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_safe_filename(filename: str) -> str:
    """
    Generate a safe filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename string
    """
    invalid_chars = '<>:"/\\|?*'
    safe_name = filename
    
    for char in invalid_chars:
        safe_name = safe_name.replace(char, '_')
    
    return safe_name


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes
    """
    return Path(file_path).stat().st_size


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
