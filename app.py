"""
app.py
Streamlit chat UI for the Persona-Adaptive Customer Support Agent.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from src import config
from src.classifier import classify_customer_persona
from src.rag_pipeline import RAGPipeline
from src.escalator import check_escalation, generate_handoff_summary
from src.generator import generate_adaptive_response

st.set_page_config(page_title=config.APP_TITLE, page_icon="🎧", layout="wide")

PERSONA_BADGE = {
    "Technical Expert": "🛠️",
    "Frustrated User": "😤",
    "Business Executive": "💼",
}


@st.cache_resource(show_spinner=False)
def get_pipeline():
    rag = RAGPipeline()
    if rag.collection.count() == 0:
        rag.ingest_directory(config.DATA_DIR)
    return rag


def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0


def render_sidebar(pipeline):
    with st.sidebar:
        st.header("⚙️ System Status")

        if not config.GEMINI_API_KEY:
            st.error("GEMINI_API_KEY not found. Add it to your .env file.")
        else:
            st.success("Gemini API key loaded.")

        try:
            chunk_count = pipeline.collection.count()
            if chunk_count == 0:
                st.warning("Knowledge base index is empty.")
            else:
                st.info(f"Knowledge base index: **{chunk_count}** chunks loaded.")
        except Exception as e:
            st.error(f"Could not reach ChromaDB: {e}")

        st.divider()
        st.subheader("Escalation Thresholds")
        st.caption(f"Retrieval confidence threshold: **{config.RETRIEVAL_CONFIDENCE_THRESHOLD}**")
        st.caption(f"Frustration turn threshold: **{config.FRUSTRATION_TURN_THRESHOLD}** consecutive turns")
        st.caption(f"Top-K retrieved chunks: **{config.TOP_K}**")

        st.divider()
        st.subheader("Conversation")
        st.caption(f"Turns this session: **{st.session_state.turn_count}**")
        if st.button("🔄 Reset conversation"):
            st.session_state.messages = []
            st.session_state.turn_count = 0
            st.rerun()

        st.divider()
        st.subheader("Try an example")
        examples = [
            "Where is the guide to clear cookies? It's been an hour and nothing is loading!",
            "What are the header parameter requirements for your bearer token auth?",
            "We need a timeline of when billing disputes are resolved.",
            "I'm experiencing internal errors with your database integration.",
            "My billing statement has unexpected duplicate charges. I demand an immediate refund!",
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{hash(ex)}", use_container_width=True):
                st.session_state.pending_input = ex
                st.rerun()


def render_history():
    for turn in st.session_state.messages:
        if turn["role"] == "user":
            with st.chat_message("user"):
                st.write(turn["message"])
        else:
            with st.chat_message("assistant"):
                badge = PERSONA_BADGE.get(turn.get("persona"), "")
                st.markdown(f"**Detected Persona:** {badge} {turn.get('persona', 'N/A')}")

                if turn.get("escalated"):
                    st.error("🚨 Escalated to human agent")
                else:
                    st.success("✅ Resolved by AI agent")

                st.write(turn["message"])

                with st.expander("📚 Retrieved sources"):
                    if turn.get("sources"):
                        for s in turn["sources"]:
                            page_info = f", page {s['page']}" if s.get("page") not in (None, "N/A") else ""
                            st.markdown(
                                f"- **{s['source']}**{page_info} — *{s.get('section', 'General')}* "
                                f"(score: {s['score']:.3f})"
                            )
                    else:
                        st.caption("No sources retrieved.")

                if turn.get("escalated"):
                    with st.expander("🧾 Human handoff summary (JSON)"):
                        st.json(turn["handoff"])


def process_turn(user_input: str, pipeline: RAGPipeline):
    with st.spinner("Classifying persona..."):
        classification = classify_customer_persona(user_input)
    persona = classification["persona"]

    with st.spinner("Retrieving relevant documents..."):
        context_chunks = pipeline.retrieve_context(user_input, top_k=config.TOP_K)

    history_personas = [
        {"persona": t.get("persona")} for t in st.session_state.messages if t["role"] == "assistant"
    ]
    escalation_result = check_escalation(
        user_query=user_input,
        persona=persona,
        context_chunks=context_chunks,
        conversation_history=history_personas,
    )

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
            conversation_history=[
                {"role": t["role"], "message": t["message"], "persona": t.get("persona")}
                for t in st.session_state.messages
            ],
            attempted_steps=[],
        )
    else:
        with st.spinner("Generating response..."):
            gen_result = generate_adaptive_response(user_input, persona, context_chunks)
        response_text = gen_result["response"]
        handoff = None

    return {
        "persona": persona,
        "classification": classification,
        "sources": context_chunks,
        "escalated": escalation_result["escalate"],
        "escalation_reasons": escalation_result["reasons"],
        "handoff": handoff,
        "response_text": response_text,
    }


def main():
    st.title(f"🎧 {config.APP_TITLE}")
    st.caption(
        "Detects customer persona, retrieves grounded answers from the knowledge base, "
        "and escalates to a human when needed."
    )

    init_session_state()
    pipeline = get_pipeline()
    render_sidebar(pipeline)
    render_history()

    pending = st.session_state.pop("pending_input", None) if "pending_input" in st.session_state else None
    user_input = st.chat_input("Type your support question...") or pending

    if user_input:
        st.session_state.messages.append({"role": "user", "message": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        if not config.GEMINI_API_KEY:
            st.error("Cannot process: GEMINI_API_KEY is missing.")
            return

        result = process_turn(user_input, pipeline)
        st.session_state.turn_count += 1

        assistant_turn = {
            "role": "assistant",
            "message": result["response_text"],
            "persona": result["persona"],
            "sources": result["sources"],
            "escalated": result["escalated"],
            "handoff": result["handoff"],
        }
        st.session_state.messages.append(assistant_turn)

        with st.chat_message("assistant"):
            badge = PERSONA_BADGE.get(result["persona"], "")
            st.markdown(f"**Detected Persona:** {badge} {result['persona']}")

            if result["escalated"]:
                st.error(f"🚨 Escalated — reasons: {', '.join(result['escalation_reasons'])}")
            else:
                st.success("✅ Resolved by AI agent")

            st.write(result["response_text"])

            with st.expander("📚 Retrieved sources"):
                if result["sources"]:
                    for s in result["sources"]:
                        page_info = f", page {s['page']}" if s.get("page") not in (None, "N/A") else ""
                        st.markdown(
                            f"- **{s['source']}**{page_info} — *{s.get('section', 'General')}* "
                            f"(score: {s['score']:.3f})"
                        )
                else:
                    st.caption("No sources retrieved.")

            if result["escalated"]:
                with st.expander("🧾 Human handoff summary (JSON)"):
                    st.json(result["handoff"])


if __name__ == "__main__":
    main()