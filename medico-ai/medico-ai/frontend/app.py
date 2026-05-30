"""
Medico.AI — Streamlit Frontend v2.0
Run: streamlit run frontend/app.py
"""
from __future__ import annotations

import io
import os

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

API_BASE = os.getenv("MEDICO_API_URL", "http://localhost:8000/api/v1")

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
body { font-family: 'Segoe UI', sans-serif; }

.hero {
    background: linear-gradient(135deg, #1a6b3c 0%, #0d4a2a 100%);
    color: white; padding: 2rem 2.5rem; border-radius: 16px;
    margin-bottom: 1.5rem; text-align: center;
}
.hero h1 { font-size: 2.8rem; margin: 0; }
.hero p  { font-size: 1.1rem; margin-top: 0.5rem; opacity: 0.9; }

.metric-card {
    background: #f0faf4; border: 1px solid #b2dfcb;
    border-radius: 12px; padding: 1rem 1.5rem; text-align: center;
}
.metric-card .value { font-size: 2rem; font-weight: 700; color: #1a6b3c; }
.metric-card .label { font-size: 0.85rem; color: #555; }

.med-card {
    border: 1px solid #d4edda; border-left: 5px solid #28a745;
    border-radius: 8px; padding: 1rem 1.2rem; margin-bottom: 1rem;
    background: #f9fffa;
}
.alt-best {
    background: #e6f4ea; border-radius: 8px; padding: 0.4rem 0.8rem;
    font-weight: 600; color: #155724;
}
.badge {
    display: inline-block; padding: 2px 10px; border-radius: 999px;
    font-size: 0.75rem; font-weight: 600; margin-left: 6px;
}
.badge-green  { background: #d4edda; color: #155724; }
.badge-yellow { background: #fff3cd; color: #856404; }
.badge-red    { background: #f8d7da; color: #721c24; }
.badge-blue   { background: #cce5ff; color: #004085; }

.chat-bubble-user {
    background: #e8f5e9; border-radius: 12px 12px 2px 12px;
    padding: 0.6rem 1rem; margin: 0.4rem 0; max-width: 80%;
    float: right; clear: both;
}
.chat-bubble-ai {
    background: #f1f3f4; border-radius: 12px 12px 12px 2px;
    padding: 0.6rem 1rem; margin: 0.4rem 0; max-width: 80%;
    float: left; clear: both;
}
.chat-container { overflow: hidden; }

.llm-badge {
    background: linear-gradient(90deg, #6f42c1, #0d6efd);
    color: white; padding: 3px 12px; border-radius: 999px;
    font-size: 0.75rem; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# ── API helpers ───────────────────────────────────────────────────────────────

def _post_image(image_bytes: bytes, content_type: str, engine: str,
                check_interactions: bool = True) -> dict:
    resp = requests.post(
        f"{API_BASE}/upload",
        files={"file": ("prescription.jpg", image_bytes, content_type)},
        data={"ocr_engine": engine, "check_interactions": str(check_interactions).lower()},
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()


def _post_text(text: str, check_interactions: bool = True) -> dict:
    resp = requests.post(
        f"{API_BASE}/search-text",
        data={"prescription_text": text,
              "check_interactions": str(check_interactions).lower()},
        timeout=45,
    )
    resp.raise_for_status()
    return resp.json()


def _search_medicine(name: str) -> dict:
    resp = requests.get(f"{API_BASE}/medicines/search", params={"name": name}, timeout=15)
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


def _chat(message: str, history: list, context_medicines: list) -> str:
    payload = {
        "message": message,
        "history": history,
        "context_medicines": context_medicines,
    }
    resp = requests.post(f"{API_BASE}/chat", json=payload, timeout=45)
    resp.raise_for_status()
    return resp.json().get("reply", "")


def _explain(brand: str, generic: str = "", salt: str = "") -> str:
    payload = {"brand_name": brand, "generic_name": generic, "salt_composition": salt}
    resp = requests.post(f"{API_BASE}/explain", json=payload, timeout=45)
    resp.raise_for_status()
    return resp.json().get("explanation", "")


def _check_interactions(medicines: list) -> str:
    resp = requests.post(f"{API_BASE}/interactions",
                         json={"medicines": medicines}, timeout=45)
    resp.raise_for_status()
    return resp.json().get("interaction_report", "")


def _llm_status() -> dict:
    try:
        resp = requests.get(f"{API_BASE}/llm-status", timeout=5)
        return resp.json()
    except Exception:
        return {"llm_available": False}


# ── Result renderer ──────────────────────────────────────────────────────────

def render_results(results: list, summary: dict | None = None,
                   interaction_warning: str = "", llm_used: bool = False):
    found = [r for r in results if r.get("match_type") != "none" and not r.get("error")]
    not_found = [r for r in results if r.get("error") or r.get("match_type") == "none"]

    if not found and not not_found:
        st.info("No medicines found. Try entering medicine names manually.")
        return

    # ── Summary metrics ───────────────────────────────────────────────────────
    if summary:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(
                f'<div class="metric-card"><div class="value">{summary["identified_count"]}</div>'
                f'<div class="label">Identified</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(
                f'<div class="metric-card"><div class="value">₹{summary["estimated_brand_cost"]:.0f}</div>'
                f'<div class="label">Branded Cost</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(
                f'<div class="metric-card"><div class="value">₹{summary["estimated_cheapest_cost"]:.0f}</div>'
                f'<div class="label">Cheapest Generic</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(
                f'<div class="metric-card"><div class="value">₹{summary["estimated_jan_aushadhi_cost"]:.0f}</div>'
                f'<div class="label">Jan Aushadhi Est.</div></div>', unsafe_allow_html=True)
        with col5:
            st.markdown(
                f'<div class="metric-card"><div class="value">₹{summary["potential_savings"]:.0f}</div>'
                f'<div class="label">Savings ({summary["savings_pct"]:.0f}%)</div></div>',
                unsafe_allow_html=True)

        st.markdown("---")

    if llm_used:
        st.info("🤖 Medicine names were extracted using AI (LLM fallback — OCR text was ambiguous).")

    # ── Drug interaction warning ──────────────────────────────────────────────
    if interaction_warning and "No significant" not in interaction_warning:
        with st.expander("⚠️ Drug Interaction Report", expanded=True):
            st.warning(interaction_warning)

    # ── Per-medicine results ──────────────────────────────────────────────────
    for r in found:
        alts = r.get("alternatives", [])
        matched = r.get("matched_brand", r["query"])
        salt = r.get("salt_composition", "")
        match_type = r.get("match_type", "")
        score = r.get("fuzzy_score", 100)

        if match_type == "exact":
            badge = '<span class="badge badge-green">✓ Exact</span>'
        elif match_type == "fuzzy":
            badge = f'<span class="badge badge-yellow">~ Fuzzy ({score}%)</span>'
        elif match_type == "salt":
            badge = '<span class="badge badge-yellow">~ Generic Match</span>'
        else:
            badge = ""

        with st.expander(f"💊 {matched}  {badge}", expanded=True):
            if salt:
                st.caption(f"**Salt / Composition:** {salt}")

            col_table, col_explain = st.columns([3, 1])

            with col_table:
                if alts:
                    rows = []
                    for i, a in enumerate(alts):
                        tag = " ⭐" if a.get("is_cheapest") else ""
                        ja_tag = " 🏥" if a.get("is_jan_aushadhi") else ""
                        rows.append({
                            "Option": f"{a['brand_name']}{tag}{ja_tag}",
                            "Generic Name": a["generic_name"],
                            "Manufacturer": a["manufacturer"],
                            "Form": f"{a['form']} {a['strength']}",
                            "Price/Unit (₹)": a["brand_price"],
                            "Generic Price (₹)": a["generic_price"],
                            "Jan Aushadhi (₹)": a.get("jan_aushadhi_price") or "N/A",
                            "Savings vs Brand": f"₹{a['savings_vs_brand']} ({a['savings_pct']:.0f}%)",
                        })
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True, hide_index=True,
                                 column_config={
                                     "Price/Unit (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                                     "Generic Price (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                                 })
                    best = alts[0]
                    st.success(
                        f"✅ **Cheapest:** {best['brand_name']} @ ₹{best['brand_price']}/unit "
                        f"— saves ₹{best['savings_vs_brand']} ({best['savings_pct']:.0f}%)"
                    )
                else:
                    st.warning("No cheaper alternatives found in database.")

            with col_explain:
                if salt or matched:
                    if st.button("🤖 Explain", key=f"explain_{matched}"):
                        with st.spinner("Asking AI…"):
                            try:
                                explanation = _explain(
                                    brand=matched,
                                    generic=r.get("salt_composition", ""),
                                    salt=salt,
                                )
                                if explanation:
                                    st.info(explanation)
                                else:
                                    st.warning("LLM not configured. Add ANTHROPIC_API_KEY to .env.")
                            except Exception as e:
                                st.error(f"Error: {e}")

    if not_found:
        st.markdown("### ❓ Not Identified")
        for r in not_found:
            st.warning(f"**{r['query']}** — {r.get('error', 'No match found')}")


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/hospital.png", width=64)
    st.markdown("## Medico.AI")
    st.caption("Smart Medicine Cost Optimizer for India")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["🏠 Home", "📸 Upload Prescription", "🔍 Search Medicine",
         "💬 AI Assistant", "📊 Browse Database", "ℹ️ About"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Backend status
    try:
        r = requests.get("http://localhost:8000/health", timeout=2)
        if r.ok:
            data = r.json()
            st.success("🟢 Backend Online")
            if data.get("llm_enabled"):
                st.markdown('<span class="llm-badge">🤖 AI Enabled</span>', unsafe_allow_html=True)
            else:
                st.caption("⚠️ AI features off (no API key)")
        else:
            st.error("🔴 Backend Error")
    except Exception:
        st.error("🔴 Backend Offline\nRun: `python backend/app.py`")

    st.markdown("---")
    st.caption("⚕️ Always consult a qualified pharmacist or doctor before switching medicines.")


# ── HOME ──────────────────────────────────────────────────────────────────────
if page == "🏠 Home":
    st.markdown("""
<div class="hero">
  <h1>💊 Medico.AI</h1>
  <p>AI-powered prescription decoder & generic medicine cost optimizer for India</p>
</div>
""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("### 📸 Upload")
        st.write("Photo your prescription. OCR reads it instantly.")
    with c2:
        st.markdown("### 🤖 AI Decode")
        st.write("Claude AI extracts medicine names from any handwriting.")
    with c3:
        st.markdown("### 💰 Save")
        st.write("Ranked cheaper alternatives including Jan Aushadhi prices.")
    with c4:
        st.markdown("### 💬 Chat")
        st.write("Ask Medico AI anything about your medicines in plain language.")

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
            st.error("Cannot reach backend. Is it running?")

    st.markdown("---")
    st.info("**Disclaimer:** Medico.AI is an informational tool only. Always consult a registered pharmacist or doctor before switching medicines.")


# ── UPLOAD ────────────────────────────────────────────────────────────────────
elif page == "📸 Upload Prescription":
    st.title("📸 Upload Prescription")
    st.write("Upload a photo or scan of your prescription. Supported: JPG, PNG, WebP, BMP.")

    tab_img, tab_text = st.tabs(["📷 Image Upload", "✏️ Type / Paste Text"])

    with tab_img:
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            engine = st.selectbox("OCR Engine", ["auto", "tesseract", "easyocr"])
        with col_opt2:
            check_int = st.checkbox("Check drug interactions (AI)", value=True)

        uploaded = st.file_uploader("Choose prescription image",
                                    type=["jpg", "jpeg", "png", "webp", "bmp"])

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
                        data = _post_image(raw, uploaded.type or "image/jpeg",
                                           engine, check_interactions=check_int)

                        with st.expander("📄 Raw OCR Text", expanded=False):
                            st.code(data.get("raw_text", "(empty)"))
                            st.caption(
                                f"Engine: {data.get('ocr_engine', '?')} | "
                                f"Confidence: {data.get('ocr_confidence', 0)}%"
                            )

                        extracted = data.get("extracted_medicines", [])
                        st.markdown(f"**Medicines extracted:** {len(extracted)}")
                        if extracted:
                            st.write(", ".join(extracted))

                        # Store in session for AI chat context
                        st.session_state["context_medicines"] = extracted

                        st.markdown("---")
                        render_results(
                            data.get("results", []),
                            summary=data.get("summary"),
                            interaction_warning=data.get("interaction_warning", ""),
                            llm_used=data.get("llm_extraction_used", False),
                        )

                    except requests.HTTPError as e:
                        st.error(f"Server error {e.response.status_code}: {e.response.text}")
                    except requests.ConnectionError:
                        st.error("Backend offline. Run `python backend/app.py` first.")
                    except Exception as e:
                        st.error(f"Unexpected error: {e}")

    with tab_text:
        st.write("Type or paste medicine names or full prescription text:")
        check_int_text = st.checkbox("Check drug interactions (AI)", value=True, key="check_int_text")
        text_input = st.text_area(
            "Prescription text", height=200,
            placeholder="e.g.\nTab Crocin 500mg BD\nCap Augmentin 625mg TDS\nTab Atorva 10mg OD",
        )
        if st.button("🔍 Find Alternatives", type="primary", key="text_btn"):
            if not text_input.strip():
                st.warning("Please enter some text.")
            else:
                with st.spinner("Analysing…"):
                    try:
                        data = _post_text(text_input, check_interactions=check_int_text)
                        st.session_state["context_medicines"] = data.get("extracted_medicines", [])
                        render_results(
                            data.get("results", []),
                            summary=data.get("summary"),
                            interaction_warning=data.get("interaction_warning", ""),
                            llm_used=data.get("llm_extraction_used", False),
                        )
                    except requests.ConnectionError:
                        st.error("Backend offline.")
                    except Exception as e:
                        st.error(f"Error: {e}")


# ── SEARCH ────────────────────────────────────────────────────────────────────
elif page == "🔍 Search Medicine":
    st.title("🔍 Search Medicine")
    st.write("Enter any brand or generic name — we'll find cheaper alternatives.")

    name = st.text_input("Medicine name", placeholder="e.g. Lipitor, Atorvastatin, Augmentin…")

    if name:
        try:
            data = _search_medicine(name)
            render_results([data])

            # Quick explain button
            if st.button("🤖 Explain this medicine with AI"):
                with st.spinner("Asking AI…"):
                    try:
                        exp = _explain(
                            brand=data.get("matched_brand", name),
                            generic=data.get("salt_composition", ""),
                            salt=data.get("salt_composition", ""),
                        )
                        if exp:
                            st.info(exp)
                        else:
                            st.warning("LLM not configured. Add ANTHROPIC_API_KEY to .env.")
                    except Exception as e:
                        st.error(f"Error: {e}")

        except requests.HTTPError as e:
            st.error(f"API error: {e.response.text}")
        except requests.ConnectionError:
            st.error("Backend offline. Run `python backend/app.py` first.")


# ── AI ASSISTANT ─────────────────────────────────────────────────────────────
elif page == "💬 AI Assistant":
    st.title("💬 AI Assistant — Ask Medico")
    st.caption("Ask anything about your medicines, dosage, side effects, or generic alternatives.")

    # Check LLM status
    try:
        llm_info = _llm_status()
        if not llm_info.get("llm_available"):
            st.warning(
                "⚠️ AI features require an API key.\n\n"
                "Add `ANTHROPIC_API_KEY=your_key` to your `.env` file and restart the backend.\n\n"
                "Get a free key at https://console.anthropic.com"
            )
    except Exception:
        st.warning("Cannot reach backend — is it running?")

    # Context medicines from session
    context_meds = st.session_state.get("context_medicines", [])
    if context_meds:
        st.info(f"💊 Prescription context: {', '.join(context_meds)}")

    # Initialise chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant", avatar="💊"):
                st.write(msg["content"])

    # Chat input
    user_input = st.chat_input("Ask Medico AI…")
    if user_input:
        # Show user message
        with st.chat_message("user"):
            st.write(user_input)

        # Call API
        with st.chat_message("assistant", avatar="💊"):
            with st.spinner("Thinking…"):
                try:
                    reply = _chat(
                        message=user_input,
                        history=st.session_state.chat_history,
                        context_medicines=context_meds,
                    )
                    st.write(reply)

                    # Update history
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})

                except requests.ConnectionError:
                    st.error("Backend offline.")
                except Exception as e:
                    st.error(f"Error: {e}")

    # Quick prompts
    st.markdown("---")
    st.markdown("**💡 Quick questions:**")
    cols = st.columns(3)
    quick_prompts = [
        "What is Paracetamol used for?",
        "Are there cheaper alternatives to Augmentin?",
        "What is the Jan Aushadhi scheme?",
        "What are common side effects of Metformin?",
        "Can I take Paracetamol and Ibuprofen together?",
        "What does 'BD' mean on a prescription?",
    ]
    for i, prompt in enumerate(quick_prompts):
        with cols[i % 3]:
            if st.button(prompt, key=f"qp_{i}"):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                try:
                    reply = _chat(prompt, st.session_state.chat_history[:-1], context_meds)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.button("🗑️ Clear chat"):
        st.session_state.chat_history = []
        st.rerun()


# ── BROWSE ────────────────────────────────────────────────────────────────────
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
            df["Savings %"] = (
                (df["brand_price_per_unit"] - df["generic_price_per_unit"])
                / df["brand_price_per_unit"] * 100
            ).round(1)
            st.dataframe(
                df[[
                    "brand_name", "generic_name", "salt_composition",
                    "strength", "form", "manufacturer", "category",
                    "brand_price_per_unit", "generic_price_per_unit",
                    "jan_aushadhi_price", "Savings %",
                ]],
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

            # AI interaction check from browsed selection
            if len(medicines) >= 2:
                st.markdown("---")
                st.markdown("### 🤖 Check Interactions")
                selected_names = st.multiselect(
                    "Select medicines to check for interactions:",
                    options=[m["brand_name"] for m in medicines],
                )
                if selected_names and st.button("Check Interactions"):
                    with st.spinner("Checking…"):
                        try:
                            report = _check_interactions(selected_names)
                            st.info(report)
                        except Exception as e:
                            st.error(f"Error: {e}")
        else:
            st.info("No medicines found. Try a different search.")
    except requests.ConnectionError:
        st.error("Backend offline.")


# ── ABOUT ─────────────────────────────────────────────────────────────────────
elif page == "ℹ️ About":
    st.title("ℹ️ About Medico.AI")
    st.markdown("""
## 🏥 What is Medico.AI?

**Medico.AI** is an open-source, AI-powered tool designed to help Indian patients
discover cheaper generic alternatives to the branded medicines they are prescribed.

### 🔬 How it works

| Step | Agent | What happens |
|------|-------|-------------|
| **Upload** | — | You photograph or scan your prescription |
| **OCR** | OCR Agent | Tesseract / EasyOCR extracts text from the image |
| **NLP** | NLP Agent | Rule-based pipeline identifies medicine names |
| **LLM Fallback** | LLM Agent | Claude AI re-reads text when NLP finds nothing |
| **Matching** | Matcher Agent | RapidFuzz maps names → database (brand → generic → salt) |
| **Pricing** | Pricer Agent | Alternatives ranked cheapest-first, savings computed |
| **Response** | Responder Agent | Clean JSON output sent to frontend |
| **Interactions** | LLM Agent | Claude checks for dangerous drug combinations |

### 🤖 LLM Integration (New in v2.0)

Medico.AI now integrates **Claude (Anthropic)** and **GPT-4o-mini (OpenAI)**:

- **NLP Fallback** — when OCR text is messy, Claude extracts medicines directly
- **Medicine Explainer** — plain-English explanation of any drug: uses, side effects, warnings
- **Drug Interaction Checker** — flags clinically significant interactions
- **AI Chat (Medico)** — conversational Q&A assistant for patients

To enable: add `ANTHROPIC_API_KEY=your_key` to your `.env` file.

### 💊 Why this matters

Branded medicines in India can cost **5–20× more** than generic equivalents with
identical salt compositions. Medico.AI includes **Jan Aushadhi** prices in all comparisons.

### ⚙️ Tech Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Streamlit
- **OCR**: Tesseract + EasyOCR
- **NLP**: Rule-based + RapidFuzz + LLM fallback
- **LLM**: Claude (Anthropic) / GPT-4o-mini (OpenAI)
- **Agents**: OCR → NLP → Matcher → Pricer → Responder

### ⚠️ Disclaimer

Medico.AI is an **informational tool only**. Always consult a registered pharmacist or
qualified doctor before changing any medication. We do not dispense medical advice.

---
Built with ❤️ for affordable healthcare in India.
""")
