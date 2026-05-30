"""
Upload & OCR route.
POST /api/v1/upload        — accepts image, returns full pipeline output
POST /api/v1/search-text   — accepts raw text, returns full pipeline output
GET  /api/v1/medicines/search?name=X — single medicine lookup
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from pydantic import BaseModel

from backend.database.db import get_db
from backend.pipeline import run_pipeline_from_image, run_pipeline_from_text

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_prescription(
    file: UploadFile = File(...),
    ocr_engine: str = Form("auto"),
    check_interactions: bool = Form(True),
    db=Depends(get_db),
):
    """
    Upload a prescription image (JPG / PNG / WebP / BMP).
    Returns OCR text, extracted medicine names, alternatives, pricing summary,
    and optional drug interaction warnings.
    """
    allowed = {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff"}
    ct = (file.content_type or "").lower()
    if ct not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ct}'. Upload JPG, PNG, WebP, BMP, or TIFF.",
        )

    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB).")

    result = run_pipeline_from_image(
        image_bytes=raw,
        db=db,
        ocr_engine=ocr_engine,
        check_interactions=check_interactions,
    )

    if result.get("error") and not result.get("results"):
        raise HTTPException(status_code=422, detail=result["error"])

    return result


@router.post("/search-text")
async def search_by_text(
    prescription_text: str = Form(...),
    check_interactions: bool = Form(True),
    db=Depends(get_db),
):
    """
    Manually enter prescription text (skip OCR).
    """
    if not prescription_text.strip():
        raise HTTPException(status_code=400, detail="Prescription text cannot be empty.")

    return run_pipeline_from_text(
        prescription_text=prescription_text,
        db=db,
        check_interactions=check_interactions,
    )
