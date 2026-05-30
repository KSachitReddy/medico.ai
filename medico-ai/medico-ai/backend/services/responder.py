"""
Responder Agent — formats the final pipeline output for the API / frontend.

Takes PricedMedicine + PricingSummary and produces a clean, serialisable dict
that the FastAPI route returns as JSON.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from backend.services.pricer import PricedMedicine, PricingSummary

logger = logging.getLogger(__name__)


def format_response(
    priced_medicines: List[PricedMedicine],
    summary: PricingSummary,
    raw_text: str = "",
    ocr_engine: str = "",
    ocr_confidence: int = 0,
    extracted_medicines: Optional[List[str]] = None,
    session_id: str = "",
    llm_extraction_used: bool = False,
    interaction_warning: str = "",
) -> dict:
    """
    Build the complete API response dict.

    Parameters
    ----------
    priced_medicines : output of pricer.price_matches()
    summary : PricingSummary
    raw_text : raw OCR text
    ocr_engine : OCR engine used
    ocr_confidence : OCR confidence score
    extracted_medicines : list of medicine names extracted by NLP / LLM
    session_id : UUID for this session
    llm_extraction_used : whether LLM fallback was used for NLP
    interaction_warning : drug interaction text from LLM

    Returns
    -------
    dict — serialisable JSON-ready response
    """
    results = [_format_medicine(pm) for pm in priced_medicines]

    return {
        "session_id": session_id,
        "raw_text": raw_text,
        "ocr_engine": ocr_engine,
        "ocr_confidence": ocr_confidence,
        "extracted_medicines": extracted_medicines or [],
        "llm_extraction_used": llm_extraction_used,
        "total_medicines_found": len(extracted_medicines or []),
        "results": results,
        "summary": _format_summary(summary),
        "interaction_warning": interaction_warning,
    }


def _format_medicine(pm: PricedMedicine) -> dict:
    return {
        "query": pm.query,
        "matched_brand": pm.matched_brand,
        "salt_composition": pm.salt_composition,
        "match_type": pm.match_type,
        "fuzzy_score": pm.fuzzy_score,
        "error": pm.error,
        "original_price": pm.original_price,
        "cheapest_price": pm.cheapest_price,
        "best_savings_pct": pm.best_savings_pct,
        "jan_aushadhi_available": pm.jan_aushadhi_available,
        "alternatives": [_format_alternative(a) for a in pm.alternatives],
    }


def _format_alternative(a) -> dict:
    return {
        "brand_name": a.brand_name,
        "generic_name": a.generic_name,
        "salt_composition": a.salt_composition,
        "manufacturer": a.manufacturer,
        "strength": a.strength,
        "form": a.form,
        "unit_type": a.unit_type,
        "category": a.category,
        "brand_price": a.brand_price,
        "generic_price": a.generic_price,
        "jan_aushadhi_price": a.jan_aushadhi_price,
        "savings_vs_brand": a.savings_vs_brand,
        "savings_pct": a.savings_pct,
        "is_jan_aushadhi": a.is_jan_aushadhi,
        "is_cheapest": a.is_cheapest,
    }


def _format_summary(s: PricingSummary) -> dict:
    return {
        "total_medicines": s.total_medicines,
        "identified_count": s.identified_count,
        "not_found_count": s.not_found_count,
        "estimated_brand_cost": s.estimated_brand_cost,
        "estimated_cheapest_cost": s.estimated_cheapest_cost,
        "estimated_jan_aushadhi_cost": s.estimated_jan_aushadhi_cost,
        "potential_savings": s.potential_savings,
        "savings_pct": s.savings_pct,
        "jan_aushadhi_savings": s.jan_aushadhi_savings,
        "jan_aushadhi_savings_pct": s.jan_aushadhi_savings_pct,
    }
