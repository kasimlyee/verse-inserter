@echo off
REM Quick test runner for VerseInserter
REM Runs all tests and generates coverage report

echo ========================================
echo   VerseInserter Test Suite Runner
echo ========================================
echo.

REM Check if poetry is installed
poetry --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Poetry is not installed or not in PATH
    echo Please install Poetry first: https://python-poetry.org/docs/#installation
    pause
    exit /b 1
)

echo Installing dependencies...
poetry install --no-root
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Running tests with coverage...
echo.

poetry run pytest --cov=verse_inserter --cov-report=html --cov-report=term -v

if errorlevel 1 (
    echo.
    echo ========================================
    echo   Tests FAILED
    echo ========================================
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo   All Tests PASSED!
    echo ========================================
    echo.
    echo Coverage report generated: htmlcov\index.html
    echo.

    REM Ask if user wants to view coverage report
    set /p VIEW_REPORT="Open coverage report in browser? (y/n): "
    if /i "%VIEW_REPORT%"=="y" (
        start htmlcov\index.html
    )

    echo.
    pause
)
