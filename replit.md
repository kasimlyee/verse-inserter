# VerseInserter - Replit Environment Setup

## Overview

**VerseInserter** is a desktop GUI application for automated scripture insertion into Microsoft Word documents. It was designed to run on Windows with a graphical user interface (tkinter/ttkbootstrap).

**Current Version:** 1.0.0  
**Author:** Kasim Lyee  
**Company:** Softlite Inc.  
**License:** MIT

## Important Limitation ⚠️

**This application cannot run its GUI in the Replit environment** because:
- Replit is a cloud-based platform without a display server (X11)
- The application uses tkinter, which requires a graphical display
- It was designed specifically for local Windows desktop use

## Project Structure

```
verse-inserter/
├── verse_inserter/          # Main application package
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Main entry point for GUI
│   ├── version.py           # Version information
│   ├── models/              # Data models
│   │   ├── verse.py         # Verse, Reference, Translation models
│   │   ├── placeholder.py   # Placeholder model
│   │   └── document.py      # Document model
│   ├── core/                # Core business logic
│   │   ├── document_processor.py   # Word document processing
│   │   ├── placeholder_parser.py   # Placeholder detection
│   │   └── cache_manager.py        # Verse caching
│   ├── api/                 # API integration
│   │   ├── bible_api_client.py    # API.Bible client
│   │   └── api_exceptions.py      # API error classes
│   ├── ui/                  # GUI components (tkinter)
│   │   └── main_window.py         # Main application window
│   ├── config/              # Configuration
│   │   └── settings.py            # App settings & crypto
│   └── utils/               # Utilities
│       ├── logger.py              # Logging system
│       ├── validators.py          # Input validation
│       └── file_handler.py        # File operations
├── cli.py                   # CLI test script (Replit)
├── pyproject.toml           # Poetry dependencies
├── poetry.lock              # Locked dependencies
└── README.md                # Full documentation

```

## Technology Stack

- **Language:** Python 3.12
- **GUI Framework:** tkinter + ttkbootstrap
- **Document Processing:** python-docx
- **API Client:** aiohttp (async HTTP)
- **Caching:** diskcache
- **Security:** cryptography (API key encryption)
- **Package Manager:** Poetry

## Dependencies

All dependencies are managed via Poetry and include:
- `python-docx` - Word document manipulation
- `requests` / `aiohttp` - HTTP clients
- `ttkbootstrap` - Modern tkinter themes
- `pydantic` - Data validation
- `cryptography` - Secure key storage
- `tenacity` - Retry logic
- `diskcache` - Persistent caching
- `colorlog` - Colored logging
- `Pillow` - Image handling
- `pyinstaller` - Windows executable builder (v6.16.0)

## How to Use This Project

### Option 1: Build Windows Executable (Recommended for Distribution)

To create a standalone .exe file for Windows:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd verse-inserter
   ```

2. **Install Python 3.12-3.14:**
   - Download from [python.org](https://python.org)
   - PyInstaller requires Python 3.12-3.14

3. **Install Poetry:**
   ```bash
   pip install poetry
   ```

4. **Build the executable:**
   
   **Using Batch (Command Prompt):**
   ```cmd
   build_windows.bat
   ```
   
   **Using PowerShell:**
   ```powershell
   .\build_windows.ps1
   ```
   
   **Manual Build:**
   ```bash
   poetry install --no-root
   poetry run pyinstaller verse_inserter.spec --clean --noconfirm
   ```

5. **Run the executable:**
   - Find `dist\VerseInserter.exe`
   - Double-click to run
   - No Python installation required on target machine

**See BUILD.md for complete build documentation.**

### Option 2: Run Locally (Development)

For development and testing:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd verse-inserter
   ```

