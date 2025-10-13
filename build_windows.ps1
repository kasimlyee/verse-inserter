# ============================================================
# VerseInserter - Windows Build Script (PowerShell)
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Building VerseInserter for Windows" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Poetry is installed
if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Poetry is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Poetry first: https://python-poetry.org/docs/#installation"
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.12-3.14"
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies
Write-Host "[1/3] Installing dependencies..." -ForegroundColor Yellow
poetry install --no-root
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[2/3] Building executable with PyInstaller..." -ForegroundColor Yellow
poetry run pyinstaller verse_inserter.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[3/3] Build complete!" -ForegroundColor Green
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Executable created: dist\VerseInserter.exe" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now run the application from:"
Write-Host "  $PWD\dist\VerseInserter.exe" -ForegroundColor Yellow
Write-Host ""
Write-Host "To distribute, copy the entire 'dist' folder or just the"
Write-Host "VerseInserter.exe file (if using --onefile mode)"
Write-Host ""
Read-Host "Press Enter to exit"
