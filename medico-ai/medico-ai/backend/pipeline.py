"""
Medico.AI — full agent pipeline orchestrator.

Pipeline:
    OCR Agent → NLP Agent (+ LLM fallback) → Matcher Agent
    → Pricer Agent → Response Agent

Usage
-----
    from backend.pipeline import run_pipeline_from_image, run_pipeline_from_text

    result = run_pipeline_from_image(image_bytes, db_session, ocr_engine="auto")
    result = run_pipeline_from_text("Tab Crocin 500mg\nAugmentin 625", db_session)
"""
from __future__ import annotations

import uuid
import logging
from typing import Optional

from sqlalchemy.orm import Session

from backend.services.ocr import extract_text_from_image
from backend.services.nlp import extract_medicines
from backend.services.llm import (
    llm_extract_medicines,
    check_drug_interactions,
    is_llm_configured,
)
from backend.services.matcher import bulk_find_alternatives
from backend.services.pricer import price_matches
from backend.services.responder import format_response
from backend.database.db import SearchHistory

logger = logging.getLogger(__name__)


def run_pipeline_from_image(
    image_bytes: bytes,
    db: Session,
    ocr_engine: str = "auto",
    check_interactions: bool = True,
    session_id: Optional[str] = None,
) -> dict:
    """
    Full pipeline starting from a raw prescription image.

    Returns the formatted API response dict.
    """
    session_id = session_id or str(uuid.uuid4())

    # ── Step 1: OCR Agent ────────────────────────────────────────────────────
    logger.info(f"[Pipeline {session_id}] OCR start (engine={ocr_engine})")
    ocr_result = extract_text_from_image(image_bytes, engine=ocr_engine)
    raw_text = ocr_result.get("text", "")
    ocr_engine_used = ocr_result.get("engine_used", "none")
    ocr_confidence = ocr_result.get("confidence", 0)

    if ocr_result.get("error") and not raw_text:
        return _error_response(
            f"OCR failed: {ocr_result['error']}",
            session_id=session_id,
        )

    return _run_from_text(
        raw_text=raw_text,
        db=db,
        ocr_engine=ocr_engine_used,
        ocr_confidence=ocr_confidence,
        check_interactions=check_interactions,
        session_id=session_id,
    )


def run_pipeline_from_text(
    prescription_text: str,
    db: Session,
    check_interactions: bool = True,
    session_id: Optional[str] = None,
) -> dict:
    """
    Full pipeline starting from plain text (skips OCR).
    """
    session_id = session_id or str(uuid.uuid4())
    return _run_from_text(
        raw_text=prescription_text,
        db=db,
        ocr_engine="manual",
        ocr_confidence=100,
        check_interactions=check_interactions,
        session_id=session_id,
    )


# ── Internal ─────────────────────────────────────────────────────────────────

def _run_from_text(
    raw_text: str,
    db: Session,
    ocr_engine: str,
    ocr_confidence: int,
    check_interactions: bool,
    session_id: str,
) -> dict:

    # ── Step 2: NLP Agent ────────────────────────────────────────────────────
    logger.info(f"[Pipeline {session_id}] NLP extraction")
    medicines_found = extract_medicines(raw_text)
    llm_used = False

    # LLM fallback if rule-based NLP found nothing
    if not medicines_found and is_llm_configured():
        logger.info(f"[Pipeline {session_id}] NLP found nothing — trying LLM fallback")
        medicines_found = llm_extract_medicines(raw_text)
        llm_used = bool(medicines_found)

    logger.info(f"[Pipeline {session_id}] Medicines found: {medicines_found}")

    # ── Step 3: Matcher Agent ────────────────────────────────────────────────
    logger.info(f"[Pipeline {session_id}] Matching medicines")
    matches = bulk_find_alternatives(medicines_found, db)

    # ── Step 4: Pricer Agent ─────────────────────────────────────────────────
    logger.info(f"[Pipeline {session_id}] Pricing")
    priced, summary = price_matches(matches)

    # ── Step 4b: Drug interaction check (LLM) ────────────────────────────────
    interaction_warning = ""
    if check_interactions and len(medicines_found) > 1 and is_llm_configured():
        logger.info(f"[Pipeline {session_id}] Drug interaction check")
        try:
            interaction_warning = check_drug_interactions(medicines_found)
        except Exception as e:
            logger.warning(f"Interaction check failed: {e}")

    # ── Step 5: Response Agent ───────────────────────────────────────────────
    logger.info(f"[Pipeline {session_id}] Formatting response")
    response = format_response(
        priced_medicines=priced,
        summary=summary,
        raw_text=raw_text,
        ocr_engine=ocr_engine,
        ocr_confidence=ocr_confidence,
        extracted_medicines=medicines_found,
        session_id=session_id,
        llm_extraction_used=llm_used,
        interaction_warning=interaction_warning,
    )

    # ── Persist to history ───────────────────────────────────────────────────
    try:
        history = SearchHistory(
            medicines_searched=", ".join(medicines_found),
            session_id=session_id,
        )
        db.add(history)
        db.commit()
    except Exception as e:
        logger.warning(f"History save failed: {e}")

    return response


def _error_response(message: str, session_id: str = "") -> dict:
    return {
        "session_id": session_id or str(uuid.uuid4()),
        "error": message,
        "raw_text": "",
        "ocr_engine": "none",
        "ocr_confidence": 0,
        "extracted_medicines": [],
        "llm_extraction_used": False,
        "total_medicines_found": 0,
        "results": [],
        "summary": {
            "total_medicines": 0,
            "identified_count": 0,
            "not_found_count": 0,
            "estimated_brand_cost": 0.0,
            "estimated_cheapest_cost": 0.0,
            "estimated_jan_aushadhi_cost": 0.0,
            "potential_savings": 0.0,
            "savings_pct": 0.0,
            "jan_aushadhi_savings": 0.0,
            "jan_aushadhi_savings_pct": 0.0,
        },
        "interaction_warning": "",
    }
