@echo off
title Build Image Crop OCR Installer
cd /d %~dp0

:: ── 1. Activate venv (or create if missing) ──
if not exist .venv\Scripts\activate (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate

:: ── 2. Install dependencies ──
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

:: ── 3. Build executable with PyInstaller ──
echo.
echo Building executable with PyInstaller...
pyinstaller --onefile --windowed --name "ImageCropOCR" --icon icon.ico --add-data "icon.ico;." --add-data "icon.png;." app.py

:: ── 4. Check result ──
if exist dist\ImageCropOCR.exe (
    echo.
    echo ========================================
    echo Build successful!
    echo Executable: dist\ImageCropOCR.exe
    echo File size:
    wc -c dist\ImageCropOCR.exe 2>nul || dir dist\ImageCropOCR.exe
    echo ========================================
    echo.
    echo To create a setup package, install Inno Setup
    echo and use the provided installer.iss script.
) else (
    echo.
    echo Build FAILED! Check errors above.
)

pause
