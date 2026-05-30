"""
Matcher service — maps extracted medicine names to DB records.
Uses fuzzy matching (RapidFuzz) + exact salt/generic lookup.
"""
from __future__ import annotations

import logging
from typing import List, Optional
from dataclasses import dataclass, field

from rapidfuzz import fuzz, process  # type: ignore
from sqlalchemy.orm import Session

from backend.database.db import Medicine

logger = logging.getLogger(__name__)

FUZZY_THRESHOLD = 72  # minimum score (0-100) to accept a fuzzy match


@dataclass
class AlternativeResult:
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
    savings_vs_brand: float = 0.0
    savings_pct: float = 0.0
    match_score: int = 100


@dataclass
class MedicineMatch:
    query: str                          # original extracted name
    matched_brand: Optional[str] = None  # best DB brand match
    salt_composition: Optional[str] = None
    alternatives: List[AlternativeResult] = field(default_factory=list)
    match_type: str = "none"            # "exact" | "fuzzy" | "salt" | "none"
    fuzzy_score: int = 0
    error: Optional[str] = None


def find_alternatives(medicine_name: str, db: Session, top_n: int = 5) -> MedicineMatch:
    """
    Main entry point.  Given a medicine name string, returns a MedicineMatch
    with ranked cheaper alternatives.
    """
    result = MedicineMatch(query=medicine_name)

    if not medicine_name or not medicine_name.strip():
        result.error = "Empty medicine name"
        return result

    name_lower = medicine_name.strip().lower()

    # 1. Exact brand match (case-insensitive)
    exact = db.query(Medicine).filter(
        Medicine.brand_name.ilike(name_lower)
    ).first()

    if exact:
        result.matched_brand = exact.brand_name
        result.salt_composition = exact.salt_composition
        result.match_type = "exact"
        result.fuzzy_score = 100
        result.alternatives = _get_alternatives_by_salt(exact, db, top_n)
        return result

    # 2. Fuzzy brand match
    all_brands = db.query(Medicine.brand_name).all()
    brand_list = [b[0] for b in all_brands]

    fuzzy_match = process.extractOne(
        medicine_name,
        brand_list,
        scorer=fuzz.token_set_ratio,
        score_cutoff=FUZZY_THRESHOLD,
    )

    if fuzzy_match:
        matched_name, score, _ = fuzzy_match
        db_med = db.query(Medicine).filter(
            Medicine.brand_name.ilike(matched_name)
        ).first()
        if db_med:
            result.matched_brand = db_med.brand_name
            result.salt_composition = db_med.salt_composition
            result.match_type = "fuzzy"
            result.fuzzy_score = int(score)
            result.alternatives = _get_alternatives_by_salt(db_med, db, top_n)
            return result

    # 3. Fuzzy generic/salt name match
    all_generics = db.query(Medicine.generic_name, Medicine.salt_composition).all()
    generic_list = [g[0] for g in all_generics]
    salt_list = [g[1] for g in all_generics]

    generic_match = process.extractOne(
        medicine_name,
        generic_list,
        scorer=fuzz.token_set_ratio,
        score_cutoff=FUZZY_THRESHOLD,
    )

    if generic_match:
        matched_generic, score, idx = generic_match
        # find a representative entry
        db_med = db.query(Medicine).filter(
            Medicine.generic_name.ilike(matched_generic)
        ).order_by(Medicine.brand_price_per_unit.desc()).first()
        if db_med:
            result.matched_brand = db_med.brand_name
            result.salt_composition = db_med.salt_composition
            result.match_type = "salt"
            result.fuzzy_score = int(score)
            result.alternatives = _get_alternatives_by_salt(db_med, db, top_n)
            return result

    result.error = f"No match found for '{medicine_name}'"
    return result


def _get_alternatives_by_salt(
    reference: Medicine, db: Session, top_n: int
) -> List[AlternativeResult]:
    """
    Fetch all medicines with the same generic/salt and rank by price.
    Always includes a 'generic formulation' entry.
    """
    # same generic name
    same_salt = db.query(Medicine).filter(
        Medicine.generic_name.ilike(reference.generic_name)
    ).all()

    ref_price = reference.brand_price_per_unit

    alts: List[AlternativeResult] = []
    for med in same_salt:
        savings = max(0.0, ref_price - med.brand_price_per_unit)
        savings_pct = (savings / ref_price * 100) if ref_price > 0 else 0.0
        alts.append(AlternativeResult(
            brand_name=med.brand_name,
            generic_name=med.generic_name,
            salt_composition=med.salt_composition,
            manufacturer=med.manufacturer,
            brand_price=med.brand_price_per_unit,
            generic_price=med.generic_price_per_unit,
            jan_aushadhi_price=med.jan_aushadhi_price,
            unit_type=med.unit_type,
            category=med.category,
            strength=med.strength,
            form=med.form,
            savings_vs_brand=round(savings, 2),
            savings_pct=round(savings_pct, 1),
        ))

    # Add a standalone "Generic Formulation" entry for the reference salt
    savings_generic = max(0.0, ref_price - reference.generic_price_per_unit)
    savings_pct_generic = (savings_generic / ref_price * 100) if ref_price > 0 else 0.0
    alts.append(AlternativeResult(
        brand_name="Generic Formulation",
        generic_name=reference.generic_name,
        salt_composition=reference.salt_composition,
        manufacturer="Various Manufacturers",
        brand_price=reference.generic_price_per_unit,
        generic_price=reference.generic_price_per_unit,
        jan_aushadhi_price=reference.jan_aushadhi_price,
        unit_type=reference.unit_type,
        category=reference.category,
        strength=reference.strength,
        form=reference.form,
        savings_vs_brand=round(savings_generic, 2),
        savings_pct=round(savings_pct_generic, 1),
    ))

    # Sort cheapest first
    alts.sort(key=lambda a: a.brand_price)

    # Deduplicate by brand name
    seen: set = set()
    unique: List[AlternativeResult] = []
    for a in alts:
        key = a.brand_name.lower()
        if key not in seen:
            seen.add(key)
            unique.append(a)

    return unique[:top_n]


def bulk_find_alternatives(medicine_names: List[str], db: Session) -> List[MedicineMatch]:
    """Process a list of medicine names."""
    return [find_alternatives(name, db) for name in medicine_names]
