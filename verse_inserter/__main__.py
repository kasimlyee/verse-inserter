"""
Application entry point for VerseInserter.

Main entry module that initializes the application, handles startup
configuration, and launches the UI with comprehensive error handling.

Author: Kasim Lyee <lyee@codewithlyee.com>
Organization: Softlite Inc.
License: Proprietary - All Rights Reserved

Usage:
    python -m verse_inserter
    or
    verse-inserter (if installed via Poetry)
"""

import sys
import traceback
from pathlib import Path

from config.settings import Settings
from ui.main_window import MainWindow
from utils.logger import get_logger
from version import __version__, __author__, __email__

# Initialize logger
logger = get_logger(__name__)


def setup_exception_handler() -> None:
    """
    Configure global exception handler for unhandled exceptions.
    
    Ensures all uncaught exceptions are logged and displayed to user
    in a friendly manner rather than crashing silently.
    """
    def exception_handler(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow keyboard interrupt to exit normally
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log the exception
        logger.critical(
            "Unhandled exception occurred",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # Format error message
        error_msg = "".join(traceback.format_exception(
            exc_type, exc_value, exc_traceback
        ))
        
        # Display error dialog if UI is available
        try:
            from tkinter import messagebox
            messagebox.showerror(
                "Critical Error",
                f"An unexpected error occurred:\n\n{exc_value}\n\n"
                f"Please check the log files for details."
            )
        except Exception:
            # If UI is not available, print to console
            print(f"CRITICAL ERROR: {error_msg}", file=sys.stderr)
    
    sys.excepthook = exception_handler


def check_dependencies() -> bool:
    """
    Verify all required dependencies are available.
    
    Returns:
        True if all dependencies present, False otherwise
    """
    required_modules = [
        ("docx", "python-docx"),
        ("requests", "requests"),
        ("ttkbootstrap", "ttkbootstrap"),
        ("cryptography", "cryptography"),
        ("pydantic", "pydantic"),
        ("diskcache", "diskcache"),
    ]
    
    missing = []
    
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        logger.error(f"Missing required dependencies: {', '.join(missing)}")
        print(
            f"ERROR: Missing required packages:\n"
            f"  {', '.join(missing)}\n\n"
            f"Please install using:\n"
            f"  poetry install\n"
            f"or\n"
            f"  pip install {' '.join(missing)}",
            file=sys.stderr
        )
        return False
    
    return True


def print_banner() -> None:
    """Print application banner to console."""
    banner = f"""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║              VerseInserter v{__version__}             ║
    ║                                                       ║
    ║     Automated Scripture Insertion for Word Docs       ║
    ║                                                       ║
    ║     Developer: {__author__:<35}                       ║
    ║     Email: {__email__:<39}                            ║
    ║     Company: Softlite Inc.                            ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """
    print(banner)


def main() -> int:
    """
    Main application entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Print banner
        print_banner()
        
        # Setup exception handler
        setup_exception_handler()
        
        # Check dependencies
        logger.info("Checking dependencies...")
        if not check_dependencies():
            return 1
        
        # Load settings
        logger.info("Loading application settings...")
        settings = Settings()
        
        # Initialize UI
        logger.info("Initializing user interface...")
        app = MainWindow(settings)
        
        # Start application event loop
        logger.info("Starting application...")
        app.mainloop()
        
        logger.info("Application closed normally")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 130  # Standard exit code for SIGINT
        
    except Exception as e:
        logger.critical(f"Fatal error during startup: {e}", exc_info=True)
        print(f"\nFATAL ERROR: {e}", file=sys.stderr)
        return 1
    
    finally:
        logger.info("Cleanup completed")


if __name__ == "__main__":
    sys.exit(main())
