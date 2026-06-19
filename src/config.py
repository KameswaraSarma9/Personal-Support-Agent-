"""
config.py
Centralized application configuration: model names, thresholds, paths,
and persona constants. Keeping these in one place makes the escalation
logic and chunking strategy easy to tune without touching business logic.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- API Configuration ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GENERATION_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "gemini-embedding-001"

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DB_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "support_kb"

# --- Chunking Strategy ---
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# --- Retrieval ---
TOP_K = 3

# --- Escalation Thresholds (configurable per assignment requirement 4.4) ---
RETRIEVAL_CONFIDENCE_THRESHOLD = 0.45  # below this, escalate due to low retrieval confidence
FRUSTRATION_TURN_THRESHOLD = 3          # consecutive frustrated turns before forced escalation

# Keywords that flag a message as touching a sensitive topic (billing, legal,
# account security) regardless of retrieval confidence. Checked case-insensitively.
SENSITIVE_KEYWORDS = [
    "refund", "chargeback", "dispute", "unauthorized charge", "fraud",
    "legal", "lawsuit", "sue", "gdpr", "ccpa", "delete my data",
    "account takeover", "compromised", "hacked", "lawyer",
    "cancel my subscription and refund", "unauthorized",
]

# --- Personas ---
PERSONAS = ["Technical Expert", "Frustrated User", "Business Executive"]

# --- UI ---
APP_TITLE = "Persona-Adaptive Customer Support Agent"
