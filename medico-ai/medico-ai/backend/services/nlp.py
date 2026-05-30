"""
NLP service — extracts medicine names from raw OCR text.
Uses rule-based extraction (no model download required at startup).
Optionally enhanced with spaCy NER if available.
"""
from __future__ import annotations

import re
import logging
from typing import List

logger = logging.getLogger(__name__)

# ── common prescription patterns ─────────────────────────────────────────────

# Keywords that appear right before a medicine name on prescriptions
_BEFORE_KW = re.compile(
    r"(?:tab(?:let)?s?|cap(?:sule)?s?|syr(?:up)?|inj(?:ection)?|oint(?:ment)?|drops?|"
    r"rx|rx:|r/|rx\.|medicine|drug|medication|prescribed|take|give|use)\s*[:\-\s]*",
    re.IGNORECASE,
)

# Dosage / frequency tokens that are NOT medicine names
_DOSAGE_PATTERN = re.compile(
    r"\b(\d+\s*(?:mg|mcg|ml|g|iu|unit|units|tablet|cap|tab|tsp|tbsp)s?)\b",
    re.IGNORECASE,
)
_FREQUENCY_PATTERN = re.compile(
    r"\b(?:od|bd|tds|qid|sos|hs|ac|pc|prn|stat|once|twice|thrice|daily|weekly|"
    r"morning|afternoon|evening|night|bedtime|before|after|meals?|food)\b",
    re.IGNORECASE,
)

# Lines that are definitely not medicine names
_SKIP_LINE_PATTERN = re.compile(
    r"(?:date|age|sex|name|address|phone|tel|dr\.|doctor|hospital|clinic|"
    r"patient|diagnosis|weight|height|bp|blood|pressure|signature|rx|©|page)",
    re.IGNORECASE,
)

# Looks like a medicine name: starts uppercase, 4-30 chars, no digits only
_MEDICINE_CANDIDATE = re.compile(r"^[A-Z][A-Za-z0-9\-\+\s]{2,28}$")


def extract_medicines(text: str) -> List[str]:
    """
    Extract potential medicine names from OCR text.

    Returns a de-duplicated list of candidate medicine names.
    """
    if not text or not text.strip():
        return []

    candidates: List[str] = []

    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        if _SKIP_LINE_PATTERN.search(line):
            continue

        # strip dosage / frequency suffixes
        cleaned = _DOSAGE_PATTERN.sub("", line)
        cleaned = _FREQUENCY_PATTERN.sub("", cleaned)

        # try to pull token right after keyword markers
        kw_match = _BEFORE_KW.search(cleaned)
        if kw_match:
            after = cleaned[kw_match.end():].strip()
            token = after.split()[0] if after.split() else ""
            if token and _MEDICINE_CANDIDATE.match(token):
                candidates.append(_normalise(token))
            continue

        # otherwise, grab every capitalised token on the line
        tokens = cleaned.split()
        for tok in tokens:
            tok_clean = re.sub(r"[^A-Za-z0-9\-\+]", "", tok)
            if len(tok_clean) >= 3 and _MEDICINE_CANDIDATE.match(tok_clean):
                candidates.append(_normalise(tok_clean))

    # deduplicate, preserve order
    seen: set = set()
    unique: List[str] = []
    for c in candidates:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique


def _normalise(name: str) -> str:
    """Title-case and strip extra whitespace."""
    return name.strip().title()
