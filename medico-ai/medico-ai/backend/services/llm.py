"""
LLM Service — Claude (Anthropic) integration for Medico.AI.

Capabilities:
  1. LLM-powered NLP fallback: extract medicine names when rule-based NLP fails
  2. Medicine explainer: plain-language explanation of a drug
  3. Drug interaction checker: flag dangerous combinations
  4. AI Chat: answer patient questions about their prescription
"""
from __future__ import annotations

import os
import json
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# ── client singleton ─────────────────────────────────────────────────────────

_anthropic_client = None
_openai_client = None


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        try:
            import anthropic  # type: ignore
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            if api_key:
                _anthropic_client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            logger.warning(f"Anthropic SDK unavailable: {e}")
    return _anthropic_client


def _get_openai():
    global _openai_client
    if _openai_client is None:
        try:
            import openai  # type: ignore
            api_key = os.getenv("OPENAI_API_KEY", "")
            if api_key:
                _openai_client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            logger.warning(f"OpenAI SDK unavailable: {e}")
    return _openai_client


def _llm_available() -> bool:
    return _get_anthropic() is not None or _get_openai() is not None


def _call_llm(system: str, user: str, max_tokens: int = 1024) -> str:
    """
    Call Claude (preferred) or GPT-4o-mini as fallback.
    Returns the assistant's text response, or empty string on failure.
    """
    client = _get_anthropic()
    if client:
        try:
            response = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic call failed: {e}")

    oa = _get_openai()
    if oa:
        try:
            response = oa.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")

    return ""


# ── 1. LLM-powered medicine extraction ─────────────────────────────────────

EXTRACT_SYSTEM = """You are a clinical pharmacist assistant.
Extract only the medicine/drug names from the provided prescription text.
Return a JSON array of strings — just the drug names, no dosage, no form, no frequency.
Example output: ["Paracetamol", "Amoxicillin", "Omeprazole"]
If no medicines are found, return an empty array: []
Return ONLY the JSON array, nothing else."""


def llm_extract_medicines(ocr_text: str) -> List[str]:
    """
    Use an LLM to extract medicine names from raw OCR text.
    Returns a list of medicine name strings.
    Falls back to empty list if LLM is unavailable or fails.
    """
    if not ocr_text.strip() or not _llm_available():
        return []

    raw = _call_llm(EXTRACT_SYSTEM, ocr_text[:4000], max_tokens=512)
    if not raw:
        return []

    try:
        # Strip markdown code fences if present
        clean = raw.strip().strip("```json").strip("```").strip()
        medicines = json.loads(clean)
        if isinstance(medicines, list):
            return [str(m).strip() for m in medicines if m]
    except Exception as e:
        logger.warning(f"LLM extraction JSON parse error: {e}  raw={raw[:200]}")

    return []


# ── 2. Medicine explainer ────────────────────────────────────────────────────

EXPLAIN_SYSTEM = """You are a friendly pharmacist explaining medicines to an Indian patient.
Keep your explanation simple, clear, and in plain English (avoid heavy jargon).
Structure your response as:
1. What it is (1-2 sentences)
2. Common uses (bullet list, max 4 points)
3. Common side effects (bullet list, max 4 points)
4. Important warnings (1-2 sentences)
5. Jan Aushadhi note if applicable (mention that cheaper generics may be available)
Keep the total response under 200 words."""


def explain_medicine(brand_name: str, generic_name: str, salt_composition: str) -> str:
    """
    Return a plain-language explanation of a medicine.
    """
    if not _llm_available():
        return ""

    user_prompt = (
        f"Medicine: {brand_name}\n"
        f"Generic name: {generic_name}\n"
        f"Salt composition: {salt_composition}\n\n"
        "Please explain this medicine to the patient."
    )
    return _call_llm(EXPLAIN_SYSTEM, user_prompt, max_tokens=400)


# ── 3. Drug interaction checker ──────────────────────────────────────────────

INTERACTION_SYSTEM = """You are a clinical pharmacist specialising in drug safety.
Given a list of medicines, identify any clinically significant drug-drug interactions.
For each interaction found, describe:
- The two drugs involved
- The type of interaction (e.g. additive, synergistic, antagonistic)
- The clinical risk (Low / Medium / High)
- Brief recommendation

If no significant interactions are found, say: "No significant interactions detected."
Keep it factual and concise. Add a disclaimer that the patient should consult their doctor."""


def check_drug_interactions(medicine_names: List[str]) -> str:
    """
    Check for drug interactions among a list of medicines.
    Returns a formatted string with interaction details.
    """
    if not medicine_names or not _llm_available():
        return ""

    medicines_str = "\n".join(f"- {m}" for m in medicine_names)
    user_prompt = f"Check interactions for these medicines:\n{medicines_str}"
    return _call_llm(INTERACTION_SYSTEM, user_prompt, max_tokens=600)


# ── 4. AI Chat ───────────────────────────────────────────────────────────────

CHAT_SYSTEM = """You are Medico, an AI pharmacist assistant helping Indian patients understand their prescriptions and find affordable generic medicines.

You can help with:
- Explaining what medicines do
- Finding cheaper generic alternatives (mention Jan Aushadhi stores)
- Understanding dosage instructions
- General medication safety questions
- When to see a doctor

Always:
- Use simple, friendly language
- Mention Jan Aushadhi stores for affordable generics when relevant
- Add a disclaimer for medical advice: "Please consult a qualified doctor or pharmacist before changing any medication."
- Keep responses concise (under 250 words unless detail is necessary)

Do NOT:
- Diagnose diseases
- Recommend specific dosages without a prescription
- Advise stopping prescribed medications"""


def chat_with_ai(
    user_message: str,
    conversation_history: Optional[List[dict]] = None,
    context_medicines: Optional[List[str]] = None,
) -> str:
    """
    Multi-turn AI chat for patient Q&A.

    Parameters
    ----------
    user_message : str
        The latest patient message.
    conversation_history : list of {"role": "user"|"assistant", "content": str}
        Prior turns in the conversation.
    context_medicines : list of str
        Medicines from the current prescription (for context injection).

    Returns
    -------
    str — assistant response text.
    """
    if not _llm_available():
        return (
            "AI chat is not available right now. "
            "Please configure ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file."
        )

    system = CHAT_SYSTEM
    if context_medicines:
        meds_str = ", ".join(context_medicines)
        system += f"\n\nCurrent prescription context — medicines: {meds_str}"

    messages = list(conversation_history or [])
    messages.append({"role": "user", "content": user_message})

    client = _get_anthropic()
    if client:
        try:
            response = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
                max_tokens=600,
                system=system,
                messages=messages,
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic chat failed: {e}")

    oa = _get_openai()
    if oa:
        try:
            all_msgs = [{"role": "system", "content": system}] + messages
            response = oa.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                max_tokens=600,
                messages=all_msgs,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI chat failed: {e}")

    return "Sorry, I couldn't reach the AI service. Please try again."


def is_llm_configured() -> bool:
    """Check whether an LLM API key is configured."""
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))
