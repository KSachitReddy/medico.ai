"""
Upload & OCR route.
POST /api/v1/upload  — accepts image, returns extracted medicine names + alternatives.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from pydantic import BaseModel

from backend.database.db import get_db, SearchHistory
from backend.services.ocr import extract_text_from_image
from backend.services.nlp import extract_medicines
from backend.services.matcher import bulk_find_alternatives, MedicineMatch, AlternativeResult

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ── Pydantic response models ─────────────────────────────────────────────────

class AlternativeOut(BaseModel):
    brand_name: str
    generic_name: str
    salt_composition: str
    manufacturer: str
    brand_price: float
    generic_price: float
    jan_aushadhi_price: Optional[float]
    unit_type: str
    category: str
    strength: str
    form: str
    savings_vs_brand: float
    savings_pct: float


class MedicineMatchOut(BaseModel):
    query: str
    matched_brand: Optional[str]
    salt_composition: Optional[str]
    match_type: str
    fuzzy_score: int
    alternatives: List[AlternativeOut]
    error: Optional[str]


class UploadResponse(BaseModel):
    session_id: str
    raw_text: str
    ocr_engine: str
    ocr_confidence: int
    extracted_medicines: List[str]
    results: List[MedicineMatchOut]
    total_medicines_found: int


# ── helpers ──────────────────────────────────────────────────────────────────

def _alt_to_out(a: AlternativeResult) -> AlternativeOut:
    return AlternativeOut(
        brand_name=a.brand_name,
        generic_name=a.generic_name,
        salt_composition=a.salt_composition,
        manufacturer=a.manufacturer,
        brand_price=a.brand_price,
        generic_price=a.generic_price,
        jan_aushadhi_price=a.jan_aushadhi_price,
        unit_type=a.unit_type,
        category=a.category,
        strength=a.strength,
        form=a.form,
        savings_vs_brand=a.savings_vs_brand,
        savings_pct=a.savings_pct,
    )


def _match_to_out(m: MedicineMatch) -> MedicineMatchOut:
    return MedicineMatchOut(
        query=m.query,
        matched_brand=m.matched_brand,
        salt_composition=m.salt_composition,
        match_type=m.match_type,
        fuzzy_score=m.fuzzy_score,
        alternatives=[_alt_to_out(a) for a in m.alternatives],
        error=m.error,
    )


# ── routes ───────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse)
async def upload_prescription(
    file: UploadFile = File(...),
    ocr_engine: str = Form("auto"),
    db=Depends(get_db),
):
    """
    Upload a prescription image (JPG / PNG / WebP / BMP).
    Returns OCR text, extracted medicine names, and cheaper alternatives.
    """
    # Validate file type
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

    # OCR
    ocr_result = extract_text_from_image(raw, engine=ocr_engine)
    if ocr_result.get("error") and not ocr_result.get("text"):
        raise HTTPException(status_code=422, detail=f"OCR failed: {ocr_result['error']}")

    raw_text = ocr_result.get("text", "")

    # NLP — extract medicine names
    medicines_found = extract_medicines(raw_text)

    # Match & price
    matches = bulk_find_alternatives(medicines_found, db)

    # Save to history
    session_id = str(uuid.uuid4())
    history = SearchHistory(
        medicines_searched=", ".join(medicines_found),
        session_id=session_id,
    )
    db.add(history)
    db.commit()

    return UploadResponse(
        session_id=session_id,
        raw_text=raw_text,
        ocr_engine=ocr_result.get("engine_used", "none"),
        ocr_confidence=ocr_result.get("confidence", 0),
        extracted_medicines=medicines_found,
        results=[_match_to_out(m) for m in matches],
        total_medicines_found=len(medicines_found),
    )


@router.post("/search-text", response_model=UploadResponse)
async def search_by_text(
    prescription_text: str = Form(...),
    db=Depends(get_db),
):
    """
    Manually enter prescription text (skip OCR).
    """
    medicines_found = extract_medicines(prescription_text)
    matches = bulk_find_alternatives(medicines_found, db)

    session_id = str(uuid.uuid4())
    history = SearchHistory(
        medicines_searched=", ".join(medicines_found),
        session_id=session_id,
    )
    db.add(history)
    db.commit()

    return UploadResponse(
        session_id=session_id,
        raw_text=prescription_text,
        ocr_engine="manual",
        ocr_confidence=100,
        extracted_medicines=medicines_found,
        results=[_match_to_out(m) for m in matches],
        total_medicines_found=len(medicines_found),
    )
