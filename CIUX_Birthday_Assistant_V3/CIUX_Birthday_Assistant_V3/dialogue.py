"""
Dialogue Management Module for CIUX Birthday Assistant V3
Maintains conversational memory and session state.
Resolves contextual follow-ups (e.g., "What about October?", "How many?"),
handles pronoun resolution, and triggers clarification for ambiguous queries.
"""

import calendar
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from nlu import RuleBasedNLU
from service import BirthdayService

logger = logging.getLogger(__name__)


class DialogueState:
    """Encapsulates conversational memory and session context."""

    def __init__(
        self,
        previous_intent: Optional[str] = None,
        previous_person: Optional[str] = None,
        previous_person_id: Optional[str] = None,
        previous_relationship: Optional[str] = None,
        previous_month: Optional[str] = None,
        previous_query: Optional[str] = None,
        previous_results: Optional[List[Dict[str, Any]]] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ):
        self.previous_intent = previous_intent
        self.previous_person = previous_person
        self.previous_person_id = previous_person_id
        self.previous_relationship = previous_relationship
        self.previous_month = previous_month
        self.previous_query = previous_query
        self.previous_results = previous_results if previous_results is not None else []
        self.history = history if history is not None else []

    def reset(self):
        """Clear all conversation memory."""
        self.previous_intent = None
        self.previous_person = None
        self.previous_person_id = None
        self.previous_relationship = None
        self.previous_month = None
        self.previous_query = None
        self.previous_results = []
        self.history = []

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state for Flask session and API responses."""
        return {
            "previous_intent": self.previous_intent,
            "previous_person": self.previous_person,
            "previous_person_id": self.previous_person_id,
            "previous_relationship": self.previous_relationship,
            "previous_month": self.previous_month,
            "previous_query": self.previous_query,
            "previous_results_count": len(self.previous_results),
            "history": self.history[-10:],
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "DialogueState":
        """Deserialize state from dictionary."""
        if not data:
            return cls()
        return cls(
            previous_intent=data.get("previous_intent"),
            previous_person=data.get("previous_person"),
            previous_person_id=data.get("previous_person_id"),
            previous_relationship=data.get("previous_relationship"),
            previous_month=data.get("previous_month"),
            previous_query=data.get("previous_query"),
            previous_results=data.get("previous_results", []),
            history=data.get("history", []),
        )


class DialogueManager:
    """Orchestrates query parsing, conversational context resolution, and service execution."""

    def __init__(self, service: BirthdayService, nlu: Optional[RuleBasedNLU] = None):
        self.service = service
        known_names = []
        if not self.service.df.empty and "name" in self.service.df.columns:
            known_names = self.service.df["name"].dropna().tolist()
        self.nlu = nlu if nlu else RuleBasedNLU(known_names=known_names)

    def process_message(
        self, user_message: str, state: DialogueState
    ) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        """
        Processes a user message with conversational context.
        Returns:
            (answer_string, debug_dict, state_dict)
        """
        cleaned_msg = user_message.strip()
        if not cleaned_msg:
            return (
                "Please enter a question or query about birthdays.",
                {"intent": "none", "entities": {}},
                state.to_dict(),
            )

        # 1. Parse query using RuleBasedNLU
        nlu_result = self.nlu.parse(cleaned_msg)
        intent = nlu_result["intent"]
        entities = nlu_result["entities"]

        # 2. Context resolution & follow-up merging
        intent, resolved_entities, results_to_use = self._resolve_context(
            cleaned_msg, intent, entities, state
        )

        # 3. Dispatch to service handler
        answer, results = self._dispatch(
            intent, resolved_entities, results_to_use, state, cleaned_msg
        )

        # 4. Update dialogue state
        self._update_state(state, intent, resolved_entities, results, cleaned_msg, answer)

        debug_info = {
            "intent": intent,
            "entities": resolved_entities,
            "raw_text": cleaned_msg,
        }

        return answer, debug_info, state.to_dict()

    def _resolve_context(
        self,
        raw_msg: str,
        intent: str,
        entities: Dict[str, Any],
        state: DialogueState,
    ) -> Tuple[str, Dict[str, Any], Optional[List[Dict[str, Any]]]]:
        """
        Merge conversation context for follow-up queries:
        - "What about October?" -> reuses previous relationship (e.g. nephew)
        - "How many?" -> counts previous results
        - "Where does Rahul live?" / "When is his birthday?" -> reuses previous person
        """
        resolved = dict(entities)
        raw_lower = raw_msg.lower().strip()
        results_to_use = None

        # Check for bare count follow-up ("How many?", "Count them", "How many people?")
        if re.match(r"^(how\s+many\??|count\s+them\??|count\??|how\s+many\s+are\s+there\??)$", raw_lower):
            intent = "count_birthdays"
            if state.previous_results:
                results_to_use = state.previous_results
            if state.previous_relationship:
                resolved["relationship"] = state.previous_relationship
            if state.previous_month:
                resolved["month"] = state.previous_month
            return intent, resolved, results_to_use

        # Pronoun check for person queries
        has_pronoun = bool(re.search(r"\b(he|she|him|her|his|they|them|their)\b", raw_lower))
        is_follow_up_phrase = bool(re.search(r"\b(what\s+about|and|how\s+about|what\s+of)\b", raw_lower))

        # Person follow-up
        if has_pronoun or (
            intent in ["person_place", "person_birthday"]
            and not resolved.get("person_name")
            and not resolved.get("person_id")
        ):
            if state.previous_person:
                resolved["person_name"] = state.previous_person
            if state.previous_person_id:
                resolved["person_id"] = state.previous_person_id

        # Month follow-up ("What about October?", "In November?")
        # User specified month, but not relationship, and previously had relationship
        if (
            resolved.get("month")
            and not resolved.get("relationship")
            and state.previous_relationship
            and (is_follow_up_phrase or intent in ["birthday_search", "count_birthdays"])
        ):
            resolved["relationship"] = state.previous_relationship
            if state.previous_intent == "count_birthdays" and (
                "count" in raw_lower or "how many" in raw_lower or is_follow_up_phrase
            ):
                intent = "count_birthdays"

        # Relationship follow-up ("What about nieces?")
        if (
            resolved.get("relationship")
            and not resolved.get("month")
            and state.previous_month
            and is_follow_up_phrase
        ):
            resolved["month"] = state.previous_month

        return intent, resolved, results_to_use

    def _dispatch(
        self,
        intent: str,
        entities: Dict[str, Any],
        results_to_use: Optional[List[Dict[str, Any]]],
        state: DialogueState,
        raw_msg: str,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Dispatch query to BirthdayService and format results."""

        if intent == "birthday_search":
            rel_month = entities.get("relative_month")
            month = entities.get("month")
            relationship = entities.get("relationship")
            person_name = entities.get("person_name")
            person_id = entities.get("person_id")

            if rel_month == "next_month":
                m_num, m_name, records = self.service.get_next_month_birthdays()
                if relationship:
                    records = self.service.filter_by_relationship(relationship, records=records)
                title = f"Birthdays in Next Month ({m_name})"
                if relationship:
                    title += f" for {relationship.capitalize()}"
                return self.service.format_birthday_records(records, title=title), records

            records = self.service.search_birthdays(
                month=month,
                relationship=relationship,
                person_name=person_name,
                person_id=person_id,
            )

            title = "Matching Birthday Records"
            notes = []
            if relationship:
                notes.append(f"Relationship: {relationship.capitalize()}")
            if month:
                notes.append(f"Month: {month}")
            if person_name:
                notes.append(f"Name search: {person_name}")

            context_notes = " | ".join(notes) if notes else ""
            answer = self.service.format_birthday_records(
                records, title=title, context_notes=context_notes
            )
            return answer, records

        elif intent == "count_birthdays":
            month = entities.get("month")
            relationship = entities.get("relationship")
            person_name = entities.get("person_name")

            if results_to_use is not None:
                count = len(results_to_use)
                records = results_to_use
            else:
                count, records = self.service.count_birthdays(
                    month=month, relationship=relationship, person_name=person_name
                )

            answer = self.service.format_count_response(
                count=count, relationship=relationship, month=month, records=records
            )
            return answer, records

        elif intent == "upcoming_birthdays":
            records = self.service.get_upcoming_birthdays(days=30)
            return self.service.format_upcoming_records(records, days=30), records

        elif intent == "tomorrow_birthdays":
            records = self.service.get_tomorrow_birthdays()
            if not records:
                return "There are **no birthdays tomorrow** based on the dataset.", []

            lines = ["### Birthdays Tomorrow 🎂", ""]
            for idx, r in enumerate(records, start=1):
                name = r.get("name", "Unknown")
                pid = r.get("person_id", "")
                turning = r.get("turning_age", "")
                rel = r.get("relationship", "Unknown")
                place = r.get("place_of_stay", "Unknown")
                age_info = f" (Turning {turning})" if turning else ""
                lines.append(
                    f"{idx}. **{name}** (`{pid}`){age_info}\n"
                    f"   - **Relationship:** {rel}\n"
                    f"   - **Location:** {place}"
                )
            return "\n".join(lines), records

        elif intent == "person_birthday":
            name = entities.get("person_name")
            pid = entities.get("person_id")

            if not name and not pid:
                return (
                    "Whose birthday would you like to know? Please provide a person's name or Person ID.",
                    [],
                )

            matches = (
                self.service.search_by_person_id(pid)
                if pid
                else self.service.search_by_person_name(name)
            )

            if not matches:
                target = pid if pid else name
                return f"No record found for **{target}** in the Excel dataset.", []

            if len(matches) > 1:
                # Clarification for ambiguous queries
                lines = [
                    f"I found multiple people matching **{name}**. Please clarify which person you mean:",
                    "",
                ]
                for m in matches:
                    lines.append(
                        f"- **{m['name']}** (ID: `{m['person_id']}`, Born: {m['formatted_dob']}, Relation: {m['relationship']})"
                    )
                lines.append("\nYou can specify by typing their full name or Person ID.")
                return "\n".join(lines), matches

            person = matches[0]
            p_name = person.get("name", "Unknown")
            p_id = person.get("person_id", "")
            dob_str = person.get("formatted_dob", person.get("dob", "Unknown"))
            rel = person.get("relationship", "Unknown")
            place = person.get("place_of_stay", "Unknown")

            answer = (
                f"**{p_name}** (`{p_id}`)'s date of birth is **{dob_str}**.\n"
                f"- **Relationship:** {rel}\n"
                f"- **Place of Stay:** {place}"
            )
            return answer, matches

        elif intent == "person_place":
            name = entities.get("person_name")
            pid = entities.get("person_id")

            if not name and not pid:
                return (
                    "Whose location would you like to look up? Please provide a person's name or Person ID.",
                    [],
                )

            person, matches = self.service.get_person_location(name=name, person_id=pid)

            if not matches:
                target = pid if pid else name
                return f"No location record found for **{target}** in the Excel dataset.", []

            if len(matches) > 1:
                lines = [
                    f"I found multiple people matching **{name}**. Which person's location would you like to check?",
                    "",
                ]
                for m in matches:
                    lines.append(
                        f"- **{m['name']}** (ID: `{m['person_id']}`, Relation: {m['relationship']})"
                    )
                lines.append("\nPlease reply with their full name or Person ID.")
                return "\n".join(lines), matches

            answer = self.service.format_location_response(person)
            return answer, matches

        else:
            guidance = (
                "I can help you explore factual birthday information from `people.xlsx`! Here are some things you can ask:\n\n"
                "- **Search by Month:** *\"Show birthdays in September\"*\n"
                "- **Search by Relationship:** *\"Show my nephews' birthdays\"*\n"
                "- **Count Birthdays:** *\"How many people have birthdays in January?\"*\n"
                "- **Upcoming Celebrations:** *\"Show upcoming birthdays\"* or *\"Show birthdays tomorrow\"*\n"
                "- **Next Month:** *\"Show next month's birthdays\"*\n"
                "- **Find a Birthday:** *\"When is Rahul's birthday?\"*\n"
                "- **Find a Location:** *\"Where does Rahul live?\"*\n\n"
                "All information is retrieved strictly from the Excel dataset without inventing any facts."
            )
            return guidance, []

    def _update_state(
        self,
        state: DialogueState,
        intent: str,
        entities: Dict[str, Any],
        results: List[Dict[str, Any]],
        user_message: str,
        assistant_answer: str,
    ):
        """Update conversation state attributes for subsequent follow-up queries."""
        state.previous_intent = intent
        state.previous_query = user_message
        state.previous_results = results

        if entities.get("relationship"):
            state.previous_relationship = entities["relationship"]

        if entities.get("month"):
            state.previous_month = entities["month"]

        if entities.get("person_name"):
            state.previous_person = entities["person_name"]

        if entities.get("person_id"):
            state.previous_person_id = entities["person_id"]

        # If a single person was identified in results, set as previous person
        if len(results) == 1:
            state.previous_person = results[0].get("name", state.previous_person)
            state.previous_person_id = results[0].get("person_id", state.previous_person_id)

        state.history.append({
            "user": user_message,
            "assistant": assistant_answer,
            "intent": intent,
        })
