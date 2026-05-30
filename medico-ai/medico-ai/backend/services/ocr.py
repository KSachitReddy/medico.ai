"""
OCR service — tries Tesseract first, falls back to EasyOCR.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional

from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

# ── lazy singletons ──────────────────────────────────────────────────────────
_easyocr_reader = None


def _get_easyocr():
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr  # type: ignore
            _easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        except Exception as e:
            logger.warning(f"EasyOCR unavailable: {e}")
    return _easyocr_reader


# ── image pre-processing ─────────────────────────────────────────────────────

def _preprocess(img: Image.Image) -> Image.Image:
    """Enhance contrast / sharpness for better OCR accuracy."""
    img = img.convert("L")  # greyscale
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    img = img.filter(ImageFilter.MedianFilter())
    return img


# ── public API ───────────────────────────────────────────────────────────────

def extract_text_from_image(image_bytes: bytes, engine: str = "auto") -> dict:
    """
    Extract raw text from image bytes.

    Parameters
    ----------
    image_bytes : bytes
    engine : "auto" | "tesseract" | "easyocr"

    Returns
    -------
    dict with keys: text, engine_used, confidence (0-100), error
    """
    result = {"text": "", "engine_used": "", "confidence": 0, "error": None}

    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        result["error"] = f"Cannot open image: {e}"
        return result

    processed = _preprocess(img)

    if engine in ("auto", "tesseract"):
        text, conf = _try_tesseract(processed)
        if text.strip():
            result.update(text=text, engine_used="tesseract", confidence=conf)
            return result

    if engine in ("auto", "easyocr"):
        text, conf = _try_easyocr(image_bytes)
        if text.strip():
            result.update(text=text, engine_used="easyocr", confidence=conf)
            return result

    # nothing worked — return empty
    result["error"] = "No text could be extracted from the image."
    return result


# ── engines ──────────────────────────────────────────────────────────────────

def _try_tesseract(img: Image.Image) -> tuple[str, int]:
    try:
        import pytesseract  # type: ignore

        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        confidences = [c for c in data["conf"] if isinstance(c, (int, float)) and c >= 0]
        avg_conf = int(sum(confidences) / len(confidences)) if confidences else 0
        text = pytesseract.image_to_string(img, config="--psm 6")
        return text, avg_conf
    except Exception as e:
        logger.debug(f"Tesseract failed: {e}")
        return "", 0


def _try_easyocr(image_bytes: bytes) -> tuple[str, int]:
    reader = _get_easyocr()
    if reader is None:
        return "", 0
    try:
        import numpy as np  # type: ignore

        img_array = np.frombuffer(image_bytes, dtype=np.uint8)
        import cv2  # type: ignore

        img_cv = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        results = reader.readtext(img_cv)
        if not results:
            return "", 0
        texts, confs = [], []
        for (_bbox, text, conf) in results:
            texts.append(text)
            confs.append(conf)
        combined = " ".join(texts)
        avg_conf = int(sum(confs) / len(confs) * 100)
        return combined, avg_conf
    except Exception as e:
        logger.debug(f"EasyOCR failed: {e}")
        return "", 0
