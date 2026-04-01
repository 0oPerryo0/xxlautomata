"""OCR utilities for reading text from screenshots (used for stage navigation)."""

from typing import Optional, Tuple
import numpy as np

try:
    import pytesseract
    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False

from utils.logger import get_logger

log = get_logger("ocr")


def find_text_position(
    screenshot: np.ndarray,
    text: str,
    lang: str = "eng",
    confidence: int = 60,
) -> Optional[Tuple[int, int]]:
    """
    Search the screenshot for a region containing `text` (case-insensitive).
    Returns the (x, y) center of the first matching word/block, or None.

    Requires pytesseract + Tesseract OCR installed:
        pip install pytesseract
        https://github.com/UB-Mannheim/tesseract/wiki  (Windows installer)
    """
    if not _TESSERACT_AVAILABLE:
        log.warning("pytesseract not installed — OCR stage search unavailable. "
                    "Run: pip install pytesseract")
        return None

    import cv2
    # Convert to RGB for tesseract
    rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)

    try:
        data = pytesseract.image_to_data(
            rgb,
            lang=lang,
            output_type=pytesseract.Output.DICT,
        )
    except Exception as e:
        log.error(f"OCR failed: {e}")
        return None

    target = text.strip().lower()
    for i, word in enumerate(data["text"]):
        if not word:
            continue
        conf = int(data["conf"][i])
        if conf < confidence:
            continue
        if target in word.strip().lower():
            x = data["left"][i] + data["width"][i] // 2
            y = data["top"][i] + data["height"][i] // 2
            log.debug(f"OCR found '{word}' at ({x}, {y}) conf={conf}")
            return x, y

    return None


def read_text_in_region(
    screenshot: np.ndarray,
    x: int,
    y: int,
    w: int,
    h: int,
    lang: str = "eng",
) -> str:
    """
    Run OCR on a cropped region of the screenshot and return the raw text.
    Useful for reading currency amounts, timers, etc.
    """
    if not _TESSERACT_AVAILABLE:
        log.warning("pytesseract not installed — OCR unavailable")
        return ""

    import cv2
    crop = screenshot[y: y + h, x: x + w]
    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    try:
        return pytesseract.image_to_string(rgb, lang=lang).strip()
    except Exception as e:
        log.error(f"OCR region read failed: {e}")
        return ""
