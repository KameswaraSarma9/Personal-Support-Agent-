"""
generator.py
Builds the persona-specific system prompt, grounds it in retrieved
knowledge-base chunks, and calls Gemini to produce the final response.
Strictly instructs the model not to answer outside the provided context,
per the assignment's anti-hallucination requirement (4.3).
"""
from google import genai
from google.genai import types

from src import config

PERSONA_INSTRUCTIONS = {
    "Technical Expert": (
        "You are a Senior Systems Engineer responding to a technically fluent customer. "
        "Provide a precise root-cause explanation, mention exact error codes/headers/config "
        "fields where relevant, and lay out step-by-step resolution steps. It is fine to be "
        "detailed and somewhat dense — this user wants accuracy over brevity. Do not pad with "
        "reassurance language; get straight to the technical substance."
    ),
    "Frustrated User": (
        "You are a warm, reassuring Customer Care Specialist responding to a frustrated customer. "
        "Open with a brief, genuine acknowledgment of their frustration (one sentence, not "
        "excessive). Then give simple, numbered or bulleted action steps in plain language, "
        "avoiding technical jargon. Keep it focused and avoid being patronizing — the goal is to "
        "make them feel heard and get them unblocked quickly."
    ),
    "Business Executive": (
        "You are a Client Relations Director responding to a business stakeholder. Lead with the "
        "direct answer and business impact. Mention an estimated resolution timeframe if the "
        "context provides one. Keep the response short — a few sentences — and skip configuration "
        "or implementation detail unless explicitly asked. Professional, confident tone."
    ),
}


def _build_context_block(context_chunks: list) -> str:
    parts = []
    for c in context_chunks:
        page_info = f", page {c['page']}" if c.get("page") not in (None, "N/A") else ""
        parts.append(
            f"[Source: {c['source']}{page_info} | Section: {c.get('section', 'General')}]\n{c['text']}"
        )
    return "\n\n---\n\n".join(parts)


def generate_adaptive_response(user_query: str, persona: str, context_chunks: list) -> dict:
    """
    Generates a persona-adapted, context-grounded response.

    Note: escalation is decided separately in escalator.py — this function
    assumes it has already been called and that we are clear to generate
    a normal response. It still degrades gracefully if context_chunks is
    empty by instructing the model to say it doesn't have the information,
    rather than hallucinating.
    """
    persona_instructions = PERSONA_INSTRUCTIONS.get(
        persona, PERSONA_INSTRUCTIONS["Business Executive"]
    )

    context_text = _build_context_block(context_chunks) if context_chunks else "(no relevant context found)"

    full_system_prompt = (
        f"{persona_instructions}\n\n"
        "CRITICAL RULES:\n"
        "- Base your response ONLY on the information in the FACTUAL CONTEXT DOCUMENTS below.\n"
        "- Do not invent facts, policies, numbers, or steps that are not present in the context.\n"
        "- If the context does not fully answer the question, say so plainly rather than guessing.\n"
        "- Do not mention that you are an AI model or refer to 'the context' explicitly to the "
        "customer; speak naturally as a support agent who knows this information.\n\n"
        f"FACTUAL CONTEXT DOCUMENTS:\n{context_text}"
    )

    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=config.GENERATION_MODEL,
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=full_system_prompt,
                temperature=0.2,
            ),
        )
        response_text = response.text
    except Exception as e:
        response_text = (
            "I'm having trouble generating a response right now due to a system error. "
            "Let me connect you with a human agent to make sure this gets resolved."
        )

    return {
        "response": response_text,
        "context_used": context_chunks,
    }
