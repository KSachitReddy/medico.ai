# 🏥 Medico.AI
> **AI-Powered Smart Medicine Cost Optimizer for India 🇮🇳**

Scan your prescription → get generic alternatives → save up to **20×** on medicine costs.

---

## 🚨 The Problem

Millions of patients in India unknowingly overpay for branded medicines despite equally effective generics being available at a fraction of the cost.

| Challenge | Impact |
|-----------|--------|
| 💸 Branded vs generic price gap | **5×–20× more expensive** |
| 🧾 Prescriptions use brand names | Salt composition hidden from patients |
| 🏪 Pharmacy incentive bias | High-margin drugs pushed over alternatives |
| ❌ No unified decoding tool | No system to auto-suggest cheaper alternatives |

---

## 💡 Existing Solutions & Their Gaps

### Jan Aushadhi *(Government Initiative)*
- ❌ Limited reach and awareness
- ❌ No prescription decoding
- ❌ Physical stores only

### Medicine Search Platforms
- ❌ Manual search required — needs prior knowledge
- ❌ No OCR or AI integration

### Pharmacist Suggestions
- ❌ Not standardized
- ❌ Can be incentive-driven and biased

---

## 🚀 Our Solution — Medico.AI

**Medico.AI** is an AI-powered platform that automatically decodes prescriptions and recommends the cheapest generic alternatives.

```
📸 Upload Prescription
        ↓
🔍 OCR — Text Extraction (Tesseract / EasyOCR)
        ↓
🧠 NLP Processing — Medicine Name Extraction
        ↓
🔬 Brand → Generic Mapping (Fuzzy + Salt Matching)
        ↓
💰 Price Comparison Engine
        ↓
✅ Suggested Cheapest Alternatives
```

---

## ✨ Features

- 📷 **Prescription Image Upload** — photos, scans, handwritten
- 🤖 **AI-Based Medicine Extraction** — OCR + NLP pipeline
- 🔎 **Brand → Generic Mapping** — drug name normalization & salt composition lookup
- 💸 **Price Comparison Engine** — ranked alternatives with savings estimate
- ⚡ **Fast & User-Friendly Interface** — built with Streamlit

---

## ⚙️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python, FastAPI / Flask |
| **Frontend** | Streamlit |
| **OCR** | Tesseract, EasyOCR |
| **NLP / AI** | spaCy, HuggingFace Transformers |
| **Matching** | FuzzyWuzzy / RapidFuzz |
| **Database** | SQLite / PostgreSQL |
| **Utilities** | Pandas, NumPy |

---

## 🏗️ Project Structure

```
medico-ai/
│
├── backend/
│   ├── app.py
│   ├── routes/
│   │   ├── upload.py
│   │   └── medicines.py
│   ├── services/
│   │   ├── ocr.py
│   │   ├── nlp.py
│   │   └── matcher.py
│   ├── database/
│   │   ├── db.py
│   │   └── models.py
│   └── utils/
│       └── helpers.py
│
├── frontend/
│   ├── app.py          # Streamlit UI
│   └── components/
│
├── data/
│   └── medicines.csv
│
├── requirements.txt
├── README.md
└── .env
```

---

## 📦 Installation

### Prerequisites
- Python 3.9+
- pip / uv
- Git

---

### 🪟 Windows

```bash
# Clone the repo
git clone https://github.com/your-username/medico-ai.git
cd medico-ai

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR
# Download: https://github.com/tesseract-ocr/tesseract
# Add the install path to your system environment variables

# Run backend
cd backend
python app.py

# Run frontend (new terminal)
cd ../frontend
streamlit run app.py
```

---

### 🍎 macOS

```bash
# Install Tesseract
brew install tesseract

# Clone the repo
git clone https://github.com/your-username/medico-ai.git
cd medico-ai

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend
cd backend
python app.py

# Run frontend (new terminal)
cd ../frontend
streamlit run app.py
```

---

### ⚡ Using `uv` *(Recommended — Fast Package Manager)*

```bash
pip install uv

uv venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate      # Windows

uv pip install -r requirements.txt
```

---

## ▶️ How to Use

1. **Upload** your prescription image (JPG, PNG, or scanned PDF)
2. **AI extracts** medicine names automatically
3. **System identifies** generic salt compositions
4. **Price engine compares** available options
5. **View results** — cheapest alternatives ranked by savings

---

## 📊 Roadmap

- [ ] 📍 Nearby pharmacy integration
- [ ] 🏛️ Jan Aushadhi Government API integration
- [ ] 🗣️ Voice-based prescription input
- [ ] 📱 Mobile app deployment (Android / iOS)

---

## 🤝 Contributing

Pull requests are welcome!

For major changes, please open an issue first to discuss what you'd like to change.

```bash
# Fork → Clone → Branch → PR
git checkout -b feature/your-feature-name
```

---

