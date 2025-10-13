@echo off
REM ============================================================
REM VerseInserter - Windows Build Script
REM ============================================================

echo.
echo ============================================================
echo   Building VerseInserter for Windows
echo ============================================================
echo.

REM Check if Poetry is installed
where poetry >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Poetry is not installed or not in PATH
    echo Please install Poetry first: https://python-poetry.org/docs/#installation
    pause
    exit /b 1
)

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.12 or higher
    pause
    exit /b 1
)

REM Install dependencies
echo [1/3] Installing dependencies...
poetry install --no-root
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Building executable with PyInstaller...
poetry run pyinstaller verse_inserter.spec --clean --noconfirm
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo [3/3] Build complete!
echo.
echo ============================================================
echo Executable created: dist\VerseInserter.exe
echo ============================================================
echo.
echo You can now run the application from:
echo   %CD%\dist\VerseInserter.exe
echo.
echo To distribute, copy the entire 'dist' folder or just the
echo VerseInserter.exe file (if using --onefile mode)
echo.
pause
