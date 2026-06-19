# Persona-Adaptive Customer Support Agent

An AI-powered customer support agent that detects a customer's communication persona,
retrieves grounded answers from a knowledge base using RAG, adapts its tone to the
detected persona, and escalates to a human agent with a structured handoff summary
when it can't safely resolve the issue.

Built for the Adsparkx AI Engineering Intern assignment.

---

## 1. Project Overview

The agent classifies every incoming support message into one of three personas
(**Technical Expert**, **Frustrated User**, **Business Executive**), retrieves the
most relevant knowledge-base chunks via vector similarity search, generates a
response grounded strictly in that retrieved content, and checks configurable
escalation triggers (low retrieval confidence, sensitive topics, repeated frustration)
before deciding whether to answer directly or hand off to a human agent.

Two interfaces are provided:
- **CLI** (`cli.py`) — minimum requirement, fully interactive terminal chatbot.
- **Streamlit Web UI** (`app.py`) — bonus feature, chat-style interface showing
  persona, sources, and escalation status per turn.

## 2. Tech Stack

| Component | Choice | Version |
|---|---|---|
| Language | Python | 3.11+ |
| LLM | Google Gemini (`gemini-2.5-flash`) | via `google-genai` SDK |
| Embeddings | Gemini `text-embedding-004` | 768-dim |
| Vector Database | ChromaDB (persistent local) | `>=0.4.0` |
| Chunking | LangChain `RecursiveCharacterTextSplitter` | `>=0.1.0` |
| PDF Parsing | `pypdf` | `>=3.0.0` |
| Web UI | Streamlit | `>=1.30.0` |
| Config | `python-dotenv` | `>=1.0.0` |

## 3. Architecture Diagram

```
                         ┌─────────────────────┐
                         │     User Message     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                       ┌────────────────────────┐
                       │   Persona Classifier    │
                       │ (Gemini, structured     │
                       │  JSON output)           │
                       └──────────┬─────────────┘
                                    │  Persona Tag
                                    │  (Tech / Frustrated / Exec)
                                    ▼
                       ┌────────────────────────┐
                       │   RAG Retrieval         │
                       │ Query → Embedding →     │
                       │ ChromaDB Cosine Search  │
                       │ → Top-K Chunks          │
                       └──────────┬─────────────┘
                                    │
                                    ▼
                       ┌────────────────────────┐
                       │   Escalation Check      │
                       │ - Low confidence?       │
                       │ - Sensitive topic?      │
                       │ - Repeated frustration? │
                       └──────────┬─────────────┘
                            │              │
                  No trigger│              │Trigger fired
                            ▼              ▼
              ┌─────────────────────┐   ┌────────────────────────┐
              │ Adaptive Generator   │   │   Human Handoff         │
              │ (persona-specific    │   │   Generate structured   │
              │  prompt + grounded   │   │   JSON summary for      │
              │  context)            │   │   human agent           │
              └──────────┬──────────┘   └──────────┬─────────────┘
                          │                          │
                          ▼                          ▼
                ┌─────────────────────────────────────────┐
                │      Response shown in CLI / Streamlit    │
                │   (persona badge, sources, escalation     │
                │           status, response text)          │
                └────────────────────────────────────────────┘
```

## 4. Persona Detection Strategy

**Classification method:** A single Gemini call per message, using a structured
JSON response schema (`response_schema` with an `enum` constraint on `persona`),
rather than free-text classification + regex parsing. This guarantees the output
is always one of the three valid persona strings.

**Prompt design:** The system instruction describes each persona's defining
characteristics (vocabulary, tone, focus) drawn directly from the assignment brief,
and asks the model to also return a `confidence` score and a one-line `reasoning`
string — both surfaced in the UI for transparency.

**Rules used:**
- Technical Expert → jargon, API/error-code/config mentions, requests for detail.
- Frustrated User → emotional language, urgency, repeated complaints.
- Business Executive → outcome/impact framing, timelines, brevity preference.
- If a message could fit more than one persona, the model is instructed to pick
  whichever tone *dominates* the message (e.g. a technical complaint phrased
  angrily leans Frustrated User if the emotion dominates, Technical Expert if the
  technical detail dominates).
- If the classifier call fails for any reason (network, malformed response), the
  system falls back to `Business Executive` with `confidence: 0.0` rather than
  crashing the pipeline — generation and retrieval still proceed normally.

## 5. RAG Pipeline Design

**Chunking strategy:** `RecursiveCharacterTextSplitter` with `chunk_size=500`,
`chunk_overlap=50`. This recursively splits on paragraph breaks, then sentences,
then words, only falling back to raw character splitting as a last resort — so
chunks stay topically coherent and a 50-character overlap prevents a step-by-step
instruction or API field name from being cut in half across a chunk boundary.

**Embedding model:** Gemini `text-embedding-004`, called once per chunk at
ingestion time and once per query at retrieval time. The exact same model is
used for both so the vectors live in the same semantic space.

