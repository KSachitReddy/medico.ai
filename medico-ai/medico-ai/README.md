# 🏥 Medico.AI

> **AI-Powered Smart Medicine Cost Optimizer for India**
> Scan your prescription → get generic alternatives → save up to 20× on medicine costs.

---

## 🚨 The Problem

Millions of patients in India unknowingly overpay for branded medicines despite equally effective generics being available at a fraction of the cost.

| Challenge | Impact |
|-----------|--------|
| 💸 Branded vs generic price gap | 5×–20× more expensive |
| 🧾 Prescriptions use brand names | Salt composition hidden from patients |
| 🏪 Pharmacy incentive bias | High-margin drugs pushed over alternatives |
| ❌ No unified decoding tool | No system to auto-suggest cheaper alternatives |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Tesseract OCR (optional but recommended for image upload)

### 1. Clone & Setup

```bash
git clone https://github.com/your-username/medico-ai.git
cd medico-ai

# Automated setup (creates venv + installs all deps)
python setup.py
```

### 2. Activate environment

```bash
# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Start the app

```bash
python start.py
```

Then open **http://localhost:8501** in your browser.

---

## 📦 Manual Installation

### macOS

```bash
brew install tesseract
git clone https://github.com/your-username/medico-ai.git && cd medico-ai
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python start.py
```

### Windows

```powershell
# Download Tesseract: https://github.com/tesseract-ocr/tesseract
# Add Tesseract to PATH

git clone https://github.com/your-username/medico-ai.git
cd medico-ai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python start.py
```

### Linux (Ubuntu/Debian)

```bash
sudo apt install tesseract-ocr
git clone https://github.com/your-username/medico-ai.git && cd medico-ai
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python start.py
```

---

## ▶️ Running Separately (Advanced)

```bash
# Terminal 1 — Backend API (http://localhost:8000)
python backend/app.py

# Terminal 2 — Frontend UI (http://localhost:8501)
streamlit run frontend/app.py
```

API docs available at **http://localhost:8000/docs**

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📷 Prescription Upload | JPG, PNG, WebP, BMP photos and scans |
| ✏️ Text Input | Manually enter or paste medicine names |
| 🤖 OCR Pipeline | Tesseract (fast) + EasyOCR (accurate) fallback |
| 🔎 Fuzzy Matching | Handles typos, abbreviations, partial names |
| 💸 Price Comparison | Ranked alternatives with savings in ₹ and % |
| 🏛️ Jan Aushadhi | Government generic store prices included |
| 📊 Medicine Browser | Search / filter 100+ medicines database |
| 🔌 REST API | Full FastAPI backend with Swagger docs |

---

## ⚙️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| Backend | Python, FastAPI, Uvicorn |
| Frontend | Streamlit |
| OCR | Tesseract, EasyOCR |
| NLP / Matching | Rule-based NLP, RapidFuzz |
| Database | SQLite (default) / PostgreSQL |
| Data | Pandas, NumPy |

---

## 🗂️ Project Structure

```
medico-ai/
├── backend/
│   ├── app.py                  # FastAPI app entry point
│   ├── routes/
│   │   ├── upload.py           # /upload and /search-text endpoints
│   │   └── medicines.py        # /medicines and /categories endpoints
│   ├── services/
│   │   ├── ocr.py              # Tesseract + EasyOCR pipeline
│   │   ├── nlp.py              # Medicine name extraction
│   │   └── matcher.py          # Fuzzy matching + price comparison
│   └── database/
│       └── db.py               # SQLAlchemy models + seeding
├── frontend/
│   └── app.py                  # Streamlit multi-page UI
├── data/
│   └── medicines.csv           # Master medicine database
├── start.py                    # One-command startup
├── setup.py                    # Automated environment setup
├── requirements.txt
├── .env.example
├── CONTRIBUTING.md
└── USER_MANUAL.md
```

---

## 🌱 Environment Variables

Copy `.env.example` to `.env`:

```env
MEDICO_API_URL=http://localhost:8000/api/v1
DATABASE_URL=sqlite:///./medico.db
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe  # Windows only
```

---

## 📊 Roadmap

- [ ] 📍 Nearby Jan Aushadhi store locator
- [ ] 🏛️ Jan Aushadhi Government API integration
- [ ] 🗣️ Voice-based prescription input
- [ ] 📱 Mobile app (Android / iOS)
- [ ] 🌐 Hindi and regional language support
- [ ] 📤 Export savings report as PDF

---

## ⚠️ Disclaimer

Medico.AI is an **informational tool only**.
Always consult a registered pharmacist or qualified doctor before switching medicines.
This tool does not dispense medical advice.

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📖 User Manual

See [USER_MANUAL.md](USER_MANUAL.md) for detailed usage instructions.
