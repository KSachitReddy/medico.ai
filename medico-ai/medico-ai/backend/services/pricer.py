"""
Pricer Agent — enriches MedicineMatch results with pricing analysis.

Reads already-matched AlternativeResult objects and:
  - Computes savings vs. branded medicine
  - Ranks alternatives cheapest-first
  - Flags Jan Aushadhi options
  - Aggregates a cost summary across all medicines in a session
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from backend.services.matcher import MedicineMatch, AlternativeResult

logger = logging.getLogger(__name__)


@dataclass
class PricedAlternative:
    brand_name: str
    generic_name: str
    salt_composition: str
    manufacturer: str
    strength: str
    form: str
    unit_type: str
    category: str
    brand_price: float
    generic_price: float
    jan_aushadhi_price: Optional[float]
    savings_vs_brand: float
    savings_pct: float
    is_jan_aushadhi: bool = False
    is_cheapest: bool = False
    match_score: int = 100


@dataclass
class PricedMedicine:
    query: str
    matched_brand: Optional[str]
    salt_composition: Optional[str]
    match_type: str
    fuzzy_score: int
    error: Optional[str]
    alternatives: List[PricedAlternative] = field(default_factory=list)
    # Convenience fields populated by pricer
    cheapest_price: Optional[float] = None
    original_price: Optional[float] = None   # reference brand price
    best_savings_pct: float = 0.0
    jan_aushadhi_available: bool = False


@dataclass
class PricingSummary:
    total_medicines: int
    identified_count: int
    not_found_count: int
    estimated_brand_cost: float
    estimated_cheapest_cost: float
    estimated_jan_aushadhi_cost: float
    potential_savings: float
    savings_pct: float
    jan_aushadhi_savings: float
    jan_aushadhi_savings_pct: float


def price_matches(
    matches: List[MedicineMatch],
    reference_brand_name: Optional[str] = None,
) -> tuple[List[PricedMedicine], PricingSummary]:
    """
    Enrich a list of MedicineMatch objects with pricing analysis.

    Returns
    -------
    (priced_medicines, summary)
    """
    priced: List[PricedMedicine] = []

    total_brand = 0.0
    total_cheapest = 0.0
    total_jan_aushadhi = 0.0
    identified = 0
    not_found = 0

    for match in matches:
        pm = _price_single(match)
        priced.append(pm)

        if pm.error or pm.match_type == "none":
            not_found += 1
            continue

        identified += 1
        if pm.original_price is not None:
            total_brand += pm.original_price
        if pm.cheapest_price is not None:
            total_cheapest += pm.cheapest_price

        # Jan Aushadhi cost — use JA price if available, else cheapest generic
        ja_price = _get_best_ja_price(pm)
        total_jan_aushadhi += ja_price if ja_price is not None else (pm.cheapest_price or 0.0)

    potential_savings = max(0.0, total_brand - total_cheapest)
    savings_pct = (potential_savings / total_brand * 100) if total_brand > 0 else 0.0
    ja_savings = max(0.0, total_brand - total_jan_aushadhi)
    ja_savings_pct = (ja_savings / total_brand * 100) if total_brand > 0 else 0.0

    summary = PricingSummary(
        total_medicines=len(matches),
        identified_count=identified,
        not_found_count=not_found,
        estimated_brand_cost=round(total_brand, 2),
        estimated_cheapest_cost=round(total_cheapest, 2),
        estimated_jan_aushadhi_cost=round(total_jan_aushadhi, 2),
        potential_savings=round(potential_savings, 2),
        savings_pct=round(savings_pct, 1),
        jan_aushadhi_savings=round(ja_savings, 2),
        jan_aushadhi_savings_pct=round(ja_savings_pct, 1),
    )

    return priced, summary


def _price_single(match: MedicineMatch) -> PricedMedicine:
    pm = PricedMedicine(
        query=match.query,
        matched_brand=match.matched_brand,
        salt_composition=match.salt_composition,
        match_type=match.match_type,
        fuzzy_score=match.fuzzy_score,
        error=match.error,
    )

    if not match.alternatives:
        return pm

    # Find the reference (most expensive = branded) price
    ref_price = max(a.brand_price for a in match.alternatives)
    cheapest_price = min(a.brand_price for a in match.alternatives)

    pm.original_price = ref_price
    pm.cheapest_price = cheapest_price
    pm.best_savings_pct = round(
        (ref_price - cheapest_price) / ref_price * 100 if ref_price > 0 else 0.0, 1
    )
    pm.jan_aushadhi_available = any(
        a.jan_aushadhi_price is not None for a in match.alternatives
    )

    priced_alts: List[PricedAlternative] = []
    for i, alt in enumerate(match.alternatives):
        is_ja = alt.jan_aushadhi_price is not None
        pa = PricedAlternative(
            brand_name=alt.brand_name,
            generic_name=alt.generic_name,
            salt_composition=alt.salt_composition,
            manufacturer=alt.manufacturer,
            strength=alt.strength,
            form=alt.form,
            unit_type=alt.unit_type,
            category=alt.category,
            brand_price=alt.brand_price,
            generic_price=alt.generic_price,
            jan_aushadhi_price=alt.jan_aushadhi_price,
            savings_vs_brand=alt.savings_vs_brand,
            savings_pct=alt.savings_pct,
            is_jan_aushadhi=is_ja,
            is_cheapest=(alt.brand_price == cheapest_price),
            match_score=alt.match_score,
        )
        priced_alts.append(pa)

    pm.alternatives = priced_alts
    return pm


def _get_best_ja_price(pm: PricedMedicine) -> Optional[float]:
    ja_prices = [
        a.jan_aushadhi_price
        for a in pm.alternatives
        if a.jan_aushadhi_price is not None
    ]
    return min(ja_prices) if ja_prices else None
