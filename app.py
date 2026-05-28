"""
Image Crop OCR Tool — PyQt6 Modern UI
Capture screen areas or load images, then extract text with Tesseract OCR.
"""

import os
import platform
import sys
import threading
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QTextEdit, QFileDialog,
    QMessageBox, QFrame, QSizePolicy, QScrollArea,
)
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QObject
from PyQt6.QtGui import (
    QPixmap, QImage, QPainter, QColor, QFont, QPen, QKeySequence,
    QClipboard, QIcon, QFontDatabase, QAction,
)

import pytesseract
from PIL import Image, ImageEnhance, ImageOps
import mss


# ---------------------------------------------------------------------------
# Tesseract path
# ---------------------------------------------------------------------------
if platform.system().lower() == "windows":
    for _p in [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]:
        if os.path.exists(_p):
            pytesseract.pytesseract.tesseract_cmd = _p
            break


# ---------------------------------------------------------------------------
# Stylesheet
# ---------------------------------------------------------------------------
STYLE = """
QMainWindow, QWidget {
    background-color: #0e0e12;
    color: #d4d4d8;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}
#headerBar {
    background-color: #13131a;
    border-bottom: 1px solid #1e1e2a;
}
#leftCard, #rightCard {
    background-color: #16161e;
    border: 1px solid #23233a;
    border-radius: 12px;
}
#accentBtn {
    background-color: #7c5cfc;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 22px;
    font-weight: 600;
    font-size: 13px;
}
#accentBtn:hover { background-color: #6a4be0; }
#accentBtn:pressed { background-color: #5a3ec8; }
#secBtn {
    background-color: #1e1e2e;
    color: #a0a0b0;
    border: 1px solid #2a2a40;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 13px;
}
#secBtn:hover { background-color: #252538; color: #d4d4d8; border-color: #3a3a55; }
#ghostBtn {
    background-color: transparent;
    color: #808090;
    border: 1px solid #2a2a40;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
}
#ghostBtn:hover { background-color: #1e1e2e; color: #d4d4d8; }
QComboBox {
    background-color: #1e1e2e;
    color: #d4d4d8;
    border: 1px solid #2a2a40;
    border-radius: 8px;
    padding: 8px 14px;
    min-width: 110px;
    font-size: 13px;
}
QComboBox:hover { border-color: #7c5cfc; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow { image: none; margin-right: 10px; }
QComboBox QAbstractItemView {
    background-color: #1a1a28;
    color: #d4d4d8;
    selection-background-color: #7c5cfc;
    selection-color: white;
    border: 1px solid #2a2a40;
    border-radius: 6px;
    padding: 4px;
}
QTextEdit {
    background-color: #111118;
    color: #c8c8d0;
    border: 1px solid #23233a;
    border-radius: 10px;
    padding: 12px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 13px;
    selection-background-color: #7c5cfc;
    selection-color: white;
}
QScrollBar:vertical {
    background: #111118;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2a2a40;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #3a3a55; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
#statusLabel {
    color: #505068;
    font-size: 12px;
    padding: 4px 12px;
}
#sectionTitle {
    color: #606078;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 10px 14px 4px 14px;
}
#divider {
    background-color: #1e1e2a;
    max-height: 1px;
    min-height: 1px;
}
#previewArea {
    background-color: #111118;
    border: 2px dashed #23233a;
    border-radius: 10px;
}
"""


# ---------------------------------------------------------------------------
# Helper: PIL Image → QPixmap
# ---------------------------------------------------------------------------
def pil_to_pixmap(img: Image.Image) -> QPixmap:
    rgb = img.convert("RGB")
    data = rgb.tobytes()
    qimg = QImage(data, rgb.width, rgb.height, 3 * rgb.width, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg)


