# 📖 Medico.AI — User Manual

> Version 1.0 | Last updated: 2024

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Installation](#2-installation)
3. [Starting the App](#3-starting-the-app)
4. [Using the App](#4-using-the-app)
   - [Home Page & Quick Search](#41-home-page--quick-search)
   - [Uploading a Prescription Image](#42-uploading-a-prescription-image)
   - [Entering Prescription Text Manually](#43-entering-prescription-text-manually)
   - [Single Medicine Search](#44-single-medicine-search)
   - [Browsing the Medicine Database](#45-browsing-the-medicine-database)
5. [Understanding the Results](#5-understanding-the-results)
6. [Tips for Best OCR Results](#6-tips-for-best-ocr-results)
7. [Troubleshooting](#7-troubleshooting)
8. [FAQ](#8-faq)
9. [Important Disclaimers](#9-important-disclaimers)

---

## 1. Introduction

**Medico.AI** helps you decode prescriptions and find cheaper generic alternatives to branded medicines.

### What it does

- Reads your prescription image using AI (OCR)
- Identifies medicine names automatically
- Finds cheaper generic alternatives with the same active ingredients
- Shows Jan Aushadhi prices (government generic stores)
- Calculates exactly how much you can save

### What it does NOT do

- It does not replace medical or pharmacist advice
- It does not guarantee stock availability
- It does not process your data online — everything runs on your own computer

---

## 2. Installation

### Step 1: Install Python

Download Python 3.9 or newer from https://www.python.org/downloads/

During Windows installation, **tick "Add Python to PATH"**.

Verify: open a terminal and type:
```
python --version
```

### Step 2: Install Tesseract OCR (for image scanning)

**macOS:**
```bash
brew install tesseract
```

**Ubuntu / Debian Linux:**
```bash
sudo apt install tesseract-ocr
```

**Windows:**
1. Download the installer from: https://github.com/tesseract-ocr/tesseract
2. Run the installer (choose "Additional language data" > English)
3. Add the install folder (e.g. `C:\Program Files\Tesseract-OCR`) to your system PATH

> **Note:** If Tesseract is not installed, Medico.AI will automatically fall back to EasyOCR (slower but works without Tesseract).

### Step 3: Download and set up Medico.AI

```bash
# Download
git clone https://github.com/your-username/medico-ai.git
cd medico-ai

# Automated setup
python setup.py
```

This creates a virtual environment and installs all required packages.

---

## 3. Starting the App

### Using the one-command launcher (recommended)

```bash
# Activate the virtual environment first
source venv/bin/activate       # macOS / Linux
venv\Scripts\activate          # Windows

# Start everything
python start.py
```

After a few seconds, you'll see:
```
✅  Medico.AI is running!
📊  UI  →  http://localhost:8501
🔌  API →  http://localhost:8000/docs
```

Open **http://localhost:8501** in your browser.

### Starting manually (two terminals)

```bash
# Terminal 1 — API backend
python backend/app.py

# Terminal 2 — Streamlit UI
streamlit run frontend/app.py
```

### Stopping the app

Press **Ctrl + C** in the terminal where `start.py` is running.

---

## 4. Using the App

### 4.1 Home Page & Quick Search

The **Home** page loads by default. It has a **Quick Search** box at the bottom.

1. Type any medicine name (brand or generic) — e.g. `Crocin`, `Atorvastatin`, `Augmentin`
2. Press **Enter**
3. Results appear instantly below

This is the fastest way to check a single medicine.

---

### 4.2 Uploading a Prescription Image

Go to **📸 Upload Prescription** in the left sidebar.

#### Step-by-step

1. Click **"Choose prescription image"**
2. Select a JPG, PNG, or WebP photo of your prescription
3. Choose your preferred **OCR engine**:
   - **auto** *(recommended)* — tries Tesseract, falls back to EasyOCR
   - **tesseract** — faster, better for printed prescriptions
   - **easyocr** — better for handwritten or unclear text
4. Click **"🔍 Analyse Prescription"**
5. Wait 5–30 seconds (EasyOCR is slower on first run)
6. Review the extracted medicines and alternatives

#### What you see after analysis

- **Raw OCR Text** (expandable) — the raw text the AI extracted from your image
- **Medicines extracted** — the names the NLP pipeline found
- **Results** — price comparison table for each medicine (see Section 5)

---

### 4.3 Entering Prescription Text Manually

On the **📸 Upload Prescription** page, click the **"✏️ Type / Paste Text"** tab.

This is useful when:
- Your prescription is already typed (WhatsApp, PDF, etc.)
- OCR quality is poor and you want to correct it manually

**Enter medicine names one per line, for example:**
```
Tab Crocin 500mg BD
Cap Augmentin 625mg TDS
Tab Lipitor 10mg OD
Syp Benadryl 10ml HS
```

Click **"🔍 Find Alternatives"** to get results.

---

### 4.4 Single Medicine Search

Go to **🔍 Search Medicine** in the sidebar.

Type any name — brand, generic, or even a partial name:
- `Crocin` → finds Paracetamol alternatives
- `Paracetamol` → same result
- `Augment` → fuzzy-matches Augmentin
- `Lipitor` → finds Atorvastatin alternatives

---

### 4.5 Browsing the Medicine Database

Go to **📊 Browse Database** in the sidebar.

You can:
- **Search by name or salt** — type in the search box
- **Filter by category** — select from the dropdown (Antibiotic, Antidiabetic, etc.)
- **Sort any column** — click a column header
- **View savings** — the "Savings %" column shows how much cheaper generics are

The database currently contains 100+ common Indian medicines across all major categories.

---

## 5. Understanding the Results

### Summary Cards

At the top of every result set, you'll see 4 summary cards:

| Card | Meaning |
|------|---------|
| **Medicines Identified** | How many medicines were found and matched |
| **Est. Branded Cost / Strip** | Approximate cost if you buy all branded versions |
| **Est. Generic Cost / Strip** | Approximate cost if you switch to cheapest generics |
| **Potential Savings** | The difference, in ₹ and percentage |

> ⚠️ These are **estimates per unit** (per tablet/capsule). Multiply by your prescribed quantity.

### Per-Medicine Results

Each medicine has its own expandable section showing:

#### Match badges
- **✓ Exact Match** — the brand name was found exactly in the database
- **~ Fuzzy (N%)** — a close match was found; N% is the confidence level
- **~ Generic Match** — matched via generic/salt name

#### Alternatives table

| Column | Meaning |
|--------|---------|
| Option | Medicine name (⭐ = cheapest option) |
| Generic Name | Active ingredient (INN name) |
| Manufacturer | Who makes it |
| Form | Dosage form and strength |
| Price / Unit (₹) | Retail price per tablet/capsule |
| Generic Price (₹) | What unbranded generics typically cost |
| Jan Aushadhi (₹) | Government Jan Aushadhi store price |
| Savings vs Brand | How much cheaper vs the most expensive brand |

#### Green success box

Shows the single cheapest option and exact savings.

---

## 6. Tips for Best OCR Results

Good image quality dramatically improves extraction accuracy.

### Photography tips

| Do ✅ | Don't ❌ |
|-------|---------|
| Use natural daylight | Use flash (causes glare) |
| Lay prescription flat | Hold it at an angle |
| Fill the frame | Leave lots of background |
| Shoot straight above | Shoot from the side |
| Keep hands steady | Let image blur |
| Use 8+ MP camera | Use heavily compressed images |

### Prescription types

| Type | Recommended Engine |
|------|--------------------|
| Printed / typed | tesseract or auto |
| Handwritten (clear) | auto |
| Handwritten (unclear) | easyocr |
| Low light / old paper | easyocr |

### If OCR misses medicines

Use the **"✏️ Type / Paste Text"** tab and type the medicine names yourself — this bypasses OCR entirely.

---

## 7. Troubleshooting

### "Backend Offline" warning in sidebar

The FastAPI backend is not running. Fix:

```bash
# Make sure your virtual environment is activated
source venv/bin/activate

# Start the backend
python backend/app.py
```

Leave that terminal open and refresh the browser.

### "No text could be extracted from the image"

- Try a clearer, brighter photo
- Switch OCR engine to `easyocr`
- Type the medicines manually in the text tab

### EasyOCR is very slow on first run

EasyOCR downloads a language model (~100 MB) on first use. Subsequent runs are faster. This is a one-time download.

### "No match found for X"

The medicine name is not in the database. You can:
1. Try a shorter or alternative spelling
2. Search for the generic/salt name instead
3. [Contribute the medicine](CONTRIBUTING.md#adding-medicines-to-the-database) to the database

### Tesseract not found on Windows

1. Download from https://github.com/tesseract-ocr/tesseract
2. Install with default options
3. Add `C:\Program Files\Tesseract-OCR` to your **System PATH**
4. Restart your terminal and try again

Alternatively, set the path in your `.env` file:
```
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Port already in use

```
# Kill whatever is on port 8000 or 8501
# macOS / Linux:
lsof -ti:8000 | xargs kill -9
lsof -ti:8501 | xargs kill -9

# Windows (PowerShell):
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process
```

---

## 8. FAQ

**Q: Is my prescription data uploaded anywhere?**
A: No. Medico.AI runs entirely on your local computer. No images or text are sent to any external server.

**Q: Are the prices accurate?**
A: Prices are approximate and based on market data at the time of the last database update. Always verify with your local pharmacy or the NPPA website.

**Q: Can I trust generic medicines?**
A: Yes — generics sold in India must meet the same quality standards as branded drugs (same active ingredient, same dosage, same form). They are regulated by CDSCO. However, always consult your doctor or pharmacist before switching.

**Q: The app found a medicine but the savings seem wrong.**
A: Prices vary by city, pharmacy, and whether you buy a full strip or single units. Use the savings figure as a guide, not a guarantee.

**Q: Can I add more medicines to the database?**
A: Yes! See [CONTRIBUTING.md](CONTRIBUTING.md#adding-medicines-to-the-database). Pull requests are welcome.

**Q: Does this work for injections and syrups?**
A: The database includes some injections and syrups. OCR for handwritten prescriptions involving liquid medicines can be less reliable — use the manual text input for best results.

**Q: My prescription is in Hindi / regional language.**
A: Current OCR is optimised for English. Hindi support is on the roadmap. For now, type the medicine names manually in English.

**Q: The app is slow.**
A: EasyOCR is CPU-intensive. If you're on a slow machine, use `tesseract` as the OCR engine (faster). The first EasyOCR run also downloads a model file.

---

## 9. Important Disclaimers

> **Medico.AI is an informational tool only.**

- It does **not** replace the advice of a qualified doctor, pharmacist, or other healthcare professional.
- **Never switch medicines** without consulting your prescribing doctor or a registered pharmacist, even if the active ingredient appears identical.
- Some conditions require specific branded formulations (bioavailability differences, extended-release mechanisms, etc.).
- Prices shown are **approximate** and may vary by location, pharmacy, and availability.
- The database may not include all available medicines or the most recent price changes.
- The developers of Medico.AI accept **no liability** for decisions made based on information provided by this tool.

**For medical emergencies, call 112 (India national emergency number).**

---

*Medico.AI — Built with ❤️ to make healthcare affordable in India.*
