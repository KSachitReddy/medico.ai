"""
OCR service — uses Claude Vision as primary engine (best for handwritten prescriptions),
falls back to Tesseract then EasyOCR if Claude is unavailable.
"""
from __future__ import annotations

import base64
import io
import logging
import os
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


def _img_to_jpeg_bytes(image_bytes: bytes) -> tuple[bytes, str]:
    """Convert image bytes to JPEG and return (jpeg_bytes, media_type)."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=95)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return image_bytes, "image/jpeg"


# ── public API ───────────────────────────────────────────────────────────────

def extract_text_from_image(image_bytes: bytes, engine: str = "auto") -> dict:
    """
    Extract raw text from image bytes.

    Parameters
    ----------
    image_bytes : bytes
    engine : "auto" | "claude" | "tesseract" | "easyocr"

    Returns
    -------
    dict with keys: text, engine_used, confidence (0-100), error
    """
    result = {"text": "", "engine_used": "", "confidence": 0, "error": None}

    # ── Claude Vision (primary — handles handwriting best) ───────────────────
    if engine in ("auto", "claude"):
        text, conf = _try_claude(image_bytes)
        if text.strip():
            result.update(text=text, engine_used="claude-vision", confidence=conf)
            return result
        if engine == "claude":
            result["error"] = "Claude Vision could not extract text. Check ANTHROPIC_API_KEY."
            return result

    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        result["error"] = f"Cannot open image: {e}"
        return result

    processed = _preprocess(img)

    # ── Tesseract fallback ───────────────────────────────────────────────────
    if engine in ("auto", "tesseract"):
        text, conf = _try_tesseract(processed)
        if text.strip():
            result.update(text=text, engine_used="tesseract", confidence=conf)
            return result

    # ── EasyOCR fallback ─────────────────────────────────────────────────────
    if engine in ("auto", "easyocr"):
        text, conf = _try_easyocr(image_bytes)
        if text.strip():
            result.update(text=text, engine_used="easyocr", confidence=conf)
            return result

    result["error"] = "No text could be extracted from the image."
    return result


# ── engines ──────────────────────────────────────────────────────────────────

def _try_claude(image_bytes: bytes) -> tuple[str, int]:
    """Use Claude's vision to extract prescription text — handles handwriting well."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.debug("ANTHROPIC_API_KEY not set — skipping Claude Vision")
        return "", 0
    try:
        import anthropic  # type: ignore

        jpeg_bytes, media_type = _img_to_jpeg_bytes(image_bytes)
        b64 = base64.standard_b64encode(jpeg_bytes).decode("utf-8")

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "This is a medical prescription image. "
                                "Please transcribe ALL text you can see, "
                                "including handwritten medicine names, dosages, "
                                "and instructions. Preserve the original layout "
                                "as much as possible. Output only the transcribed "
                                "text with no commentary."
                            ),
                        },
                    ],
                }
            ],
        )
        text = message.content[0].text if message.content else ""
        return text, 95  # Claude vision is highly accurate
    except Exception as e:
        logger.warning(f"Claude Vision failed: {e}")
        return "", 0


_OCR_TMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ocr_tmp")


def _try_tesseract(img: Image.Image) -> tuple[str, int]:
    import subprocess
    import uuid

    try:
        os.makedirs(_OCR_TMP_DIR, exist_ok=True)
        tmp_path = os.path.join(_OCR_TMP_DIR, f"ocr_{uuid.uuid4().hex}.png")
        img.save(tmp_path)
        result = subprocess.run(
            ["tesseract", tmp_path, "stdout", "--psm", "6"],
            capture_output=True,
            timeout=30,
        )
        text = result.stdout.decode("utf-8", errors="replace").strip()
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return text, 80 if text else 0
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
