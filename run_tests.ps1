#!/usr/bin/env pwsh
# Quick test runner for VerseInserter (PowerShell)
# Runs all tests and generates coverage report

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VerseInserter Test Suite Runner" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if poetry is installed
try {
    $poetryVersion = poetry --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Poetry not found" }
    Write-Host "Poetry detected: $poetryVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Poetry is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Poetry first: https://python-poetry.org/docs/#installation" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
poetry install --no-root

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Running tests with coverage..." -ForegroundColor Yellow
Write-Host ""

poetry run pytest --cov=verse_inserter --cov-report=html --cov-report=term -v

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  Tests FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  All Tests PASSED!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Coverage report generated: htmlcov\index.html" -ForegroundColor Cyan
    Write-Host ""

    # Ask if user wants to view coverage report
    $viewReport = Read-Host "Open coverage report in browser? (y/n)"
    if ($viewReport -eq "y" -or $viewReport -eq "Y") {
        Start-Process "htmlcov\index.html"
    }

    Write-Host ""
    Read-Host "Press Enter to exit"
}
