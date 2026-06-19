"""
cli.py
Minimal interactive command-line chatbot interface (assignment requirement
4.6: "At minimum: Interactive command-line chatbot"). The Streamlit app
(app.py) is the bonus UI. Both share the same underlying src/ modules.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import config
from src.classifier import classify_customer_persona
from src.rag_pipeline import RAGPipeline
from src.escalator import check_escalation, generate_handoff_summary
from src.generator import generate_adaptive_response

PERSONA_BADGE = {
    "Technical Expert": "[TECH]",
    "Frustrated User": "[FRUSTRATED]",
    "Business Executive": "[EXEC]",
}


def print_divider():
    print("-" * 70)


def main():
    if not config.GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY not set. Add it to your .env file and try again.")
        sys.exit(1)

    print_divider()
    print(f"  {config.APP_TITLE} — CLI Mode")
    print("  Type 'exit' or 'quit' to leave. Type 'reset' to clear conversation memory.")
    print_divider()

    pipeline = RAGPipeline()
    chunk_count = pipeline.count()
    if chunk_count == 0:
        print("\nWARNING: Knowledge base index is empty.")
        print("Run `python ingest_knowledge_base.py` first, then restart this script.\n")

    conversation_history = []  # list of {role, message, persona}

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye.")
            break
        if user_input.lower() == "reset":
            conversation_history = []
            print("Conversation memory cleared.")
            continue

        conversation_history.append({"role": "user", "message": user_input, "persona": None})

        # 1. Classify persona
        classification = classify_customer_persona(user_input)
        persona = classification["persona"]
        badge = PERSONA_BADGE.get(persona, "")
        print(f"\n{badge} Detected Persona: {persona}  (confidence: {classification['confidence']:.2f})")

        # 2. Retrieve context
        context_chunks = pipeline.retrieve_context(user_input, top_k=config.TOP_K)
        print("\nRetrieved sources:")
        if context_chunks:
            for c in context_chunks:
                page_info = f", page {c['page']}" if c.get("page") not in (None, "N/A") else ""
                print(f"  - {c['source']}{page_info} | {c.get('section', 'General')} (score: {c['score']:.3f})")
        else:
            print("  (none found)")

        # 3. Escalation check
        history_personas = [t for t in conversation_history if t["role"] == "assistant"]
        escalation_result = check_escalation(
            user_query=user_input,
            persona=persona,
            context_chunks=context_chunks,
            conversation_history=history_personas,
        )

        # 4. Generate response or escalate
        if escalation_result["escalate"]:
            response_text = (
                "I want to make sure this gets handled correctly, so I'm connecting you with a "
                "human support specialist who can take a closer look at this for you."
            )
            handoff = generate_handoff_summary(
                user_query=user_input,
                persona=persona,
                context_chunks=context_chunks,
                escalation_result=escalation_result,
                conversation_history=conversation_history,
                attempted_steps=[],
            )
            print(f"\nESCALATION STATUS: ESCALATED — reasons: {', '.join(escalation_result['reasons'])}")
            print("\nHuman handoff summary:")
            import json
            print(json.dumps(handoff, indent=2))
        else:
            gen_result = generate_adaptive_response(user_input, persona, context_chunks)
            response_text = gen_result["response"]
            print("\nESCALATION STATUS: Resolved by AI agent")
            handoff = None

        print("\nAgent response:")
        print(response_text)

        conversation_history.append({
            "role": "assistant",
            "message": response_text,
            "persona": persona,
        })

        print_divider()


if __name__ == "__main__":
    main()