# ---------------------------------------------------------------------------
# Screen-capture overlay (fullscreen)
# ---------------------------------------------------------------------------
class CaptureOverlay(QWidget):
    region_captured = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setCursor(Qt.CursorShape.CrossCursor)

        self._start: Optional[QPoint] = None
        self._end: Optional[QPoint] = None
        self._screenshot: Optional[QPixmap] = None
        self._pil_screenshot: Optional[Image.Image] = None

        with mss.mss() as sct:
            shot = sct.grab(sct.monitors[0])
            pil = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
            self._pil_screenshot = pil
            self._screenshot = pil_to_pixmap(pil)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.showFullScreen()
        self.setFocus()

    def paintEvent(self, event):
        if self._screenshot is None:
            return
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._screenshot)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        if self._start and self._end:
            rect = QRect(self._start, self._end).normalized()
            painter.setClipRect(rect)
            painter.drawPixmap(0, 0, self._screenshot)
            painter.setClipping(False)
            painter.setPen(QPen(QColor("#00ff41"), 2, Qt.PenStyle.SolidLine))
            painter.drawRect(rect)
            for pt in [rect.topLeft(), rect.topRight(), rect.bottomLeft(), rect.bottomRight()]:
                painter.fillRect(pt.x() - 4, pt.y() - 4, 8, 8, QColor("#00ff41"))

        painter.setPen(QColor("#00ff41"))
        painter.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        text = "DRAG TO SELECT   |   ESC TO CANCEL"
        tw = painter.fontMetrics().horizontalAdvance(text)
        x = (self.width() - tw) // 2
        painter.fillRect(x - 16, 12, tw + 32, 34, QColor(10, 10, 15, 220))
        painter.drawText(x, 34, text)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.pos()
            self._end = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        if self._start:
            self._end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._start:
            self._end = event.pos()
            rect = QRect(self._start, self._end).normalized()
            self.close()
            if rect.width() < 5 or rect.height() < 5:
                self.region_captured.emit(None)
                return
            cropped = self._pil_screenshot.crop((rect.x(), rect.y(), rect.right(), rect.bottom()))
            self.region_captured.emit(cropped)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            self.region_captured.emit(None)


