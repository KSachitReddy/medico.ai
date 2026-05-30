"""
Medico.AI — Streamlit Frontend
Run: streamlit run frontend/app.py
"""
from __future__ import annotations

import io
import os
import sys

import requests
import pandas as pd
import streamlit as st
from PIL import Image

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Medico.AI — Smart Medicine Cost Optimizer",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Backend URL ──────────────────────────────────────────────────────────────
API_BASE = os.getenv("MEDICO_API_URL", "http://localhost:8000/api/v1")

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* Global */
body { font-family: 'Segoe UI', sans-serif; }

/* Hero banner */
.hero {
    background: linear-gradient(135deg, #1a6b3c 0%, #0d4a2a 100%);
    color: white;
    padding: 2rem 2.5rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    text-align: center;
}
.hero h1 { font-size: 2.8rem; margin: 0; }
.hero p  { font-size: 1.1rem; margin-top: 0.5rem; opacity: 0.9; }

/* Metric cards */
.metric-card {
    background: #f0faf4;
    border: 1px solid #b2dfcb;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    text-align: center;
}
.metric-card .value { font-size: 2rem; font-weight: 700; color: #1a6b3c; }
.metric-card .label { font-size: 0.85rem; color: #555; }

/* Medicine result card */
.med-card {
    border: 1px solid #d4edda;
    border-left: 5px solid #28a745;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
    background: #f9fffa;
}
.med-card.warning {
    border-left-color: #ffc107;
    background: #fffdf0;
}
.med-card.danger {
    border-left-color: #dc3545;
    background: #fff5f5;
}

/* Alt row */
.alt-best {
    background: #e6f4ea;
    border-radius: 8px;
    padding: 0.4rem 0.8rem;
    font-weight: 600;
    color: #155724;
}

/* Badge */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-left: 6px;
}
.badge-green  { background: #d4edda; color: #155724; }
.badge-yellow { background: #fff3cd; color: #856404; }
.badge-red    { background: #f8d7da; color: #721c24; }
</style>
""",
    unsafe_allow_html=True,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def savings_badge(pct: float) -> str:
    if pct >= 50:
        return f'<span class="badge badge-green">💰 Save {pct:.0f}%</span>'
    elif pct >= 20:
        return f'<span class="badge badge-yellow">💰 Save {pct:.0f}%</span>'
    elif pct > 0:
        return f'<span class="badge badge-red">Save {pct:.0f}%</span>'
    return ""


def _post_image(image_bytes: bytes, content_type: str, engine: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/upload",
        files={"file": ("prescription.jpg", image_bytes, content_type)},
        data={"ocr_engine": engine},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def _post_text(text: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/search-text",
        data={"prescription_text": text},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _search_medicine(name: str) -> dict:
    resp = requests.get(
        f"{API_BASE}/medicines/search",
        params={"name": name},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def _list_medicines(q: str = "", category: str = "") -> list:
    params = {"limit": 200}
    if q:
        params["q"] = q
    if category:
        params["category"] = category
    resp = requests.get(f"{API_BASE}/medicines", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _get_categories() -> list:
    try:
        resp = requests.get(f"{API_BASE}/categories", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def render_results(results: list, session_id: str = ""):
    """Render medicine match results nicely."""
    found = [r for r in results if r.get("match_type") != "none" and not r.get("error")]
    not_found = [r for r in results if r.get("error") or r.get("match_type") == "none"]

    if not found and not not_found:
        st.info("No medicines found in the prescription. Try entering medicine names manually below.")
        return

    # Summary metrics
    total_brand = sum(
        r["alternatives"][0]["brand_price"] if r.get("alternatives") else 0
        for r in found
    )
    total_cheapest = sum(
        r["alternatives"][0]["brand_price"] if r.get("alternatives") else 0
        for r in found
    )
    # recalculate cheapest
    total_cheapest = 0.0
    for r in found:
        if r.get("alternatives"):
            total_cheapest += r["alternatives"][0]["brand_price"]

    # The "original" prescription cost = matched brand price (first alt is cheapest, we need the original)
    # Let's find matched brand price
    original_total = 0.0
    for r in found:
        alts = r.get("alternatives", [])
        # find the matched brand in alts
        mb = r.get("matched_brand", "")
        matched_alt = next((a for a in alts if a["brand_name"].lower() == mb.lower()), None)
        if matched_alt:
            original_total += matched_alt["brand_price"]
        elif alts:
            # fallback: max price
            original_total += max(a["brand_price"] for a in alts)

    potential_savings = max(0.0, original_total - total_cheapest)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f'<div class="metric-card"><div class="value">{len(found)}</div>'
            f'<div class="label">Medicines Identified</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="metric-card"><div class="value">₹{original_total:.0f}</div>'
            f'<div class="label">Est. Branded Cost / Strip</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f'<div class="metric-card"><div class="value">₹{total_cheapest:.0f}</div>'
            f'<div class="label">Est. Generic Cost / Strip</div></div>',
            unsafe_allow_html=True,
        )
    with col4:
        pct = (potential_savings / original_total * 100) if original_total > 0 else 0
        st.markdown(
            f'<div class="metric-card"><div class="value">₹{potential_savings:.0f}</div>'
            f'<div class="label">Potential Savings ({pct:.0f}%)</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Per-medicine results
    for r in found:
        alts = r.get("alternatives", [])
        matched = r.get("matched_brand", r["query"])
        salt = r.get("salt_composition", "")
        match_type = r.get("match_type", "")
        score = r.get("fuzzy_score", 100)

        badge_html = ""
        if match_type == "exact":
            badge_html = '<span class="badge badge-green">✓ Exact Match</span>'
        elif match_type == "fuzzy":
            badge_html = f'<span class="badge badge-yellow">~ Fuzzy ({score}%)</span>'
        elif match_type == "salt":
            badge_html = '<span class="badge badge-yellow">~ Generic Match</span>'

        with st.expander(f"💊 {matched}  {badge_html}", expanded=True):
            if salt:
                st.caption(f"**Salt / Composition:** {salt}")

            if alts:
                # Build table
                rows = []
                for i, a in enumerate(alts):
                    tag = " ⭐ Best" if i == 0 else ""
                    rows.append(
                        {
                            "Option": f"{a['brand_name']}{tag}",
                            "Generic Name": a["generic_name"],
                            "Manufacturer": a["manufacturer"],
                            "Form": f"{a['form']} {a['strength']}",
                            "Price / Unit (₹)": a["brand_price"],
                            "Generic Price (₹)": a["generic_price"],
                            "Jan Aushadhi (₹)": a.get("jan_aushadhi_price") or "N/A",
                            "Savings vs Brand": f"₹{a['savings_vs_brand']} ({a['savings_pct']:.0f}%)",
                        }
                    )
                df = pd.DataFrame(rows)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Price / Unit (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                        "Generic Price (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    },
                )

                best = alts[0]
                st.success(
                    f"✅ **Cheapest option:** {best['brand_name']} "
                    f"@ ₹{best['brand_price']}/unit "
                    f"— saves ₹{best['savings_vs_brand']} ({best['savings_pct']:.0f}%) vs branded"
                )
            else:
                st.warning("No cheaper alternatives found in database.")

    if not_found:
        st.markdown("### ❓ Not Identified")
        for r in not_found:
            st.warning(f"**{r['query']}** — {r.get('error', 'No match found')}")


# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image(
        "https://img.icons8.com/fluency/96/hospital.png",
        width=64,
    )
    st.markdown("## Medico.AI")
    st.caption("Smart Medicine Cost Optimizer for India")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["🏠 Home", "📸 Upload Prescription", "🔍 Search Medicine", "📊 Browse Database", "ℹ️ About"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    # Backend status
    try:
        r = requests.get(f"http://localhost:8000/health", timeout=2)
        if r.ok:
            st.success("🟢 Backend Online")
        else:
            st.error("🔴 Backend Error")
    except Exception:
        st.error("🔴 Backend Offline\nStart with:\n```\npython backend/app.py\n```")

    st.markdown("---")
    st.caption("⚕️ Always consult a qualified pharmacist or doctor before switching medicines.")


# ── Pages ────────────────────────────────────────────────────────────────────

# ── HOME ─────────────────────────────────────────────────────────────────────
if page == "🏠 Home":
    st.markdown(
        """
<div class="hero">
  <h1>💊 Medico.AI</h1>
  <p>AI-powered prescription decoder & generic medicine cost optimizer for India</p>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 📸 Upload")
        st.write("Photograph or scan your prescription. Our OCR engine reads it instantly.")
    with c2:
        st.markdown("### 🤖 AI Decode")
        st.write("NLP extracts medicine names. Fuzzy matching maps brands to generic salt compositions.")
    with c3:
        st.markdown("### 💰 Save")
        st.write("Get ranked cheaper alternatives including Jan Aushadhi store prices.")

    st.markdown("---")
    st.markdown("### 🚀 Quick Search")
    quick = st.text_input("Enter a medicine name (e.g. Crocin, Augmentin, Lipitor)…")
    if quick:
        try:
            data = _search_medicine(quick)
            render_results([data])
        except requests.HTTPError as e:
            st.error(f"API error: {e}")
        except requests.ConnectionError:
            st.error("Cannot reach backend. Is `python backend/app.py` running?")

    st.markdown("---")
    st.info(
        "**Disclaimer:** Medico.AI is an informational tool only. "
        "Always consult a registered pharmacist or doctor before switching medicines."
    )

# ── UPLOAD ───────────────────────────────────────────────────────────────────
elif page == "📸 Upload Prescription":
    st.title("📸 Upload Prescription")
    st.write("Upload a photo or scan of your prescription. Supported formats: JPG, PNG, WebP, BMP.")

    tab_img, tab_text = st.tabs(["📷 Image Upload", "✏️ Type / Paste Text"])

    with tab_img:
        engine = st.selectbox(
            "OCR Engine",
            ["auto", "tesseract", "easyocr"],
            help="'auto' tries Tesseract first, falls back to EasyOCR.",
        )
        uploaded = st.file_uploader(
            "Choose prescription image",
            type=["jpg", "jpeg", "png", "webp", "bmp"],
        )

        if uploaded:
            col_img, col_info = st.columns([1, 2])
            with col_img:
                img = Image.open(uploaded)
                st.image(img, caption="Uploaded Prescription", use_column_width=True)
            with col_info:
                st.write(f"**File:** {uploaded.name}")
                st.write(f"**Size:** {uploaded.size / 1024:.1f} KB")
                st.write(f"**OCR Engine:** {engine}")

            if st.button("🔍 Analyse Prescription", type="primary"):
                with st.spinner("Running OCR and AI analysis…"):
                    try:
                        uploaded.seek(0)
                        raw = uploaded.read()
                        data = _post_image(raw, uploaded.type or "image/jpeg", engine)

                        with st.expander("📄 Raw OCR Text", expanded=False):
                            st.code(data.get("raw_text", "(empty)"))
                            st.caption(
                                f"Engine: {data['ocr_engine']} | Confidence: {data['ocr_confidence']}%"
                            )

                        st.markdown(f"**Medicines extracted:** {data['total_medicines_found']}")
                        if data.get("extracted_medicines"):
                            st.write(", ".join(data["extracted_medicines"]))

                        st.markdown("---")
                        render_results(data.get("results", []))

                    except requests.HTTPError as e:
                        st.error(f"Server error {e.response.status_code}: {e.response.text}")
                    except requests.ConnectionError:
                        st.error("Backend offline. Run `python backend/app.py` first.")
                    except Exception as e:
                        st.error(f"Unexpected error: {e}")

    with tab_text:
        st.write("Type or paste medicine names or full prescription text:")
        text_input = st.text_area(
            "Prescription text",
            height=200,
            placeholder="e.g.\nTab Crocin 500mg BD\nCap Augmentin 625mg TDS\nTab Atorva 10mg OD",
        )
        if st.button("🔍 Find Alternatives", type="primary", key="text_btn"):
            if not text_input.strip():
                st.warning("Please enter some text.")
            else:
                with st.spinner("Analysing…"):
                    try:
                        data = _post_text(text_input)
                        render_results(data.get("results", []))
                    except requests.ConnectionError:
                        st.error("Backend offline.")
                    except Exception as e:
                        st.error(f"Error: {e}")

# ── SEARCH ───────────────────────────────────────────────────────────────────
elif page == "🔍 Search Medicine":
    st.title("🔍 Search Medicine")
    st.write("Enter any brand or generic name — we'll find cheaper alternatives.")

    name = st.text_input("Medicine name", placeholder="e.g. Lipitor, Atorvastatin, Augmentin…")

    if name:
        try:
            data = _search_medicine(name)
            render_results([data])
        except requests.HTTPError as e:
            st.error(f"API error: {e.response.text}")
        except requests.ConnectionError:
            st.error("Backend offline. Run `python backend/app.py` first.")

# ── BROWSE ───────────────────────────────────────────────────────────────────
elif page == "📊 Browse Database":
    st.title("📊 Medicine Database")

    cats = ["All"] + _get_categories()
    col_q, col_cat = st.columns([3, 1])
    with col_q:
        q = st.text_input("Search by name / salt", placeholder="e.g. Paracetamol")
    with col_cat:
        cat = st.selectbox("Category", cats)

    try:
        medicines = _list_medicines(q=q, category=(cat if cat != "All" else ""))
        if medicines:
            df = pd.DataFrame(medicines)
            df["Savings (Brand→Generic)"] = (
                (df["brand_price_per_unit"] - df["generic_price_per_unit"]).round(2)
            )
            df["Savings %"] = (
                (df["Savings (Brand→Generic)"] / df["brand_price_per_unit"] * 100).round(1)
            )
            st.dataframe(
                df[
                    [
                        "brand_name", "generic_name", "salt_composition",
                        "strength", "form", "manufacturer", "category",
                        "brand_price_per_unit", "generic_price_per_unit",
                        "jan_aushadhi_price", "Savings %",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "brand_price_per_unit": st.column_config.NumberColumn("Brand Price (₹)", format="₹%.2f"),
                    "generic_price_per_unit": st.column_config.NumberColumn("Generic Price (₹)", format="₹%.2f"),
                    "jan_aushadhi_price": st.column_config.NumberColumn("Jan Aushadhi (₹)", format="₹%.2f"),
                    "Savings %": st.column_config.NumberColumn(format="%.1f%%"),
                },
            )
            st.caption(f"Showing {len(medicines)} records")
        else:
            st.info("No medicines found. Try a different search.")
    except requests.ConnectionError:
        st.error("Backend offline.")

# ── ABOUT ────────────────────────────────────────────────────────────────────
elif page == "ℹ️ About":
    st.title("ℹ️ About Medico.AI")
    st.markdown(
        """
## 🏥 What is Medico.AI?

**Medico.AI** is an open-source, AI-powered tool designed to help Indian patients
discover cheaper generic alternatives to the branded medicines they are prescribed.

### 🔬 How it works

| Step | What happens |
|------|-------------|
| **Upload** | You photograph or scan your prescription |
| **OCR** | Tesseract / EasyOCR extracts text from the image |
| **NLP** | A rule-based NLP pipeline identifies medicine names |
| **Matching** | RapidFuzz maps each name to our database using brand → generic → salt matching |
| **Ranking** | Alternatives are sorted cheapest-first and savings are calculated |

### 💊 Why this matters

Branded medicines in India can cost **5–20× more** than their generic equivalents with
identical salt compositions.  Most patients are unaware they can ask for generics, and many
pharmacists push high-margin branded drugs.

### 🏛️ Jan Aushadhi

The Government of India's **Jan Aushadhi** initiative sells quality generics at 50–90% lower
prices than brands.  Medico.AI includes Jan Aushadhi prices in all comparisons.

### ⚙️ Tech Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Streamlit
- **OCR**: Tesseract + EasyOCR
- **NLP**: Rule-based + RapidFuzz
- **Data**: 100+ common Indian medicines with live price data

### ⚠️ Disclaimer

Medico.AI is an **informational tool only**.  Always consult a registered pharmacist or
qualified doctor before changing any medication.  We do not dispense medical advice.

---
Built with ❤️ for affordable healthcare in India.
"""
    )
