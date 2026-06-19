"""
escalator.py
Decides whether a conversation turn should be escalated to a human agent,
based on configurable thresholds (src/config.py), and builds the
structured handoff summary required by the assignment (section 4.5/4.6).

Escalation triggers implemented (assignment 4.4):
  1. Low retrieval confidence / no relevant info found.
  2. Sensitive topics (billing, legal, account security) via keyword check.
  3. Repeated frustration across consecutive turns (multi-turn memory).
  4. (Caller can also force escalation, e.g. user explicitly asks for a human.)
"""
import re

from src import config


def _contains_sensitive_topic(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in config.SENSITIVE_KEYWORDS)


def check_escalation(
    user_query: str,
    persona: str,
    context_chunks: list,
    conversation_history: list = None,
) -> dict:
    """
    Evaluates all escalation triggers for the current turn.

    conversation_history: list of dicts like {"persona": str, ...} representing
    prior turns in the session, oldest first. Used for the "repeated frustration"
    trigger. Pass None or [] for a fresh conversation.

    Returns:
        {
            "escalate": bool,
            "reasons": list[str],   # human-readable trigger names
            "best_score": float,
        }
    """
    conversation_history = conversation_history or []
    reasons = []

    # Trigger 1: Low retrieval confidence / nothing found
    best_score = max([c["score"] for c in context_chunks], default=0.0)
    if not context_chunks or best_score < config.RETRIEVAL_CONFIDENCE_THRESHOLD:
        reasons.append("Low retrieval confidence")

    # Trigger 2: Sensitive topic keywords
    if _contains_sensitive_topic(user_query):
        reasons.append("Sensitive topic detected (billing/legal/security)")

    # Trigger 3: Repeated frustration across consecutive turns
    recent_personas = [turn.get("persona") for turn in conversation_history[-(config.FRUSTRATION_TURN_THRESHOLD - 1):]]
    recent_personas.append(persona)
    if (
        len(recent_personas) >= config.FRUSTRATION_TURN_THRESHOLD
        and all(p == "Frustrated User" for p in recent_personas[-config.FRUSTRATION_TURN_THRESHOLD:])
    ):
        reasons.append(f"Frustration persisted for {config.FRUSTRATION_TURN_THRESHOLD}+ consecutive turns")

    return {
        "escalate": len(reasons) > 0,
        "reasons": reasons,
        "best_score": round(best_score, 4),
    }


def generate_handoff_summary(
    user_query: str,
    persona: str,
    context_chunks: list,
    escalation_result: dict,
    conversation_history: list = None,
    attempted_steps: list = None,
) -> dict:
    """
    Builds the structured human-handoff summary (assignment 4.5):
      - detected persona
      - user issue summary
      - conversation history
      - retrieved documents used
      - actions already attempted
      - recommended next steps
    """
    conversation_history = conversation_history or []
    attempted_steps = attempted_steps or []

    sources_used = sorted({c["source"] for c in context_chunks}) if context_chunks else []

    if "Low retrieval confidence" in escalation_result.get("reasons", []):
        recommendation = (
            "No sufficiently relevant documentation was found for this query. "
            "Recommend manual investigation by a human agent familiar with this issue area."
        )
    elif any("Sensitive topic" in r for r in escalation_result.get("reasons", [])):
        recommendation = (
            "This issue touches a sensitive area (billing/legal/account security) that requires "
            "human judgment and cannot be resolved through automated responses."
        )
    elif any("Frustration persisted" in r for r in escalation_result.get("reasons", [])):
        recommendation = (
            "Customer has expressed frustration across multiple consecutive turns without "
            "resolution. Recommend a human agent take over to rebuild trust and resolve directly."
        )
    else:
        recommendation = "Review conversation context and proceed with manual resolution."

    handoff = {
        "persona": persona,
        "issue_summary": (user_query[:160] + "...") if len(user_query) > 160 else user_query,
        "conversation_history": [
            {"role": turn.get("role", "user"), "message": turn.get("message", ""), "persona": turn.get("persona")}
            for turn in conversation_history
        ],
        "retrieved_documents_used": sources_used,
        "attempted_steps": attempted_steps,
        "escalation_reasons": escalation_result.get("reasons", []),
        "retrieval_confidence_score": escalation_result.get("best_score", 0.0),
        "recommended_action": recommendation,
    }
    return handoff
