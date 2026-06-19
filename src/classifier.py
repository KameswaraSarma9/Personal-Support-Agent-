"""
classifier.py
Persona detection module. Sends the user's message to Gemini with a
structured JSON response schema so we get a reliable, parseable
classification rather than free-form text we'd need to regex out.
"""
import json
from google import genai
from google.genai import types

from src import config


def _get_client() -> genai.Client:
    return genai.Client(api_key=config.GEMINI_API_KEY)


SYSTEM_INSTRUCTION = (
    "You are an advanced classification engine for a customer support system. "
    "Analyze the sentiment, vocabulary, and tone of an incoming support message "
    "and classify it into exactly one of three customer personas:\n\n"
    "1. 'Technical Expert': Uses technical terminology, asks about APIs, error "
    "codes, configurations, logs, or integration details. Wants precise, "
    "detailed explanations.\n"
    "2. 'Frustrated User': Uses emotional or urgent language, exclamation marks, "
    "repeated complaints, words like 'nothing works', 'still broken', 'immediately'.\n"
    "3. 'Business Executive': Focuses on business impact, operations, timelines, "
    "ROI, or resolution SLAs. Prefers brevity and outcome-oriented framing.\n\n"
    "If a message could plausibly fit more than one persona (e.g., a technical "
    "complaint phrased with frustration), pick the persona that dominates the tone "
    "of the message. Respond strictly in the requested JSON structure with no "
    "extra commentary."
)

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "persona": {
            "type": "STRING",
            "enum": config.PERSONAS,
        },
        "confidence": {"type": "NUMBER"},
        "reasoning": {"type": "STRING"},
    },
    "required": ["persona", "confidence", "reasoning"],
}


def classify_customer_persona(user_message: str) -> dict:
    """
    Classifies a user's message into one of the three supported personas.

    Returns a dict: {"persona": str, "confidence": float, "reasoning": str}
    Falls back to a safe default if the API call fails, so the rest of the
    pipeline (retrieval, generation) can still run.
    """
    try:
        client = _get_client()
        response = client.models.generate_content(
            model=config.GENERATION_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
                temperature=0.1,
            ),
        )
        result = json.loads(response.text)

        # Defensive validation in case the model returns something unexpected
        if result.get("persona") not in config.PERSONAS:
            result["persona"] = "Business Executive"
        result["confidence"] = float(result.get("confidence", 0.5))
        return result

    except Exception as e:
        return {
            "persona": "Business Executive",
            "confidence": 0.0,
            "reasoning": f"Classifier fallback triggered due to an error: {e}",
        }


if __name__ == "__main__":
    test_msg = (
        "Our production API key stopped working with a 401 Unauthorized error. "
        "Check the logs immediately."
    )
    print(json.dumps(classify_customer_persona(test_msg), indent=2))
