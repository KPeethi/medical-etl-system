@echo off
REM Medical ETL System Insta# Install requirements
echo Installing Python packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python packages
    echo Trying to install core packages individually...
    pip install pandas numpy Pillow pytesseract pdf2image openpyxl py7zr rarfile python-dateutil
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install core packages
        pause
        exit /b 1
    )
)Script for Windows
REM Run this script as Administrator

echo ============================================
echo Medical ETL System Installation Script
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python version: %PYTHON_VERSION%

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing Python packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python packages
    pause
    exit /b 1
)

REM Test Tesseract installation
echo.
echo Testing Tesseract OCR installation...
python -c "import pytesseract; print('Tesseract version:', pytesseract.get_tesseract_version())" 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Tesseract OCR not found or not properly configured
    echo Please install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
    echo After installation, update the TESSERACT_CMD path in config\config.py
    echo.
) else (
    echo Tesseract OCR is properly installed and configured
)

REM Create necessary directories
echo Creating directories...
mkdir logs 2>nul
mkdir temp 2>nul
mkdir data 2>nul

echo.
echo ============================================
echo Installation completed!
echo ============================================
echo.
echo To run the ETL system:
echo 1. Activate virtual environment: venv\Scripts\activate
echo 2. Run dry test: python main.py source_folder dest_folder --dry-run
echo 3. Check logs in the 'logs' directory
echo.
echo For detailed usage instructions, see README.md
echo.
pause