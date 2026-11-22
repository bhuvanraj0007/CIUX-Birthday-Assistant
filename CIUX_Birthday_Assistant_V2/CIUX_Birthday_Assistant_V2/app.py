"""
app.py - Flask Web Application for CIUX Birthday Assistant V2.

Runs on http://127.0.0.1:5002 (Port 5002 MUST be used; never port 5000).
Serves chat interface and /chat API.
"""

import sys
import traceback
from flask import Flask, render_template, request, jsonify
from config import HOST, PORT, DEBUG, SECRET_KEY, EXCEL_PATH
from nlu import parse_query
from service import BirthdayService

# Initialize Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# Initialize BirthdayService once at startup
try:
    birthday_service = BirthdayService(excel_path=EXCEL_PATH)
    print(f"[STARTUP] CIUX Birthday Assistant V2 initialized successfully.")
    print(f"[STARTUP] Dataset loaded: {EXCEL_PATH}")
except Exception as e:
    print(f"[ERROR] Fatal error initializing BirthdayService: {e}", file=sys.stderr)
    traceback.print_exc()
    birthday_service = None


@app.route("/", methods=["GET"])
def index():
    """Render the primary chatbot web interface."""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """
    Handle natural language query:
    Request JSON:
        { "message": "Show birthdays in September" }
    Response JSON:
        {
            "answer": "...",
            "debug": {
                "intent": "birthday_search",
                "entities": { ... }
            }
        }
    """
    try:
        data = request.get_json(silent=True) or {}
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({
                "answer": "Please enter a message or question about birthdays.",
                "debug": {
                    "intent": "unknown",
                    "entities": {
                        "person_name": None,
                        "person_id": None,
                        "month": None,
                        "relationship": None,
                        "relative_date": None
                    }
                }
            }), 400

        # Step 1: NLU parsing
        nlu_result = parse_query(user_message)

        # Step 2: Service execution
        if birthday_service is None:
            return jsonify({
                "answer": "The birthday dataset could not be loaded on the server. Please check the Excel file.",
                "debug": nlu_result
            }), 500

        answer = birthday_service.process_nlu_query(nlu_result)

        return jsonify({
            "answer": answer,
            "debug": nlu_result
        })

    except Exception as err:
        print(f"[ERROR] Exception during /chat processing: {err}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({
            "answer": "Sorry, an internal error occurred while processing your request. Please try again.",
            "debug": {
                "error": str(err)
            }
        }), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check route confirming V2 on Port 5002."""
    return jsonify({
        "status": "healthy",
        "service": "CIUX Birthday Assistant V2",
        "port": PORT,
        "dataset_records": len(birthday_service.df) if birthday_service else 0
    })


if __name__ == "__main__":
    print(f"==================================================")
    print(f" CIUX Birthday Assistant V2")
    print(f" Server running at: http://{HOST}:{PORT}")
    print(f" Note: Port 5002 is active (Port 5000 is NOT used).")
    print(f"==================================================")
    app.run(host=HOST, port=PORT, debug=DEBUG)