**Vector database choice:** ChromaDB, run as a **persistent local client**
(`chromadb.PersistentClient`) pointed at `./chroma_db`. This was chosen over an
in-memory-only setup specifically so the index survives across Streamlit/CLI
restarts — the knowledge base is only re-embedded when `ingest_knowledge_base.py`
is explicitly run, not on every app launch or chat turn (a deliberate
performance/cost decision called out in the assignment's optimization tips).

**Retrieval strategy:** Top-`k=3` nearest neighbors by similarity. Chroma's raw
distance score is converted into a normalized similarity-style score in `[0, 1]`
for consistent threshold comparisons in the escalation logic. Each retrieved
chunk carries metadata: `source` (file name), `section` (best-effort heading
extracted via regex from the chunk text), and `page` (for PDF sources only).

## 6. Escalation Logic

**Escalation triggers (all configurable in `src/config.py`):**

1. **Low retrieval confidence** — if the best similarity score among retrieved
   chunks falls below `RETRIEVAL_CONFIDENCE_THRESHOLD` (default `0.45`), or no
   chunks are retrieved at all.
2. **Sensitive topic detected** — a keyword check (`SENSITIVE_KEYWORDS` list)
   covering billing disputes, refunds, chargebacks, legal threats, account
   compromise, and data-deletion requests. These are escalated regardless of
   retrieval confidence, since they require human judgment per policy.
3. **Repeated frustration** — if the customer's persona has been classified as
   `Frustrated User` for `FRUSTRATION_TURN_THRESHOLD` (default `3`) consecutive
   turns in the same session, the conversation is escalated even if each
   individual message had a confident retrieval match — the signal here is
   *unresolved* frustration over time, not any single message.

**Confidence thresholds:** `0.45` for retrieval (tunable — lower it to escalate
less often, raise it to escalate more conservatively) and `3` consecutive turns
for the frustration trigger.

When any trigger fires, a structured JSON handoff summary is generated
(see `src/escalator.py: generate_handoff_summary`) containing the detected
persona, a truncated issue summary, full conversation history, which knowledge-base
documents were retrieved, an empty/populated attempted-steps list, the specific
escalation reason(s), the confidence score, and a tailored recommended action.

## 7. Project Structure

```
persona-support-agent/
│
├── data/                          # Knowledge base (11 documents)
│   ├── password_reset.md
│   ├── api_authentication.md
│   ├── database_integration.md
│   ├── data_export_privacy.md
│   ├── webhook_configuration.md
│   ├── rate_limiting.md
│   ├── team_permissions.md
│   ├── billing_policy.txt
│   ├── account_security.txt
│   ├── plan_management.txt
│   ├── mobile_sync.txt
│   └── sso_configuration_guide.pdf   <-- required PDF document
│
├── src/
│   ├── __init__.py
│   ├── config.py                  # Thresholds, model names, paths
│   ├── classifier.py               # Persona detection (Gemini structured output)
│   ├── rag_pipeline.py             # Chunker, embedder, ChromaDB ingestion + retrieval
│   ├── generator.py                # Persona prompt compiler + LLM response generator
│   └── escalator.py                # Escalation triggers + handoff JSON builder
│
├── scripts/
│   └── make_pdf.py                 # Generates the SSO guide PDF (one-time)
│
├── app.py                          # Streamlit web UI (bonus)
├── cli.py                          # Command-line chatbot (minimum requirement)
├── ingest_knowledge_base.py        # One-time/on-demand index builder
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 8. Setup Instructions

1. **Clone the repository and create a virtual environment:**
   ```bash
   git clone <your-repo-url>
   cd persona-support-agent
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API key:**
   ```bash
   cp .env.example .env
   # then edit .env and paste your real Gemini API key:
   # GEMINI_API_KEY="your_actual_gemini_api_key_here"
   ```
   Get a key from [Google AI Studio](https://aistudio.google.com/app/apikey).

4. **Build the knowledge base index** (one-time, re-run after editing `/data`):
   ```bash
   python ingest_knowledge_base.py
   # or to force a full rebuild:
   python ingest_knowledge_base.py --reset
   ```

5. **Run the app:**
   ```bash
   # CLI:
   python cli.py

   # Streamlit web UI:
   streamlit run app.py
   ```

## 9. Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Google Gemini API key, used for both generation and embeddings. |

## 10. Example Queries

| # | Query | Expected Persona | Expected Behavior |
|---|---|---|---|
| 1 | "Where is the guide to clear cookies? It's been an hour and nothing is loading!" | Frustrated User | Empathetic opener, simple bulleted steps. |
| 2 | "What are the header parameter requirements for your bearer token auth?" | Technical Expert | Detailed, code/header-level technical answer. |
| 3 | "We need a timeline of when billing disputes are resolved." | Business Executive | Short, impact/timeline-focused — likely escalates (billing keyword). |
| 4 | "I'm experiencing internal errors with your database integration." | Technical Expert | Retrieves database integration doc, gives root-cause + steps. |
| 5 | "My billing statement has unexpected duplicate charges. I demand an immediate refund!" | Frustrated User | **Escalates** — sensitive billing topic, generates handoff JSON. |

## 11. Known Limitations

- **Section/heading metadata** for `.txt`/`.md` files is extracted with a
  best-effort regex (looking for Markdown headings or numbered ALL-CAPS section
  titles). Plain prose without clear headings falls back to a generic
  `"General"` label.
- **Frustration tracking** is based on persona classification per turn, not a
  dedicated sentiment-trend model — a customer who is frustrated but phrases
  it in technical language on a given turn may not register as "Frustrated User"
  for that turn, slightly delaying the repeated-frustration trigger.
- **No conversation persistence** across sessions — conversation memory exists
  only within a single CLI run or Streamlit session; closing the app clears it.
- **Single embedding/generation provider** — the pipeline is built specifically
  around the Gemini SDK; swapping providers would require changes to
  `classifier.py`, `generator.py`, and the embedding calls in `rag_pipeline.py`.
- **Sensitive-topic detection is keyword-based**, not semantic — it will miss
  paraphrased sensitive requests that avoid the configured keyword list, and
  could occasionally over-trigger on benign mentions of a keyword in passing.

### Future Improvements
- Replace keyword-based sensitive-topic detection with a small classifier call.
- Add a feedback button in the Streamlit UI to log false escalations/non-escalations.
- Add a lightweight dashboard tab showing persona distribution and escalation
  rate across a session for analytics.
- Support multi-turn context in the generator itself (currently each turn is
  generated independently of prior assistant responses, though escalation logic
  does track persona history).
