# 🤝 Contributing to Medico.AI

First off — thank you for taking the time to contribute! 🎉
Medico.AI is an open-source project aimed at making healthcare more affordable in India.
Every contribution, big or small, matters.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Adding Medicines to the Database](#adding-medicines-to-the-database)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Bugs](#reporting-bugs)
- [Requesting Features](#requesting-features)

---

## 📜 Code of Conduct

We follow a simple rule: **be kind and respectful**.
Discrimination, harassment, or hostile behaviour of any kind will not be tolerated.

---

## 💡 How Can I Contribute?

### 🐛 Bug Reports
Open an issue with the label `bug`. Include:
- Steps to reproduce
- Expected vs actual behaviour
- Screenshots (if UI-related)
- Your OS, Python version

### ✨ Feature Requests
Open an issue with the label `enhancement`. Describe:
- The problem you're solving
- Proposed solution
- Any alternatives you considered

### 💊 Adding Medicine Data
The most impactful contribution! See [Adding Medicines](#adding-medicines-to-the-database).

### 🔧 Code Contributions
- Bug fixes
- New features (please open an issue first)
- Performance improvements
- Tests
- Documentation

---

## 🛠️ Development Setup

```bash
# 1. Fork and clone the repo
git clone https://github.com/YOUR_USERNAME/medico-ai.git
cd medico-ai

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies (includes dev extras)
pip install -r requirements.txt

# 4. Install Tesseract OCR
# macOS: brew install tesseract
# Linux: sudo apt install tesseract-ocr
# Windows: https://github.com/tesseract-ocr/tesseract

# 5. Run the app in development mode
python start.py
```

The API will reload automatically on code changes (`--reload` flag).

---

## 📁 Project Structure

```
medico-ai/
├── backend/
│   ├── app.py                  # FastAPI app — add routes here
│   ├── routes/                 # Endpoint handlers
│   ├── services/
│   │   ├── ocr.py              # Add new OCR engines here
│   │   ├── nlp.py              # Improve medicine extraction here
│   │   └── matcher.py          # Improve matching logic here
│   └── database/db.py          # Add new DB models here
├── frontend/app.py             # All Streamlit pages live here
├── data/medicines.csv          # Master drug database
└── tests/                      # (planned) pytest suite
```

---

## 🎨 Coding Standards

### Python
- Format with **black**: `black .`
- Lint with **flake8**: `flake8 --max-line-length=100`
- Type-hint all public functions
- Docstrings on all modules, classes, and public methods (Google style)

```python
def find_alternatives(medicine_name: str, db: Session, top_n: int = 5) -> MedicineMatch:
    """
    Map a medicine name to cheaper alternatives.

    Args:
        medicine_name: Brand or generic name from OCR.
        db: SQLAlchemy session.
        top_n: Maximum alternatives to return.

    Returns:
        MedicineMatch with ranked alternatives.
    """
```

### Commits
Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add voice input support
fix: handle empty OCR output gracefully
docs: update setup instructions for Windows
data: add 20 cardiovascular medicines
refactor: split matcher into fuzzy and salt modules
test: add tests for NLP extraction
```

### Branch Naming

```
feature/voice-input
fix/empty-ocr-crash
data/add-antibiotics
docs/user-manual-update
```

---

## 💊 Adding Medicines to the Database

The medicine database lives in `data/medicines.csv`. This is the **highest-impact** contribution.

### CSV Column Reference

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| `brand_name` | string | `Crocin` | Exact brand name as sold in India |
| `generic_name` | string | `Paracetamol` | INN / generic name |
| `salt_composition` | string | `Paracetamol 500mg` | Full composition string |
| `manufacturer` | string | `GSK` | Marketing company |
| `brand_price_per_unit` | float | `2.50` | MRP per tablet/capsule/unit (₹) |
| `unit_type` | string | `tablet` | tablet / capsule / syrup / injection / sachet |
| `generic_price_per_unit` | float | `0.50` | Typical generic market price (₹) |
| `jan_aushadhi_price` | float | `0.35` | Jan Aushadhi store price (₹); can be empty |
| `category` | string | `Analgesic/Antipyretic` | Pharmacological category |
| `strength` | string | `500mg` | Dosage strength |
| `form` | string | `tablet` | Dosage form |

### Price Verification Sources
Use these official sources for price data:
- **NPPA (National Pharmaceutical Pricing Authority)**: https://www.nppaindia.nic.in/
- **Jan Aushadhi**: https://janaushadhi.gov.in/
- **Pharmeasy / 1mg**: for retail brand prices
- **CIMS India**: for composition data

### Adding Rows
Add new rows to the bottom of `data/medicines.csv`.
The app seeds the database from this file at startup.

> ⚠️ Please verify prices from at least two sources before submitting.

---

## 🔀 Submitting a Pull Request

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit using Conventional Commits.

3. **Test your changes**:
   ```bash
   python start.py   # smoke test
   # Ensure /docs API still loads
   # Ensure Streamlit UI still works
   ```

4. **Push and open a PR**:
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a Pull Request on GitHub against `main`.

5. **PR checklist**:
   - [ ] Code follows the style guide (black, flake8)
   - [ ] New functions/modules have docstrings
   - [ ] Medicine data verified from official sources (if data PR)
   - [ ] No API keys or personal data committed
   - [ ] `requirements.txt` updated if new packages added

---

## 🐛 Reporting Bugs

Open an issue at `https://github.com/your-username/medico-ai/issues` with:

```
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behaviour.

**Expected behaviour**
What you expected to happen.

**Screenshots**
If applicable.

**Environment**
- OS: [e.g. macOS 14, Ubuntu 22.04, Windows 11]
- Python version: [e.g. 3.11.2]
- Browser: [e.g. Chrome 120]
```

---

## 💬 Requesting Features

Open an issue with the `enhancement` label and include:

```
**Is your feature request related to a problem?**
Clearly describe the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Alternatives considered**
Any alternative solutions you've considered.

**Additional context**
Mockups, examples, references.
```

---

## 🙏 Thank You

Every contribution helps make healthcare more affordable in India.
Whether it's fixing a typo or adding 100 medicines — it all counts.

**Happy coding!** 💊
