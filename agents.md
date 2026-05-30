# 🤖 AGENTS.md — Medico.AI Agent Architecture

This document describes the AI agent pipeline powering Medico.AI — how each agent works, what it receives, what it outputs, and how they chain together.

---

## 🧭 Overview

Medico.AI uses a **sequential multi-agent pipeline**. Each agent has a single responsibility and passes its output to the next.

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INPUT                             │
│                  (Prescription Image)                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   OCR Agent     │  Extracts raw text from image
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   NLP Agent     │  Identifies medicine names
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Matcher Agent  │  Maps brands → generic salts
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Pricer Agent   │  Compares prices, ranks options
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ Response Agent  │  Formats final output for UI
                   └─────────────────┘
```

---

## 🔬 Agent Breakdown

---

### 1. 📸 OCR Agent

**File:** `backend/services/ocr.py`

**Responsibility:** Convert the uploaded prescription image into raw text.

**Input:**
```
Image file (JPG / PNG / PDF)
```

**Output:**
```json
{
  "raw_text": "Tab. Crocin 500mg\nAugmentin 625\nPan 40...",
  "confidence": 0.91,
  "engine_used": "easyocr"
}
```

**Logic:**
- Tries **EasyOCR** first (better for handwritten/low-quality images)
- Falls back to **Tesseract** for printed/typed prescriptions
- Applies image preprocessing (grayscale, denoise, deskew) before OCR

**Key libraries:** `easyocr`, `pytesseract`, `opencv-python`

---

### 2. 🧠 NLP Agent

**File:** `backend/services/nlp.py`

**Responsibility:** Parse raw OCR text and extract structured medicine entries.

**Input:**
```json
{
  "raw_text": "Tab. Crocin 500mg\nAugmentin 625\nPan 40..."
}
```

**Output:**
```json
{
  "medicines": [
    { "name": "Crocin", "form": "Tablet", "dosage": "500mg" },
    { "name": "Augmentin", "form": "Tablet", "dosage": "625mg" },
    { "name": "Pan", "form": "Tablet", "dosage": "40mg" }
  ]
}
```

**Logic:**
- Strips noise (doctor names, dates, clinic headers)
- Uses **spaCy NER** to identify drug-like tokens
- Uses **regex patterns** to extract dosage and form (Tab / Cap / Syp / Inj)
- Falls back to **HuggingFace NER model** for ambiguous cases

**Key libraries:** `spacy`, `transformers`, `re`

---

### 3. 🔎 Matcher Agent

**File:** `backend/services/matcher.py`

**Responsibility:** Map each extracted brand name to its generic salt composition and find equivalent generics.

**Input:**
```json
{
  "medicines": [
    { "name": "Crocin", "form": "Tablet", "dosage": "500mg" }
  ]
}
```

**Output:**
```json
{
  "matches": [
    {
      "brand": "Crocin",
      "salt": "Paracetamol",
      "dosage": "500mg",
      "generics": ["Calpol", "Metacin", "P-500", "Paracip"]
    }
  ]
}
```

**Logic:**
1. **Exact lookup** in `medicines.csv` by brand name
2. **Fuzzy match** (RapidFuzz, threshold ≥ 85) for OCR typos / spelling variants
3. **Salt normalization** — maps brand → INN (International Nonproprietary Name)
4. **Reverse lookup** — finds all brands sharing the same salt + dosage

**Key libraries:** `rapidfuzz`, `pandas`

---

### 4. 💰 Pricer Agent

**File:** `backend/services/pricer.py`

**Responsibility:** Fetch prices for each matched medicine and rank by cost.

**Input:**
```json
{
  "matches": [
    {
      "brand": "Crocin",
      "salt": "Paracetamol",
      "dosage": "500mg",
      "generics": ["Calpol", "Metacin", "P-500", "Paracip"]
    }
  ]
}
```

**Output:**
```json
{
  "results": [
    {
      "brand": "Crocin 500mg",
      "brand_price": 32.00,
      "alternatives": [
        { "name": "Paracip 500mg", "price": 8.50, "savings": "73%" },
        { "name": "P-500",         "price": 6.00, "savings": "81%" },
        { "name": "Metacin 500mg", "price": 5.50, "savings": "83%" }
      ]
    }
  ]
}
```

**Logic:**
- Looks up MRP from local `medicines.csv` database
- Calculates savings percentage: `((brand - generic) / brand) * 100`
- Sorts alternatives by price ascending
- Flags **Jan Aushadhi** generics separately when available

**Key libraries:** `pandas`, `numpy`

---

### 5. 📋 Response Agent

**File:** `backend/services/responder.py`

**Responsibility:** Format the final structured results for the Streamlit frontend.

**Input:**
```json
{ "results": [ ... ] }
```

**Output:**
```json
{
  "summary": {
    "total_medicines": 3,
    "estimated_brand_cost": 210.00,
    "estimated_generic_cost": 38.00,
    "total_savings": "81%"
  },
  "medicines": [ ... ]
}
```

**Logic:**
- Aggregates total cost and savings across all medicines
- Generates a human-readable summary string
- Structures data for Streamlit `st.dataframe()` and `st.metric()` components

---

## 🔗 Agent Communication

Agents communicate via **plain Python dicts** (no message queue needed for v1). Each agent exposes a single `run(input: dict) -> dict` method.

```python
# backend/pipeline.py

from services.ocr      import OCRAgent
from services.nlp      import NLPAgent
from services.matcher  import MatcherAgent
from services.pricer   import PricerAgent
from services.responder import ResponseAgent

def run_pipeline(image_path: str) -> dict:
    result = OCRAgent().run({"image_path": image_path})
    result = NLPAgent().run(result)
    result = MatcherAgent().run(result)
    result = PricerAgent().run(result)
    result = ResponseAgent().run(result)
    return result
```

---

## 🛡️ Error Handling

Each agent must handle failures gracefully and never crash the pipeline.

| Agent | Failure Mode | Fallback |
|-------|-------------|----------|
| OCR Agent | Unreadable image | Return empty text + low confidence warning |
| NLP Agent | No medicines found | Return empty list + user prompt to retry |
| Matcher Agent | No match found | Return `"unknown"` salt, skip pricing |
| Pricer Agent | Price not in DB | Mark as `"price unavailable"` |
| Response Agent | Malformed input | Return safe error response to UI |

---

## 🧪 Testing Agents

Each agent has its own test file under `tests/`.

```bash
# Run all agent tests
pytest tests/

# Run a specific agent
pytest tests/test_ocr.py
pytest tests/test_nlp.py
pytest tests/test_matcher.py
pytest tests/test_pricer.py
```

---

## 📁 File Reference

```
backend/
├── pipeline.py          # Orchestrates all agents in sequence
└── services/
    ├── ocr.py           # OCR Agent
    ├── nlp.py           # NLP Agent
    ├── matcher.py       # Matcher Agent
    ├── pricer.py        # Pricer Agent
    └── responder.py     # Response Agent

tests/
├── test_ocr.py
├── test_nlp.py
├── test_matcher.py
└── test_pricer.py

data/
└── medicines.csv        # Brand → salt → price database
```

---

## 🚧 Future Agents

| Agent | Purpose |
|-------|---------|
| **Pharmacy Locator Agent** | Find nearby stores stocking the generic |
| **Jan Aushadhi Agent** | Query government API for PMBJP store prices |
| **Voice Input Agent** | Transcribe spoken prescription via Whisper |
| **Interaction Checker Agent** | Flag dangerous drug combinations |

---

*For contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md). For project setup, see [README.md](README.md).*