# ---------------------------------------------------------------------------
# Worker thread signal helper
# ---------------------------------------------------------------------------
class OcrSignals(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Crop OCR")
        self.setMinimumSize(960, 640)
        self.resize(1080, 700)
        self._image: Optional[Image.Image] = None
        self._overlay: Optional[CaptureOverlay] = None

        # Set window icon
        icon_path = Path(__file__).parent / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._build_ui()
        self.setStyleSheet(STYLE)

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── HEADER ──────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("headerBar")
        header.setFixedHeight(56)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        # Logo
        logo_icon = QLabel("OCR")
        logo_icon.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        logo_icon.setStyleSheet("color: #7c5cfc; background: transparent;")
        header_layout.addWidget(logo_icon)

        logo_text = QLabel("  Image Crop OCR")
        logo_text.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        logo_text.setStyleSheet("color: #e0e0e8; background: transparent;")
        header_layout.addWidget(logo_text)

        header_layout.addStretch()

        lang_label = QLabel("Language")
        lang_label.setStyleSheet("color: #606078; font-size: 12px; background: transparent;")
        header_layout.addWidget(lang_label)
        header_layout.addSpacing(6)

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "Bangla", "Bangla + English"])
        self.lang_map = {"English": "eng", "Bangla": "ben", "Bangla + English": "ben+eng"}
        header_layout.addWidget(self.lang_combo)

        header_layout.addSpacing(12)

        extract_btn = QPushButton("  ⚡ Extract Text")
        extract_btn.setObjectName("accentBtn")
        extract_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        extract_btn.clicked.connect(self._extract_text)
        header_layout.addWidget(extract_btn)

        root_layout.addWidget(header)

        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.Shape.HLine)
        root_layout.addWidget(div)

        # ── TOOLBAR ─────────────────────────────────────────────────
        toolbar = QFrame()
        toolbar.setStyleSheet("background: transparent; border: none;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(20, 12, 20, 8)

        open_btn = QPushButton("  📁  Open")
        open_btn.setObjectName("secBtn")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(self._open_image)
        tb_layout.addWidget(open_btn)

        capture_btn = QPushButton("  📷  Capture")
        capture_btn.setObjectName("secBtn")
        capture_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        capture_btn.clicked.connect(self._capture_screen)
        tb_layout.addWidget(capture_btn)

        paste_btn = QPushButton("  📋  Paste")
        paste_btn.setObjectName("secBtn")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(self._paste_clipboard)
        tb_layout.addWidget(paste_btn)

        icon_btn = QPushButton("  ®  To Icon")
        icon_btn.setObjectName("secBtn")
        icon_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        icon_btn.clicked.connect(self._convert_to_icon)
        tb_layout.addWidget(icon_btn)

        clear_btn = QPushButton("  🗑  Clear")
        clear_btn.setObjectName("secBtn")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_all)
        tb_layout.addWidget(clear_btn)

        tb_layout.addStretch()
        root_layout.addWidget(toolbar)

        # ── BODY ────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(20, 4, 20, 8)
        body_layout.setSpacing(12)

        # Left card: image preview
        left_card = QFrame()
        left_card.setObjectName("leftCard")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        left_header = QLabel("  Image Preview")
        left_header.setObjectName("sectionTitle")
        left_header.setFixedHeight(32)
        left_layout.addWidget(left_header)

        self.preview_label = QLabel()
        self.preview_label.setObjectName("previewArea")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_label.setMinimumSize(320, 200)
        self._set_preview_placeholder()
        left_layout.addWidget(self.preview_label)

        body_layout.addWidget(left_card, stretch=3)

        # Right card: extracted text
        right_card = QFrame()
        right_card.setObjectName("rightCard")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        rh_row = QHBoxLayout()
        rh_row.setContentsMargins(14, 10, 14, 0)
        rh_title = QLabel("Extracted Text")
        rh_title.setObjectName("sectionTitle")
        rh_title.setContentsMargins(0, 0, 0, 0)
        rh_row.addWidget(rh_title)
        rh_row.addStretch()

        copy_btn = QPushButton("📋 Copy")
        copy_btn.setObjectName("ghostBtn")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_text)
        rh_row.addWidget(copy_btn)
        right_layout.addLayout(rh_row)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(False)
        self.output_text.setPlaceholderText("Extracted text will appear here...")
        right_layout.addWidget(self.output_text)

        body_layout.addWidget(right_card, stretch=2)

        root_layout.addWidget(body, stretch=1)

        # ── STATUS BAR ──────────────────────────────────────────────
        status = QFrame()
        status.setFixedHeight(32)
        status.setStyleSheet("background: #0e0e12; border-top: 1px solid #1a1a28;")
        st_layout = QHBoxLayout(status)
        st_layout.setContentsMargins(16, 0, 16, 0)

        self.status_label = QLabel("  ℹ  Ready")
        self.status_label.setObjectName("statusLabel")
        st_layout.addWidget(self.status_label)
        st_layout.addStretch()

        dark_label = QLabel("🌙 Dark Mode")
        dark_label.setStyleSheet("color: #505068; font-size: 12px; background: transparent;")
        st_layout.addWidget(dark_label)

        root_layout.addWidget(status)

    # ------------------------------------------------------------------ Helpers
    def _set_preview_placeholder(self):
        self.preview_label.setText(
            '<div style="text-align:center; color:#404058;">'
            '<div style="font-size:48px; margin-bottom:12px;">🖼</div>'
            '<div style="font-size:15px; font-weight:600; color:#505068;">No image selected</div>'
            '<div style="font-size:12px; margin-top:6px; color:#3a3a50;">'
            'Click "Open Image" or "Capture Screen"<br>to get started</div>'
            '</div>'
        )
        self.preview_label.setStyleSheet(
            "#previewArea { background-color: #111118; border: 2px dashed #23233a; border-radius: 10px; }"
        )

    def _set_status(self, text: str):
        self.status_label.setText(f"  {text}")

    def _pil_to_pixmap_scaled(self, img: Image.Image, max_w: int, max_h: int) -> QPixmap:
        iw, ih = img.size
        scale = min(max_w / iw, max_h / ih, 1.0)
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
        resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
        return pil_to_pixmap(resized)

    # ------------------------------------------------------------------ Actions
    def _open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp);;All (*)"
        )
        if not path:
            return
        try:
            img = Image.open(path)
            self._image = ImageOps.exif_transpose(img).convert("RGB")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot open image.\n\n{e}")
            return
        self._show_image(self._image)
        self._set_status(f"✅ Loaded: {Path(path).name}")

    def _capture_screen(self):
        self._overlay = CaptureOverlay()
        self._overlay.region_captured.connect(self._on_capture_done)

    def _on_capture_done(self, img):
        self._overlay = None
        if img is None:
            self._set_status("Capture cancelled.")
            return
        self._image = img
        self._show_image(img)
        self._set_status("✅ Screen captured. Drag to crop & extract.")

    def _paste_clipboard(self):
        clipboard = QApplication.clipboard()
        pixmap = clipboard.pixmap()
        if pixmap.isNull():
            self._set_status("⚠ No image in clipboard.")
            return
        try:
            qimg = pixmap.toImage()
            b = qimg.bits().asstring(qimg.sizeInBytes())
            pil = Image.frombuffer("RGB", (qimg.width(), qimg.height()), b, "raw", "RGB", qimg.bytesPerLine(), 1)
            self._image = pil.convert("RGB")
            self._show_image(self._image)
            self._set_status("✅ Pasted from clipboard.")
        except Exception as e:
            self._set_status(f"⚠ Paste failed: {e}")

    def _show_image(self, img: Image.Image):
        pm = self._pil_to_pixmap_scaled(img, 800, 600)
        self.preview_label.setPixmap(pm)
        self.preview_label.setStyleSheet(
            "#previewArea { background-color: #111118; border: 2px solid #23233a; border-radius: 10px; }"
        )

    def _copy_text(self):
        text = self.output_text.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Empty", "Nothing to copy.")
            return
        QApplication.clipboard().setText(text)
        self._set_status("✅ Copied to clipboard.")

    def _clear_all(self):
        self._image = None
        self._set_preview_placeholder()
        self.output_text.clear()
        self._set_status("✅ Cleared.")

    # ------------------------------------------------------------------ Icon Converter
    def _convert_to_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select image to convert to icon", "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All (*)"
        )
        if not path:
            return
        try:
            img = Image.open(path).resize((256, 256), Image.Resampling.LANCZOS)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot open image.\n\n{e}")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save icon as", Path(path).stem + ".ico",
            "Icon (*.ico);;All (*)"
        )
        if not save_path:
            return
        try:
            img.save(save_path, format="ICO", sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
            self._set_status(f"✅ Icon saved: {Path(save_path).name}")
            QMessageBox.information(
                self, "Icon Created",
                f"Icon saved successfully!\n\n{Path(save_path).name}\n\n"
                "You can now use this .ico file for:\n"
                "\u2022 Windows app shortcuts\n"
                "\u2022 Folder icons\n"
                "\u2022 PyInstaller packaging (use --icon=path.ico)"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save icon.\n\n{e}")

    # ------------------------------------------------------------------ OCR
    def _extract_text(self):
        if self._image is None:
            QMessageBox.warning(self, "No Image", "Please open or capture an image first.")
            return

        self._set_status("⏳ Extracting text...")
        QApplication.processEvents()

        lang = self.lang_map.get(self.lang_combo.currentText(), "eng")
        img = self._image.copy()

        gray = img.convert("L")
        w, h = gray.size
        if max(w, h) < 1400:
            gray = gray.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
        gray = ImageEnhance.Contrast(gray).enhance(1.8)
        gray = ImageEnhance.Sharpness(gray).enhance(1.5)

        signals = OcrSignals()
        signals.finished.connect(self._ocr_done)
        signals.error.connect(self._ocr_error)

        def run():
            try:
                text = pytesseract.image_to_string(gray, lang=lang, config="--oem 3 --psm 6")
                signals.finished.emit(text.strip())
            except pytesseract.TesseractNotFoundError:
                signals.error.emit("NOTFOUND")
            except pytesseract.TesseractError as e:
                signals.error.emit(f"LANG:{e}")
            except Exception as e:
                signals.error.emit(f"ERR:{e}")

        threading.Thread(target=run, daemon=True).start()

    def _ocr_done(self, text: str):
        self.output_text.setPlainText(text)
        n = len(text)
        self._set_status(f"✅ Extracted {n} characters." if n else "✅ No text detected.")

    def _ocr_error(self, err: str):
        if err == "NOTFOUND":
            QMessageBox.critical(
                self, "Tesseract Not Found",
                "Tesseract OCR is not installed.\n\n"
                "Install from:\nhttps://github.com/UB-Mannheim/tesseract/wiki\n"
                "Default: C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
            )
            self._set_status("❌ Tesseract not found.")
        elif err.startswith("LANG:"):
            QMessageBox.critical(self, "Language Error", err[5:])
            self._set_status("❌ Language pack missing.")
        else:
            QMessageBox.critical(self, "OCR Error", err)
            self._set_status("❌ OCR failed.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    icon_path = Path(__file__).parent / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
