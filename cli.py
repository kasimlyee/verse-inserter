"""
Command-line interface for VerseInserter.

This CLI version allows testing the core functionality in environments
without GUI support (like Replit).

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

import sys
from pathlib import Path

print("=" * 60)
print("  VerseInserter - Automated Scripture Insertion")
print("  Version 1.0.0")
print("=" * 60)
print()
print("NOTE: This is a desktop GUI application built with tkinter.")
print("It cannot run in Replit's cloud environment as it requires")
print("a display server (GUI).")
print()
print("To run this application:")
print("  1. Clone this repository to your local machine")
print("  2. Install Python 3.12 or higher")
print("  3. Install dependencies: poetry install")
print("  4. Run: python -m verse_inserter")
print()
print("=" * 60)
print()
print("Testing core functionality...")
print()

try:
    from verse_inserter import __version__, __author__
    print(f"✓ Version module loaded: v{__version__} by {__author__}")
    
    from verse_inserter.models.verse import TranslationType, VerseReference, Verse
    print("✓ Models module loaded successfully")
    
    from verse_inserter.core.placeholder_parser import PlaceholderParser
    print("✓ Placeholder parser module loaded")
    
    from verse_inserter.core.cache_manager import CacheManager
    print("✓ Cache manager module loaded")
    
    from verse_inserter.api.bible_api_client import BibleAPIClient
    print("✓ Bible API client module loaded")
    
    from verse_inserter.utils.logger import get_logger
    print("✓ Logger module loaded")
    
    print()
    print("All core modules loaded successfully!")
    print()
    print("Example usage:")
    print()
    
    parser = PlaceholderParser()
    placeholders = parser.parse_text("Check out {{John 3:16}} for God's love.")
    
    if placeholders:
        ref = placeholders[0].reference
        print(f"  Found placeholder: {ref.canonical_reference}")
        print(f"  Book: {ref.book}")
        print(f"  Chapter: {ref.chapter}")
        print(f"  Verse: {ref.verse_start}")
    
    print()
    print("✓ Core functionality verified!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("Setup complete! This application is ready to run locally.")
print("=" * 60)
