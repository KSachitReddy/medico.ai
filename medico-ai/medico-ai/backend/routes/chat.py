"""
AI Chat route — POST /api/v1/chat
Handles multi-turn patient Q&A powered by Claude / GPT-4o-mini.

Also exposes:
  POST /api/v1/explain   — explain a single medicine
  POST /api/v1/interact  — check drug interactions
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.llm import (
    chat_with_ai,
    explain_medicine,
    check_drug_interactions,
    is_llm_configured,
)

router = APIRouter()


# ── Pydantic models ──────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None
    context_medicines: Optional[List[str]] = None


class ChatResponse(BaseModel):
    reply: str
    llm_available: bool


class ExplainRequest(BaseModel):
    brand_name: str
    generic_name: str = ""
    salt_composition: str = ""


class ExplainResponse(BaseModel):
    explanation: str
    llm_available: bool


class InteractionRequest(BaseModel):
    medicines: List[str]


class InteractionResponse(BaseModel):
    interaction_report: str
    llm_available: bool


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """
    Multi-turn AI chat with Medico assistant.
    Pass previous turns in `history` for context.
    Optionally pass `context_medicines` to give the LLM prescription context.
    """
    available = is_llm_configured()

    history_dicts = [{"role": m.role, "content": m.content} for m in (req.history or [])]

    reply = chat_with_ai(
        user_message=req.message,
        conversation_history=history_dicts,
        context_medicines=req.context_medicines,
    )

    return ChatResponse(reply=reply, llm_available=available)


@router.post("/explain", response_model=ExplainResponse)
def explain_endpoint(req: ExplainRequest):
    """
    Get a plain-language explanation of a medicine.
    """
    available = is_llm_configured()
    if not available:
        return ExplainResponse(
            explanation="LLM not configured. Add ANTHROPIC_API_KEY to .env to enable this feature.",
            llm_available=False,
        )

    explanation = explain_medicine(
        brand_name=req.brand_name,
        generic_name=req.generic_name,
        salt_composition=req.salt_composition,
    )

    return ExplainResponse(explanation=explanation, llm_available=True)


@router.post("/interactions", response_model=InteractionResponse)
def interactions_endpoint(req: InteractionRequest):
    """
    Check for drug-drug interactions among a list of medicines.
    """
    available = is_llm_configured()
    if not available:
        return InteractionResponse(
            interaction_report="LLM not configured. Add ANTHROPIC_API_KEY to .env to enable this feature.",
            llm_available=False,
        )

    if len(req.medicines) < 2:
        return InteractionResponse(
            interaction_report="Please provide at least 2 medicines to check interactions.",
            llm_available=True,
        )

    report = check_drug_interactions(req.medicines)
    return InteractionResponse(interaction_report=report, llm_available=True)


@router.get("/llm-status")
def llm_status():
    """Check whether LLM features are available."""
    return {
        "llm_available": is_llm_configured(),
        "message": (
            "LLM features enabled (AI chat, drug interactions, medicine explanations)."
            if is_llm_configured()
            else "LLM not configured. Set ANTHROPIC_API_KEY in .env to enable AI features."
        ),
    }
