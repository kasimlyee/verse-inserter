# Building VerseInserter for Windows

This guide explains how to create a standalone Windows executable (.exe) for VerseInserter.

## Prerequisites

Before building, ensure you have:

1. **Python 3.12-3.14** installed
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Note: PyInstaller currently requires Python <3.15

2. **Poetry** installed
   - Install with: `pip install poetry`
   - Or follow the [official installation guide](https://python-poetry.org/docs/#installation)

3. **Windows Operating System**
   - The executable must be built on Windows to run on Windows
   - Tested on Windows 10 and Windows 11

## Quick Build (Recommended)

### Option 1: Using Batch File

1. Open Command Prompt in the project directory
2. Run the build script:
   ```cmd
   build_windows.bat
   ```

### Option 2: Using PowerShell

1. Open PowerShell in the project directory
2. Run the build script:
   ```powershell
   .\build_windows.ps1
   ```

The build process will:
- ✓ Install all dependencies
- ✓ Create the executable with PyInstaller
- ✓ Place the result in the `dist/` folder

**Output:** `dist\VerseInserter.exe`

## Manual Build

If you prefer to build manually:

```cmd
# 1. Install dependencies
poetry install --no-root

# 2. Build the executable
poetry run pyinstaller verse_inserter.spec --clean --noconfirm
```

## Build Configuration

The build is configured in `verse_inserter.spec`:

- **Entry Point:** `verse_inserter/__main__.py`
- **Mode:** Single-file executable (all dependencies bundled)
- **Console:** Disabled (GUI application, no console window)
- **Hidden Imports:** All required packages (tkinter, ttkbootstrap, python-docx, etc.)

### Customizing the Build

To modify the build, edit `verse_inserter.spec`:

#### Add an Icon
```python
exe = EXE(
    # ... other settings ...
    icon='path/to/icon.ico',  # Add this line
)
```

#### Change to Directory Mode (faster startup)
```python
# Comment out the current EXE block and use:
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VerseInserter',
    debug=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='VerseInserter',
)
```

#### Enable Console for Debugging
```python
exe = EXE(
    # ... other settings ...
    console=True,  # Change False to True
)
```

## Build Output

After building, you'll find:

```
dist/
└── VerseInserter.exe   # Standalone executable (~50-80 MB)

build/                   # Temporary build files (can be deleted)
```

## Distribution

To distribute the application:

### Single File Mode (Current)
- Simply share `dist\VerseInserter.exe`
- Users can run it directly without installation
- No dependencies required on target machine

### Directory Mode
- Share the entire `dist\VerseInserter\` folder
- Users run `VerseInserter\VerseInserter.exe`
- Faster startup time
- Larger distribution size

## Troubleshooting

### Build Fails with "Module Not Found"

Add the missing module to `hiddenimports` in `verse_inserter.spec`:

```python
hiddenimports=[
    # ... existing imports ...
    'your_missing_module',
],
```

### Executable Shows Console Window

Ensure `console=False` in `verse_inserter.spec`:

```python
exe = EXE(
    # ... other settings ...
    console=False,
)
```

### Large Executable Size

This is normal for PyInstaller. The exe includes:
- Python interpreter
- All dependencies
- Application code

To reduce size:
- Use directory mode instead of single-file
- Exclude unnecessary packages
- Enable UPX compression (already enabled)

### Application Doesn't Start

1. **Check Python version:** Must be 3.12-3.14
2. **Run from command line:** See detailed error messages
   ```cmd
   cd dist
   VerseInserter.exe
   ```
3. **Rebuild with console enabled** to see startup errors

## Testing the Executable

After building:

1. Navigate to the `dist` folder
2. Double-click `VerseInserter.exe`
3. The application should start with the GUI
4. Test core functionality:
   - Settings dialog
   - File selection
   - Document processing

## Advanced: Creating an Installer

To create a professional installer (optional):

1. **Using Inno Setup:**
   - Download [Inno Setup](https://jrsoftware.org/isinfo.php)
   - Create a script to package the exe
   - Generate Setup.exe installer

2. **Using NSIS:**
   - Download [NSIS](https://nsis.sourceforge.io/)
   - Create installer script
   - Build installer package

3. **Using WiX Toolset:**
   - Download [WiX](https://wixtoolset.org/)
   - Create MSI installer
   - Professional deployment option

## Build Automation

For CI/CD or automated builds:

```yaml
# Example GitHub Actions workflow
name: Build Windows Executable
on: [push]
jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install Poetry
        run: pip install poetry
      - name: Build
        run: .\build_windows.ps1
      - uses: actions/upload-artifact@v3
        with:
          name: VerseInserter
          path: dist/VerseInserter.exe
```

## Version Information

To add version info to the executable, create `version_info.txt`:

```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Softlite Inc.'),
        StringStruct(u'FileDescription', u'VerseInserter - Automated Scripture Insertion'),
        StringStruct(u'FileVersion', u'1.0.0'),
        StringStruct(u'InternalName', u'VerseInserter'),
        StringStruct(u'LegalCopyright', u'© 2024 Softlite Inc.'),
        StringStruct(u'OriginalFilename', u'VerseInserter.exe'),
        StringStruct(u'ProductName', u'VerseInserter'),
        StringStruct(u'ProductVersion', u'1.0.0')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

Then add to the spec file:
```python
exe = EXE(
    # ... other settings ...
    version='version_info.txt',
)
```

## Support

For build issues:
- **Email:** lyee@codewithlyee.com
- **GitHub Issues:** [verse-inserter/issues](https://github.com/kasimlyee/verse-inserter/issues)
- **Documentation:** [docs.codewithlyee.com/verse-inserter](https://docs.codewithlyee.com/verse-inserter)

---

**Last Updated:** October 2025  
**PyInstaller Version:** 6.16.0  
**Python Version:** 3.12-3.14
