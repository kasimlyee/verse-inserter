# VerseInserter - Automated Scripture Insertion

**Version:** 1.0.0  
**Developer:** Kasim Lyee ([lyee@codewithlyee.com](mailto:lyee@codewithlyee.com))  
**Organization:** Softlite Inc.  
**License:** MIT

> *"Inserting Scripture Seamlessly into Your Words."*

---

## Overview

VerseInserter is a Windows desktop application that automatically inserts Bible verses into Microsoft Word documents. Built with Python architecture, it offers high performance, security, and reliability.

### Key Features

- **Automatic Verse Insertion**: Replaces `{{John 3:16}}` placeholders with actual scripture text
- **Multiple Translations**: Support for NIV, KJV, ESV, NKJV, and NLT
- **High Performance**: Processes 100+ verses in seconds using async operations
- **Intelligent Caching**: Minimizes API calls with multi-tier caching
- **Modern UI**: Beautiful, responsive interface built with ttkbootstrap
- **Secure**: Encrypted API key storage with cryptography
- **Real-time Progress**: Live status updates and comprehensive logging
- **Auto-backup**: Automatic document backup before processing

---

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Windows 10/11
- Poetry (for dependency management)
- API.Bible API key ([Get one free](https://scripture.api.bible))

### Installation

```bash
# Clone the repository
git clone https://github.com/kasimlyee/verse-inserter.git
cd verse-inserter

# Install dependencies using Poetry
poetry install

# Activate virtual environment
poetry shell

# Run the application
python -m verse_inserter
```

### Alternative Installation (pip)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m verse_inserter
```

---

## Usage Guide

### Basic Workflow

1. **Launch Application**: Run `python -m verse_inserter`
2. **Configure API Key**: Go to Settings and enter your API.Bible key
3. **Select Document**: Click "Browse for Document..." and choose your .docx file
4. **Choose Translation**: Select your preferred Bible translation
5. **Process**: Click "Process Document" and wait for completion
6. **Review**: Check the output file (original_filled.docx) in the same directory

### Placeholder Format

Use double curly braces to mark verses for insertion:

```
{{John 3:16}}
{{Genesis 1:1-3}}
{{Psalm 23:1}}
{{1 Corinthians 13:4-7}}
```

### Example Document

**Before:**
```
The Bible says {{John 3:16}}, which demonstrates God's love.
```

**After:**
```
The Bible says John 3:16 — For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life., which demonstrates God's love.
```

---

## Architecture

### Project Structure

```
verse_inserter/
├── verse_inserter/           # Main application package
│   ├── core/                 # Core business logic
│   │   ├── document_processor.py
│   │   ├── verse_fetcher.py
│   │   ├── placeholder_parser.py
│   │   ├── cache_manager.py
│   │   └── formatter.py
│   ├── api/                  # API layer
│   │   ├── bible_api_client.py
│   │   ├── api_exceptions.py
│   │   └── rate_limiter.py
│   ├── ui/                   # User interface
│   │   ├── main_window.py
│   │   └── widgets/
│   ├── config/               # Configuration
│   │   ├── settings.py
│   │   ├── constants.py
│   │   └── crypto.py
│   ├── utils/                # Utilities
│   │   ├── logger.py
│   │   ├── validators.py
│   │   └── file_handler.py
│   └── models/               # Data models
│       ├── verse.py
│       ├── placeholder.py
│       └── document.py
├── tests/                    # Test suite
├── docs/                     # Documentation
└── scripts/                  # Build scripts
```

### Design Patterns

- **Repository Pattern**: Separation of data access logic
- **Factory Pattern**: Object creation abstraction
- **Strategy Pattern**: Pluggable algorithm selection
- **Observer Pattern**: Event-driven UI updates
- **Singleton Pattern**: Global configuration management

---

## Configuration

### Settings File

Configuration is stored in `~/.verse_inserter/config.json`:

```json
{
  "api_key": "encrypted_key_here",
  "default_translation": "NIV",
  "enable_cache": true,
  "cache_ttl_days": 30,
  "auto_backup": true,
  "theme": "cosmo",
  "max_concurrent_requests": 5
}
```

### Environment Variables

You can also use environment variables (prefixed with `VERSE_INSERTER_`):

```bash
export VERSE_INSERTER_API_KEY="your-api-key"
export VERSE_INSERTER_DEFAULT_TRANSLATION="NIV"
export VERSE_INSERTER_ENABLE_CACHE=true
```

---

## API Setup

### Getting an API Key

1. Visit [API.Bible](https://scripture.api.bible)
2. Click "Sign Up" and create a free account
3. Navigate to "API Keys" in your dashboard
4. Generate a new API key
5. Copy the key and paste it into VerseInserter Settings

### API Limits

- **Free Tier**: 100 requests/minute, 10,000 requests/day
- **Pro Tier**: 1,000 requests/minute, unlimited daily requests

VerseInserter's intelligent caching dramatically reduces API usage.

---



## Building & Distribution

### Building Executable

```bash
# Using PyInstaller
poetry run python scripts/build_exe.py

# Output: dist/VerseInserter.exe
```

### Creating Installer

```bash
# Using Inno Setup
iscc scripts/create_installer.iss

# Output: dist/VerseInserter_Setup.exe
```

### Installer Features

- Silent installation option
- Custom icon and branding
- Start