@echo off
title Image Crop OCR Tool
cd /d %~dp0

:: Create virtual environment if not exists
if not exist .venv\Scripts\activate (
    echo Creating virtual environment...
    python -m venv .venv
)

:: Activate venv
call .venv\Scripts\activate

:: Install/update dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: Run app
echo.
echo Starting Image Crop OCR Tool...
python app.py

pause
