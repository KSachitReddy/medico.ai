# Contributing to medico.ai 🤝

Thank you for your interest in contributing to **medico.ai** — a civic tech platform helping Indian citizens access affordable generic medicines. Every contribution, big or small, directly helps people save money on healthcare.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Setting Up the Development Environment](#setting-up-the-development-environment)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Adding Medicine Data](#adding-medicine-data)
- [Contact](#contact)

---

## Code of Conduct

This project is built for public benefit. We expect all contributors to:

- Be respectful and inclusive in all interactions
- Focus on what is best for citizens and end users
- Accept constructive criticism gracefully
- Never add commercially motivated content — this platform is ad-free and non-commercial

---

## How Can I Contribute?

There are many ways to contribute to medico.ai:

| Type | Examples |
|---|---|
| 🐛 **Bug fixes** | Fix broken search, UI glitches, Firebase errors |
| ✨ **New features** | Store locator, dosage filter, language support |
| 💊 **Medicine data** | Add more drugs to the database |
| 🌐 **Translations** | Add Telugu, Hindi, Tamil language support |
| 📖 **Documentation** | Improve README, add code comments |
| 🎨 **UI/UX** | Improve design, accessibility, mobile responsiveness |
| 🧪 **Testing** | Write unit tests, report bugs |

---

## Setting Up the Development Environment

### Prerequisites

Make sure you have installed:
- **Node.js** v18 or higher — [nodejs.org](https://nodejs.org)
- **npm** v9 or higher
- **Python** 3.10 or higher
- **uv** (Python package manager)
- **Git**

### Step 1 — Fork the Repository

Click the **Fork** button at the top right of the GitHub repo page. This creates your own copy of the project.

### Step 2 — Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/medico-ai.git
cd medico-ai
```

### Step 3 — Add Upstream Remote

This lets you pull in future updates from the original repo:

```bash
git remote add upstream https://github.com/ORIGINAL_USERNAME/medico-ai.git
```

### Step 4 — Install Node Dependencies

```bash
npm install
```

### Step 5 — Install Python Dependencies

Install uv if you don't have it:

```bash
# macOS / Linux
curl -Lsf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then install Python packages:

```bash
uv pip install -r requirements.txt
```

### Step 6 — Set Up Environment Variables

```bash
cp .env.example .env
```

Fill in your own API keys in `.env`:

```env
VITE_FIREBASE_API_KEY=your_key
VITE_FIREBASE_AUTH_DOMAIN=your_domain
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_bucket
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
VITE_ANTHROPIC_API_KEY=your_anthropic_key
VITE_GOOGLE_MAPS_API_KEY=your_maps_key
```

> ⚠️ Never commit your `.env` file. It is already in `.gitignore`.

### Step 7 — Seed the Database

```bash
node src/data/seed.js
```

### Step 8 — Start the Dev Server

```bash
npm run dev
```

App runs at `http://localhost:5173`

---

## Project Structure

```
medico.ai/
├── src/
│   ├── components/       # Reusable UI components
│   ├── pages/            # Page-level components
│   ├── services/         # Firebase, Anthropic API, search logic
│   └── data/             # Medicine data and seed script
├── scripts/              # Python data cleaning scripts
├── public/               # Static assets
├── .env.example          # Environment variable template
├── requirements.txt      # Python dependencies
└── package.json          # Node dependencies
```

---

## Coding Standards

### JavaScript / React

- Use **functional components** with hooks — no class components
- Use **camelCase** for variables and functions: `medicineData`, `handleSearch`
- Use **PascalCase** for component names: `MedicineCard`, `SearchBar`
- Keep components small — if a component exceeds 150 lines, break it up
- Add a comment for any non-obvious logic

```jsx
// ✅ Good
const MedicineCard = ({ medicine }) => {
  return <div className="...">{medicine.name}</div>;
};

// ❌ Avoid
const medicinecard = (props) => {
  return <div>{props.medicine.name}</div>;
};
```

### CSS / Tailwind

- Use Tailwind utility classes only — no custom CSS files unless absolutely necessary
- Keep className strings readable — break long ones across lines

### Python (Data Scripts)

- Follow **PEP 8** style guide
- Use **snake_case** for variables: `generic_name`, `price_per_strip`
- Add docstrings to all functions

```python
# ✅ Good
def clean_medicine_data(df):
    """Remove duplicates and normalize column names from Jan Aushadhi Excel."""
    df = df.drop_duplicates()
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    return df
```

### Commit Messages

Use clear, descriptive commit messages:

```
✅ feat: add fuzzy search for medicine names
✅ fix: correct price calculation in savings calculator
✅ docs: update README installation steps
✅ data: add 50 new medicines to database

❌ fix stuff
❌ update
❌ changes
```

Format: `type: short description`
Types: `feat`, `fix`, `docs`, `data`, `style`, `refactor`, `test`

---

## Submitting a Pull Request

### Step 1 — Sync with Upstream

Before starting work, make sure your fork is up to date:

```bash
git fetch upstream
git checkout main
git merge upstream/main
```

### Step 2 — Create a Feature Branch

Never work directly on `main`. Create a branch named after what you're building:

```bash
git checkout -b feat/store-locator
git checkout -b fix/search-not-working
git checkout -b data/add-diabetes-medicines
```

### Step 3 — Make Your Changes

Write your code, test it locally, make sure the app still runs without errors.

### Step 4 — Commit Your Changes

```bash
git add .
git commit -m "feat: add Jan Aushadhi store locator with Google Maps"
```

### Step 5 — Push to Your Fork

```bash
git push origin feat/store-locator
```

### Step 6 — Open a Pull Request

1. Go to your fork on GitHub
2. Click **"Compare & pull request"**
3. Fill in the PR template:
   - What does this PR do?
   - What issue does it fix? (if any)
   - Screenshots (if UI change)
4. Submit — a maintainer will review it

### Pull Request Checklist

Before submitting, confirm:

- [ ] App runs without errors locally (`npm run dev`)
- [ ] No `.env` file or API keys committed
- [ ] Code follows the style guidelines above
- [ ] Commit message is clear and descriptive
- [ ] Screenshots included if it's a UI change

---

## Reporting Bugs

Found something broken? Please open a GitHub Issue with:

1. **What happened** — describe the bug clearly
2. **What you expected** — what should have happened
3. **Steps to reproduce** — how can we recreate it
4. **Screenshots** — if applicable
5. **Environment** — browser, OS, Node version

**Issue title format:** `[BUG] Search returns no results for valid medicine name`

---

## Suggesting Features

Have an idea? Open a GitHub Issue with:

1. **Feature description** — what should it do?
2. **Who benefits** — which users does this help?
3. **Why it matters** — how does it improve the civic mission?

**Issue title format:** `[FEATURE] Add Hindi language support`

---

## Adding Medicine Data

This is one of the most impactful contributions. More medicines = more citizens helped.

### Data Format

Add medicines to `src/data/medicines.json` in this format:

```json
{
  "id": "metformin_500",
  "generic_name": "Metformin",
  "strength": "500mg",
  "category": "Diabetes",
  "otc": false,
  "branded": [
    { "name": "Glycomet", "price_per_strip": 40, "tablets": 10 },
    { "name": "Glucophage", "price_per_strip": 55, "tablets": 10 }
  ],
  "generics": [
    { "name": "Metformin IP (Jan Aushadhi)", "price_per_strip": 5, "tablets": 10 },
    { "name": "Metformin 500", "price_per_strip": 12, "tablets": 10 }
  ]
}
```

### Rules for Data Contributions

- ✅ Only add medicines with **verified prices** from Jan Aushadhi official list or pharmacy websites
- ✅ Always include at least one Jan Aushadhi generic
- ✅ Cite your source in the PR description
- ❌ Do not add unverified or estimated prices
- ❌ Do not add prescription-only (Rx) medicines without a clear disclaimer

---

## Contact

For questions, reach out via:
- GitHub Issues — preferred for bugs and features
- Email — [your-email@example.com]

---

*medico.ai is built for the people, by the people. Thank you for contributing.*
