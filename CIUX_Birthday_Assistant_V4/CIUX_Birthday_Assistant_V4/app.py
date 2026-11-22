"""
Flask Backend Application for CIUX Birthday Assistant V4
Provides REST API endpoints for chat interactions, dialogue state management,
context resetting, and serves the modern chatbot user interface.
"""

import logging
import sys
import traceback
from pathlib import Path
from flask import Flask, jsonify, render_template, request, session

import config
from dialogue import DialogueManager, DialogueState
from service import BirthdayService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("CIUX_V4_App")

# Initialize Flask application
app = Flask(
    __name__,
    template_folder=str(config.BASE_DIR / "templates"),
    static_folder=str(config.BASE_DIR / "static"),
)

# Configure Flask app settings
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SESSION_COOKIE_NAME"] = config.SESSION_COOKIE_NAME
app.config["SESSION_COOKIE_HTTPONLY"] = config.SESSION_COOKIE_HTTPONLY
app.config["SESSION_COOKIE_SAMESITE"] = config.SESSION_COOKIE_SAMESITE
app.config["PERMANENT_SESSION_LIFETIME"] = config.PERMANENT_SESSION_LIFETIME

# Initialize core services
logger.info("Initializing BirthdayService...")
birthday_service = BirthdayService(dataset_path=config.DATASET_PATH)
logger.info(f"Loaded {len(birthday_service.df)} records from dataset.")

logger.info("Initializing DialogueManager with Hybrid NLU...")
dialogue_manager = DialogueManager(service=birthday_service)
logger.info(
    f"Hybrid NLU ready. LLM mode: {'Enabled (' + config.OPENAI_MODEL + ')' if dialogue_manager.nlu.is_llm_available() else 'Disabled (Rule-based Fallback Active)'}"
)


def get_session_state() -> DialogueState:
    """Retrieve or initialize DialogueState from Flask session."""
    raw_state = session.get("dialogue_state")
    if not raw_state or not isinstance(raw_state, dict):
        state = DialogueState()
        session["dialogue_state"] = state.to_dict()
        return state
    return DialogueState.from_dict(raw_state)


def save_session_state(state: DialogueState) -> None:
    """Persist DialogueState back to Flask session."""
    session["dialogue_state"] = state.to_dict()
    session.modified = True


@app.route("/", methods=["GET"])
def index():
    """Render the main responsive Chatbot UI."""
    return render_template(
        "index.html",
        records_count=len(birthday_service.df),
        llm_enabled=dialogue_manager.nlu.is_llm_available(),
        llm_model=config.OPENAI_MODEL if dialogue_manager.nlu.is_llm_available() else "Rule-based NLU",
    )


@app.route("/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint.
    Accepts: JSON { "message": "Show birthdays in September" }
    Returns: JSON { "answer": "...", "debug": { ... } }
    """
    try:
        # Validate request content type and body
        if not request.is_json:
            logger.warning("Rejected non-JSON request to /chat")
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json(silent=True)
        if data is None or not isinstance(data, dict):
            logger.warning("Rejected malformed JSON body to /chat")
            return jsonify({"error": "Malformed JSON payload"}), 400

        user_message = data.get("message")
        if user_message is None or not isinstance(user_message, str):
            logger.warning("Missing or non-string 'message' in /chat payload")
            return jsonify({"error": "Field 'message' is required and must be a string"}), 400

        user_message = user_message.strip()
        if not user_message:
            return jsonify({
                "answer": "Please enter a question or query about birthdays.",
                "debug": {
                    "intent": "empty_input",
                    "entities": {},
                    "engine": "none",
                },
            }), 200

        # Enforce maximum input length to prevent DOS
        if len(user_message) > 1000:
            return jsonify({"error": "Message is too long (maximum 1000 characters)"}), 400

        # Retrieve isolated session conversation state
        state = get_session_state()

        # Process message through DialogueManager
        answer, debug_info, updated_state = dialogue_manager.process_message(
            user_message, state
        )

        # Persist updated session state
        save_session_state(updated_state)

        logger.info(
            f"Query: '{user_message}' | Intent: '{debug_info.get('intent')}' | Engine: {debug_info.get('engine')}"
        )

        return jsonify({
            "answer": answer,
            "debug": debug_info,
        }), 200

    except Exception as e:
        logger.error(f"Unhandled exception during /chat: {e}\n{traceback.format_exc()}")
        return jsonify({
            "error": "An internal error occurred while processing your message.",
            "details": str(e) if config.DEBUG_MODE else "Check server logs for details.",
        }), 500


@app.route("/reset", methods=["POST"])
def reset():
    """Reset the session conversation context."""
    try:
        session.pop("dialogue_state", None)
        session.modified = True
        logger.info("Session context reset requested and completed.")
        return jsonify({
            "status": "success",
            "message": "Conversation context has been successfully reset.",
        }), 200
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
        return jsonify({"error": "Failed to reset session"}), 500


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint providing dataset and service status."""
    return jsonify({
        "status": "healthy",
        "dataset_loaded": not birthday_service.df.empty,
        "records_count": len(birthday_service.df),
        "llm_available": dialogue_manager.nlu.is_llm_available(),
        "model": config.OPENAI_MODEL if dialogue_manager.nlu.is_llm_available() else "Rule-based NLU",
    }), 200


if __name__ == "__main__":
    logger.info(f"Starting CIUX Birthday Assistant V4 on http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG_MODE)
