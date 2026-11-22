"""
app.py - Flask Web Application for CIUX Birthday Assistant V5.

Integrates:
- Rule-based & LLM-assisted NLU
- Factual Data Query Service (Excel grounded)
- Multi-turn Dialogue & Context Management
- REST endpoints for chat interaction and context reset
"""

import logging
import uuid
from flask import Flask, jsonify, render_template, request, session

from config import DEBUG_MODE, EXCEL_PATH, HOST, OPENAI_API_KEY, OPENAI_MODEL, PORT, SECRET_KEY
from dialogue import DialogueManager
from llm_nlu import LLMAssistedNLU
from nlu import RuleBasedNLU
from service import BirthdayService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
)
logger = logging.getLogger("CIUX_App")

# Initialize Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Initialize core services
logger.info("Initializing BirthdayService with dataset: %s", EXCEL_PATH)
try:
    birthday_service = BirthdayService(EXCEL_PATH)
    logger.info(
        "Dataset loaded successfully with %d registered persons.",
        len(birthday_service.get_known_names())
    )
except Exception as e:
    logger.error("Failed to load Excel dataset: %s", e)
    raise e

rule_based_nlu = RuleBasedNLU(
    known_names=birthday_service.get_known_names(),
    known_relationships=birthday_service.get_known_relationships()
)

llm_nlu = LLMAssistedNLU(
    rule_based_nlu=rule_based_nlu,
    api_key=OPENAI_API_KEY,
    model_name=OPENAI_MODEL
)

dialogue_manager = DialogueManager()


def get_or_create_session_id() -> str:
    """Ensure every client session has an isolated unique session identifier."""
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


@app.route("/", methods=["GET"])
def index():
    """Render the main conversational interface."""
    get_or_create_session_id()
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """
    Handle user natural language queries.
    Accepts JSON: { "message": "..." }
    Returns JSON: { "answer": "...", "debug": { ... } }
    """
    try:
        session_id = get_or_create_session_id()

        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({
                "answer": "Invalid request payload. Please send a valid JSON request.",
                "debug": {"error": "invalid_payload"}
            }), 400

        user_message = str(payload.get("message", "")).strip()

        if not user_message:
            return jsonify({
                "answer": "Please type a question or use the microphone to ask about birthdays, relationships, or locations.",
                "debug": {"status": "empty_input"}
            }), 200

        logger.info("[Session %s] User query: '%s'", session_id[:8], user_message)

        # 1. Parse message using LLM or rule-based fallback
        nlu_result = llm_nlu.parse(user_message)
        logger.info(
            "[Session %s] NLU parsed intent: '%s', engine: '%s'",
            session_id[:8],
            nlu_result.get("intent"),
            nlu_result.get("engine")
        )

        # 2. Process turn via DialogueManager and execute queries
        response = dialogue_manager.process_turn(session_id, nlu_result, birthday_service)

        logger.info("[Session %s] Response generated successfully.", session_id[:8])
        return jsonify(response), 200

    except Exception as e:
        logger.exception("Unexpected error processing /chat: %s", e)
        return jsonify({
            "answer": "An unexpected error occurred while processing your question. Please try again.",
            "debug": {
                "error": str(e),
                "type": type(e).__name__
            }
        }), 500


@app.route("/reset", methods=["POST"])
def reset():
    """Reset the conversational context for the current session."""
    try:
        session_id = get_or_create_session_id()
        dialogue_manager.reset_context(session_id)
        logger.info("[Session %s] Context reset by user.", session_id[:8])

        return jsonify({
            "status": "ok",
            "message": "Conversation context has been cleared. How can I help you today?"
        }), 200

    except Exception as e:
        logger.exception("Error resetting context: %s", e)
        return jsonify({
            "status": "error",
            "message": "Failed to reset conversation context."
        }), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info("Starting CIUX Birthday Assistant V5 on http://%s:%d", HOST, PORT)
    app.run(host=HOST, port=PORT, debug=DEBUG_MODE)