2. **Install Python 3.12-3.14:**
   - Download from [python.org](https://python.org)
   - Ensure Python 3.12-3.14 is installed

3. **Install Poetry:**
   ```bash
   pip install poetry
   ```

4. **Install dependencies:**
   ```bash
   poetry install --no-root
   ```

5. **Run the application:**
   ```bash
   poetry run python -m verse_inserter
   ```

6. **Configure API Key:**
   - Sign up at [API.Bible](https://scripture.api.bible)
   - Get a free API key
   - Enter it in the Settings dialog

### Option 3: Test Core Functionality (Replit)

In Replit, you can test that the core modules load correctly:

1. The workflow "VerseInserter Info" runs automatically
2. It verifies all modules import successfully
3. Tests basic placeholder parsing
4. Shows version and setup information

**Note:** This only tests module imports - the full GUI cannot run.

## Features

### Core Functionality
- **Automatic Verse Insertion:** Finds `{{John 3:16}}` style placeholders and replaces them with actual verse text
- **Multiple Translations:** Supports NIV, KJV, ESV, NKJV, NLT
- **Intelligent Caching:** Reduces API calls by caching verses locally
- **Format Preservation:** Maintains original document formatting
- **Batch Processing:** Handles multiple verses efficiently using async operations
- **Auto-backup:** Creates backup before processing

### User Interface (Desktop Only)
- Modern ttkbootstrap theme
- Real-time progress tracking
- Activity log viewer
- Settings management with encrypted API key storage
- Drag-and-drop support (future feature)

## API Integration

The application integrates with [API.Bible](https://scripture.api.bible):
- **Free Tier:** 100 requests/minute, 10,000/day
- **Authentication:** API key (encrypted locally)
- **Supported Translations:**
  - NIV (New International Version)
  - KJV (King James Version)
  - ESV (English Standard Version)
  - NKJV (New King James Version)
  - NLT (New Living Translation)

## Configuration

Settings are stored in `~/.verse_inserter/config.json` with encrypted API keys:

```json
{
  "api_key": "encrypted_value",
  "default_translation": "NIV",
  "enable_cache": true,
  "cache_ttl_days": 30,
  "auto_backup": true,
  "theme": "cosmo"
}
```

Environment variables (optional):
```bash
export VERSE_INSERTER_API_KEY="your-key"
export VERSE_INSERTER_DEFAULT_TRANSLATION="NIV"
```

## Development

### Testing in Replit

The `cli.py` script provides basic module testing:
```bash
python cli.py
```

This verifies:
- ✓ All modules import correctly
- ✓ Models are properly structured
- ✓ Core functionality is available
- ✓ Dependencies are installed

### Running Tests Locally

```bash
# Install dev dependencies
poetry install

# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=verse_inserter

# Code formatting
poetry run black verse_inserter/
poetry run isort verse_inserter/

# Linting
poetry run flake8 verse_inserter/
poetry run pylint verse_inserter/
```

## Architecture

### Design Patterns
- **Repository Pattern:** Separation of data access
- **Factory Pattern:** Object creation abstraction
- **Strategy Pattern:** Pluggable algorithms
- **Observer Pattern:** UI event handling
- **Singleton Pattern:** Global configuration

### Key Components

1. **DocumentProcessor:** Core engine for Word document manipulation
2. **PlaceholderParser:** Regex-based placeholder detection and validation
3. **BibleAPIClient:** Async HTTP client with retry logic
4. **CacheManager:** Persistent verse caching with TTL
5. **MainWindow:** tkinter GUI with ttkbootstrap styling

## Known Issues

1. **Replit Limitation:** GUI cannot display in cloud environment
2. **Windows-Specific:** Primarily tested on Windows OS
3. **Display Required:** Needs X11 or similar display server

## Future Enhancements

- Command-line mode for headless processing
- Web-based interface for cloud deployment
- Additional Bible translations
- Support for other document formats (PDF, HTML)
- Batch processing multiple documents
- Custom verse formatting templates

## Support

For issues or questions:
- **Email:** lyee@codewithlyee.com
- **GitHub:** https://github.com/kasimlyee/verse-inserter
- **Documentation:** https://docs.codewithlyee.com/verse-inserter

## License

MIT License - See LICENSE file for details.

---

## Recent Changes

### 2024-10-13 (Windows Build Setup)
- Installed PyInstaller 6.16.0 for Windows executable creation
- Created PyInstaller spec file with all dependencies configured
- Built Windows build automation scripts (batch and PowerShell)
- Created comprehensive BUILD.md documentation
- Updated Python version constraint for PyInstaller compatibility (>=3.12,<3.15)
- Added build instructions to documentation

### 2024-10-13 (Replit Setup)
- Installed Python 3.12 environment
- Installed all dependencies via Poetry
- Created missing module files (models, core, API)
- Restructured project to match expected package layout
- Created CLI test script for Replit environment
- Set up workflow for testing core functionality
- Documented limitations and local setup instructions

### Project Status
- ✅ Core modules: Working
- ✅ Dependencies: Installed
- ✅ Package structure: Corrected
- ✅ Windows build: Ready (PyInstaller configured)
- ❌ GUI: Cannot run in Replit (requires local display)
- ✅ Documentation: Complete

## User Preferences

None recorded yet. This section will track:
- Preferred Bible translations
- Default processing options
- Workflow preferences
- Custom configurations
