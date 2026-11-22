"""
dialogue.py - Dialogue and Context Management Module for CIUX Birthday Assistant V5.

Maintains multi-turn conversational context per session:
- Tracks last person, relationship, month, intent, and previous queries.
- Intelligently resolves ellipsis and pronouns (e.g. "What about October?", "Where does he live?").
- Asks clarification questions when queries are ambiguous.
- Prevents entity leakage on independent queries.
- Thread-safe session isolation.
"""

from datetime import date
import re
import threading
from typing import Any, Dict, List, Optional

from service import BirthdayService, MONTH_NAMES


class DialogueManager:
    """Manages conversational session state and contextual query resolution."""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Retrieve or initialize the context dictionary for a specific session."""
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = {
                    "last_person": None,
                    "last_person_id": None,
                    "last_relationship": None,
                    "last_month": None,
                    "last_intent": None,
                    "previous_query": None,
                    "history": []
                }
            return self._sessions[session_id]

    def reset_context(self, session_id: str) -> None:
        """Clear the context for the given session."""
        with self._lock:
            self._sessions[session_id] = {
                "last_person": None,
                "last_person_id": None,
                "last_relationship": None,
                "last_month": None,
                "last_intent": None,
                "previous_query": None,
                "history": []
            }

    def update_context(
        self,
        session_id: str,
        intent: str,
        entities: Dict[str, Any],
        query: str,
        response_text: str
    ) -> None:
        """Update context attributes after a successful turn."""
        with self._lock:
            ctx = self.get_context(session_id)
            if entities.get("person_name"):
                ctx["last_person"] = entities["person_name"]
            if entities.get("person_id"):
                ctx["last_person_id"] = entities["person_id"]
            if entities.get("relationship"):
                ctx["last_relationship"] = entities["relationship"]
            if entities.get("month"):
                ctx["last_month"] = entities["month"]
            ctx["last_intent"] = intent
            ctx["previous_query"] = query
            ctx["history"].append({"user": query, "assistant": response_text})
            # Keep history bounded
            if len(ctx["history"]) > 20:
                ctx["history"] = ctx["history"][-20:]

    def process_turn(
        self,
        session_id: str,
        nlu_result: Dict[str, Any],
        service: BirthdayService,
        ref_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Resolve conversation context against the current turn, dispatch to BirthdayService,
        and update conversation state.
        """
        raw_msg = nlu_result.get("raw_message", "").strip()
        intent = nlu_result.get("intent", "unknown")
        entities = dict(nlu_result.get("entities", {}))
        engine = nlu_result.get("engine", "rule_based")

        ctx = self.get_context(session_id)
        lower_msg = raw_msg.lower()

        # -------------------------------------------------------------
        # 1. Check for Contextual Follow-up Patterns
        # -------------------------------------------------------------

        # Pattern A: "What about October?" / "And October?" / "How about November?"
        is_followup_pattern = bool(re.search(r"\b(what\s+about|how\s+about|and|in)\b", lower_msg)) or len(lower_msg.split()) <= 3

        if entities.get("month") and not entities.get("relationship") and not entities.get("person_name"):
            # If user provides a month and previous turn had a relationship:
            if ctx.get("last_relationship"):
                entities["relationship"] = ctx["last_relationship"]
                # If previous intent was count_birthdays and query didn't explicitly ask to show/list
                if ctx.get("last_intent") == "count_birthdays" and "show" not in lower_msg and "list" not in lower_msg:
                    intent = "count_birthdays"
                else:
                    intent = "birthday_search"

        # Pattern B: "What about nieces?" / "And colleagues?"
        if entities.get("relationship") and not entities.get("month") and not entities.get("person_name"):
            if is_followup_pattern and ctx.get("last_month"):
                entities["month"] = ctx["last_month"]
                if ctx.get("last_intent") == "count_birthdays" and "show" not in lower_msg:
                    intent = "count_birthdays"
                else:
                    intent = "birthday_search"

        # Pattern C: Follow-up counting ("How many?", "How many are there?")
        if intent == "count_birthdays":
            if not entities.get("month") and not entities.get("relationship"):
                if ctx.get("last_month"):
                    entities["month"] = ctx["last_month"]
                if ctx.get("last_relationship"):
                    entities["relationship"] = ctx["last_relationship"]

        # Pattern D: Pronoun resolution ("Where does he live?", "When is his birthday?", "Where do they live?")
        pronoun_match = re.search(r"\b(he|she|him|her|they|his|hers|their)\b", lower_msg)
        curr_person = str(entities.get("person_name", "")).strip().lower()
        if not entities.get("person_name") or curr_person in ("he", "she", "him", "her", "they", "his", "hers", "their"):
            if pronoun_match or intent in ("person_place", "person_birthday"):
                if ctx.get("last_person"):
                    entities["person_name"] = ctx["last_person"]
                elif ctx.get("last_person_id"):
                    entities["person_id"] = ctx["last_person_id"]

        # -------------------------------------------------------------
        # 2. Ambiguity & Clarification Checks
        # -------------------------------------------------------------
        if intent == "person_place" and not entities.get("person_name") and not entities.get("person_id"):
            return {
                "answer": "Whose location would you like to check? Please provide a person's name or ID (e.g., 'Where does Rahul live?').",
                "debug": {
                    "intent": intent,
                    "entities": entities,
                    "engine": engine,
                    "context": dict(ctx),
                    "status": "clarification_needed"
                }
            }

        if intent == "person_birthday" and not entities.get("person_name") and not entities.get("person_id"):
            return {
                "answer": "Whose birthday would you like to check? Please specify a person's name (e.g., 'When is Rahul Patil's birthday?').",
                "debug": {
                    "intent": intent,
                    "entities": entities,
                    "engine": engine,
                    "context": dict(ctx),
                    "status": "clarification_needed"
                }
            }

        # -------------------------------------------------------------
        # 3. Dispatch to BirthdayService
        # -------------------------------------------------------------
        dispatch_result: Dict[str, Any] = {}

        if intent == "count_birthdays":
            dispatch_result = service.count_birthdays(
                month=entities.get("month"),
                relationship=entities.get("relationship")
            )

        elif intent == "person_place":
            dispatch_result = service.get_person_location(
                name=entities.get("person_name") or "",
                person_id=entities.get("person_id")
            )

        elif intent == "tomorrow_birthdays":
            dispatch_result = service.get_tomorrow_birthdays(ref_date=ref_date)

        elif intent == "upcoming_birthdays":
            dispatch_result = service.get_upcoming_birthdays(ref_date=ref_date)

        elif intent == "person_birthday":
            if entities.get("person_id"):
                dispatch_result = service.search_by_person_id(entities["person_id"])
            else:
                dispatch_result = service.search_by_person(entities.get("person_name", ""))

        elif intent == "birthday_search":
            if entities.get("relative_month") == "next":
                dispatch_result = service.get_next_month_birthdays(ref_date=ref_date)
            elif entities.get("person_id"):
                dispatch_result = service.search_by_person_id(entities["person_id"])
            else:
                dispatch_result = service.search_birthdays(
                    month=entities.get("month"),
                    relationship=entities.get("relationship")
                )

        else:
            # Check for standard greetings
            if re.search(r"\b(hi|hello|hey|namaste|good\s+morning|good\s+afternoon|good\s+evening)\b", lower_msg):
                answer = (
                    "Hello! 👋 I am your **CIUX Birthday Assistant (V5)**.\n\n"
                    "You can ask me questions about:\n"
                    "• **Birthdays by month:** *'Show birthdays in September'*\n"
                    "• **Birthdays by relationship:** *'Show my nephews' birthdays'*\n"
                    "• **Birthday counts:** *'How many nephews have birthdays in October?'*\n"
                    "• **Upcoming events:** *'Show upcoming birthdays'* or *'Who has a birthday tomorrow?'*\n"
                    "• **Person details:** *'Where does Rahul live?'* or *'When is Lakshmi's birthday?'*"
                )
            else:
                answer = (
                    "I couldn't identify the birthday query from your question. "
                    "You can ask me things like:\n"
                    "• *'Show birthdays in September'*\n"
                    "• *'How many nephews have birthdays in October?'*\n"
                    "• *'Where does Rahul live?'*\n"
                    "• *'Who has a birthday tomorrow?'*\n"
                    "• *'Show upcoming birthdays'*"
                )

            dispatch_result = {
                "answer": answer,
                "count": 0,
                "results": [],
                "query_type": "unknown"
            }

        # -------------------------------------------------------------
        # 4. Context Update & Return
        # -------------------------------------------------------------
        final_answer = dispatch_result.get("answer", "")
        self.update_context(session_id, intent, entities, raw_msg, final_answer)

        debug_info = {
            "intent": intent,
            "entities": entities,
            "engine": engine,
            "query_type": dispatch_result.get("query_type", intent),
            "records_found": dispatch_result.get("count", len(dispatch_result.get("results", []))),
            "context": {
                "last_person": ctx.get("last_person"),
                "last_relationship": ctx.get("last_relationship"),
                "last_month": ctx.get("last_month"),
                "last_intent": ctx.get("last_intent")
            }
        }

        return {
            "answer": final_answer,
            "debug": debug_info
        }
