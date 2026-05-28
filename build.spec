# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller build spec for Image Crop OCR.
Usage:
    pyinstaller build.spec
"""

import sys
import os
from pathlib import Path

block_cipher = None

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
ICON = str(ROOT / "icon.ico")
DATA_FILES = [(str(ROOT / "icon.ico"), "."), (str(ROOT / "icon.png"), ".")]

# ── Tesseract auto-detect ──────────────────────────────────────────────────
# Include tessdata if found next to tesseract.exe
for _base in [
    r"C:\Program Files\Tesseract-OCR",
    r"C:\Program Files (x86)\Tesseract-OCR",
]:
    tess_dir = Path(_base)
    if tess_dir.exists():
        # include tesseract.exe
        for f in ["tesseract.exe", "*.dll"]:
            p = tess_dir / f
            if p.exists() or "*" in f:
                DATA_FILES.append((str(tess_dir), "tesseract-ocr"))
        break

a = Analysis(
    ['app.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=DATA_FILES,
    hiddenimports=[
        'PIL', 'PIL._imaging', 'PIL.Image', 'PIL.ImageEnhance', 'PIL.ImageOps',
        'pytesseract', 'mss', 'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ImageCropOCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON,
)

# Create a one-folder build (you can also use COLLECT for one-file)
COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ImageCropOCR',
)
