"""
Dialogue Management Module for CIUX Birthday Assistant V4
Maintains conversational memory, manages context per session, resolves follow-up queries,
handles disambiguation, and coordinates between NLU and BirthdayService.
"""

import calendar
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from llm_nlu import HybridNLU
from service import BirthdayService

logger = logging.getLogger(__name__)


class DialogueState:
    """Encapsulates session-isolated dialogue memory."""

    def __init__(
        self,
        last_selected_person: Optional[str] = None,
        last_person_id: Optional[str] = None,
        last_relationship: Optional[str] = None,
        last_month: Optional[Union[int, str]] = None,
        last_intent: Optional[str] = None,
        previous_query: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ):
        self.last_selected_person = last_selected_person
        self.last_person_id = last_person_id
        self.last_relationship = last_relationship
        self.last_month = last_month
        self.last_intent = last_intent
        self.previous_query = previous_query
        self.history = history if history is not None else []

    def reset(self):
        """Reset conversation memory."""
        self.last_selected_person = None
        self.last_person_id = None
        self.last_relationship = None
        self.last_month = None
        self.last_intent = None
        self.previous_query = None
        self.history = []

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state for Flask session storage."""
        return {
            "last_selected_person": self.last_selected_person,
            "last_person_id": self.last_person_id,
            "last_relationship": self.last_relationship,
            "last_month": self.last_month,
            "last_intent": self.last_intent,
            "previous_query": self.previous_query,
            "history": self.history[-10:],  # keep last 10 turns
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "DialogueState":
        """Deserialize state from dictionary."""
        if not data:
            return cls()
        return cls(
            last_selected_person=data.get("last_selected_person"),
            last_person_id=data.get("last_person_id"),
            last_relationship=data.get("last_relationship"),
            last_month=data.get("last_month"),
            last_intent=data.get("last_intent"),
            previous_query=data.get("previous_query"),
            history=data.get("history", []),
        )


class DialogueManager:
    """Coordinates NLU parsing, context resolution, and Service execution."""

    def __init__(self, service: BirthdayService, nlu: Optional[HybridNLU] = None):
        self.service = service
        # Populate known names from dataset for better NLU entity extraction
        known_names = []
        if not self.service.df.empty and "name" in self.service.df.columns:
            known_names = self.service.df["name"].dropna().tolist()
        self.nlu = nlu if nlu else HybridNLU(known_names=known_names)

    def process_message(
        self, user_message: str, state: DialogueState
    ) -> Tuple[str, Dict[str, Any], DialogueState]:
        """
        Process a user input string within a conversational state context.
        Returns:
            (answer_text, debug_dict, updated_state)
        """
        cleaned_msg = user_message.strip()
        if not cleaned_msg:
            return (
                "Please enter a question or query about birthdays.",
                {"intent": "none", "entities": {}, "engine": "none"},
                state,
            )

        # 1. Parse using Hybrid NLU (LLM with Rule-based fallback)
        nlu_result = self.nlu.parse(cleaned_msg, context=state.to_dict())
        intent = nlu_result.get("intent", "unknown")
        entities = nlu_result.get("entities", {})

        # 2. Contextual Resolution and Follow-up Merging
        intent, resolved_entities, context_applied = self._resolve_context(
            cleaned_msg, intent, entities, state
        )

        # 3. Dispatch to service handler
        answer, debug_meta = self._dispatch_intent(
            intent, resolved_entities, state, cleaned_msg
        )

        # 4. Update dialogue state based on successful execution
        self._update_state(state, intent, resolved_entities, cleaned_msg, answer)

        # 5. Build comprehensive debug info
        debug_info = {
            "intent": intent,
            "entities": resolved_entities,
            "raw_text": cleaned_msg,
            "engine": nlu_result.get("engine", "unknown"),
            "context_applied": context_applied,
            "session_context": {
                "last_selected_person": state.last_selected_person,
                "last_person_id": state.last_person_id,
                "last_relationship": state.last_relationship,
                "last_month": state.last_month,
                "last_intent": state.last_intent,
            },
        }
        if "model" in nlu_result:
            debug_info["llm_model"] = nlu_result["model"]

        return answer, debug_info, state

    def _resolve_context(
        self,
        raw_msg: str,
        intent: str,
        entities: Dict[str, Any],
        state: DialogueState,
    ) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        """
        Merge previous conversational context for follow-up queries.
        Examples:
        - "What about October?" -> inherits previous relationship (e.g. nephew)
        - "Where does he live?" -> inherits previous person (e.g. Rahul)
        - "What about her birthday?" -> inherits previous person
        """
        resolved = dict(entities)
        context_applied = {}
        raw_lower = raw_msg.lower()

        # Check for pronoun references or implied person
        pronoun_found = bool(
            re.search(r"\b(he|she|him|her|his|they|them|their)\b", raw_lower)
        )
        is_follow_up_phrase = bool(
            re.search(r"\b(what\s+about|and|how\s+about|what\s+of)\b", raw_lower)
        )

        # Follow-up for person-specific query
        if pronoun_found or (
            intent in ["person_place", "person_birthday"]
            and not resolved.get("person_name")
            and not resolved.get("person_id")
        ):
            if state.last_selected_person:
                resolved["person_name"] = state.last_selected_person
                context_applied["person_name_from_context"] = state.last_selected_person
            if state.last_person_id:
                resolved["person_id"] = state.last_person_id
                context_applied["person_id_from_context"] = state.last_person_id

        # Follow-up query like "What about October?" or "In November?"
        # User supplied a month, but no relationship, and previously asked about a relationship
        if (
            resolved.get("month")
            and not resolved.get("relationship")
            and state.last_relationship
            and (is_follow_up_phrase or intent in ["birthday_search", "count_birthdays"])
        ):
            resolved["relationship"] = state.last_relationship
            context_applied["relationship_from_context"] = state.last_relationship
            # If previous intent was count_birthdays and current message looks like a count or follow-up
            if state.last_intent == "count_birthdays" and (
                "count" in raw_lower or "how many" in raw_lower or is_follow_up_phrase
            ):
                intent = "count_birthdays"

        # User supplied a relationship, but no month, and previously had a month
        if (
            resolved.get("relationship")
            and not resolved.get("month")
            and state.last_month
            and is_follow_up_phrase
        ):
            resolved["month"] = state.last_month
            context_applied["month_from_context"] = state.last_month

        return intent, resolved, context_applied

    def _dispatch_intent(
        self,
        intent: str,
        entities: Dict[str, Any],
        state: DialogueState,
        raw_msg: str,
    ) -> Tuple[str, Dict[str, Any]]:
        """Dispatch query to BirthdayService and format response."""
        meta = {}

        if intent == "birthday_search":
            return self._handle_birthday_search(entities, state)

        elif intent == "count_birthdays":
            return self._handle_count_birthdays(entities, state)

        elif intent == "upcoming_birthdays":
            return self._handle_upcoming_birthdays(entities)

        elif intent == "tomorrow_birthdays":
            return self._handle_tomorrow_birthdays()

        elif intent == "person_birthday":
            return self._handle_person_birthday(entities, state)

        elif intent == "person_place":
            return self._handle_person_place(entities, state)

        else:
            return self._handle_unknown(raw_msg)

    def _handle_birthday_search(
        self, entities: Dict[str, Any], state: DialogueState
    ) -> Tuple[str, Dict[str, Any]]:
        """Handle general birthday searches."""
        rel_month = entities.get("relative_month")
        month = entities.get("month")
        relationship = entities.get("relationship")
        person_name = entities.get("person_name")
        person_id = entities.get("person_id")

        # Handle "next month"
        if rel_month == "next_month":
            m_num, m_name, records = self.service.get_next_month_birthdays()
            if relationship:
                records = self.service.filter_by_relationship(relationship, records=records)
            title = f"Birthdays in Next Month ({m_name})"
            if relationship:
                title += f" for {relationship.capitalize()}"
            answer = self.service.format_birthday_records(records, title=title)
            return answer, {"count": len(records), "month": m_name}

        # Regular search by month, relationship, name, or ID
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
            m_int = self.service.parse_month(month)
            m_str = calendar.month_name[m_int] if m_int else str(month)
            notes.append(f"Month: {m_str}")
        if person_name:
            notes.append(f"Name search: {person_name}")

        context_notes = " | ".join(notes) if notes else ""
        answer = self.service.format_birthday_records(
            records, title=title, context_notes=context_notes
        )
        return answer, {"count": len(records)}

    def _handle_count_birthdays(
        self, entities: Dict[str, Any], state: DialogueState
    ) -> Tuple[str, Dict[str, Any]]:
        """Handle birthday counting queries."""
        month = entities.get("month")
        relationship = entities.get("relationship")
        person_name = entities.get("person_name")

        count, records = self.service.count_birthdays(
            month=month, relationship=relationship, person_name=person_name
        )
        answer = self.service.format_count_response(
            count=count, relationship=relationship, month=month, records=records
        )
        return answer, {"count": count}

    def _handle_upcoming_birthdays(
        self, entities: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handle upcoming birthdays lookup."""
        records = self.service.get_upcoming_birthdays(days=30)
        answer = self.service.format_upcoming_records(records, days=30)
        return answer, {"count": len(records)}

    def _handle_tomorrow_birthdays(self) -> Tuple[str, Dict[str, Any]]:
        """Handle tomorrow's birthdays query."""
        records = self.service.get_tomorrow_birthdays()
        if not records:
            return "There are **no birthdays tomorrow** based on the dataset.", {"count": 0}

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
        return "\n".join(lines), {"count": len(records)}

    def _handle_person_birthday(
        self, entities: Dict[str, Any], state: DialogueState
    ) -> Tuple[str, Dict[str, Any]]:
        """Handle querying a specific person's birthday."""
        name = entities.get("person_name")
        pid = entities.get("person_id")

        if not name and not pid:
            return (
                "Whose birthday would you like to know? Please provide a person's name or Person ID.",
                {"error": "missing_person"},
            )

        matches = (
            self.service.search_by_person_id(pid)
            if pid
            else self.service.search_by_person_name(name)
        )

        if not matches:
            target = pid if pid else name
            return (
                f"No record found for **{target}** in the Excel dataset.",
                {"count": 0},
            )

        if len(matches) > 1:
            # Ambiguity clarification
            lines = [
                f"I found multiple people matching **{name}**. Please clarify which person you mean:",
                "",
            ]
            for m in matches:
                lines.append(
                    f"- **{m['name']}** (ID: `{m['person_id']}`, Born: {m['formatted_dob']}, Relation: {m['relationship']})"
                )
            lines.append("\nYou can specify by typing their full name or Person ID.")
            return "\n".join(lines), {"ambiguous_count": len(matches)}

        # Exactly 1 match
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
        return answer, {"person_id": p_id, "name": p_name}

    def _handle_person_place(
        self, entities: Dict[str, Any], state: DialogueState
    ) -> Tuple[str, Dict[str, Any]]:
        """Handle querying where someone lives / their place of stay."""
        name = entities.get("person_name")
        pid = entities.get("person_id")

        if not name and not pid:
            return (
                "Whose location would you like to look up? Please provide a person's name or Person ID.",
                {"error": "missing_person"},
            )

        person, matches = self.service.get_person_location(name=name, person_id=pid)

        if not matches:
            target = pid if pid else name
            return (
                f"No location record found for **{target}** in the Excel dataset.",
                {"count": 0},
            )

        if len(matches) > 1:
            # Ambiguity clarification
            lines = [
                f"I found multiple people matching **{name}**. Which person's location would you like to check?",
                "",
            ]
            for m in matches:
                lines.append(
                    f"- **{m['name']}** (ID: `{m['person_id']}`, Relation: {m['relationship']})"
                )
            lines.append("\nPlease reply with their full name or Person ID.")
            return "\n".join(lines), {"ambiguous_count": len(matches)}

        answer = self.service.format_location_response(person)
        return answer, {"person_id": person.get("person_id"), "name": person.get("name")}

    def _handle_unknown(self, raw_msg: str) -> Tuple[str, Dict[str, Any]]:
        """Handle unrecognized queries gracefully with guidance."""
        answer = (
            "I can help you explore factual birthday information from your dataset! Here are some things you can ask:\n\n"
            "- **Search by Month:** *\"Show birthdays in September\"*\n"
            "- **Search by Relationship:** *\"Show birthdays of nephews\"*\n"
            "- **Count Birthdays:** *\"How many nephews have birthdays in October?\"*\n"
            "- **Upcoming Celebrations:** *\"Show upcoming birthdays\"* or *\"Tomorrow's birthdays\"*\n"
            "- **Find a Birthday:** *\"When is Rahul's birthday?\"*\n"
            "- **Find a Location:** *\"Where does Rahul live?\"*\n\n"
            "All responses are strictly retrieved from `people.xlsx` without inventing any details."
        )
        return answer, {"intent": "unknown"}

    def _update_state(
        self,
        state: DialogueState,
        intent: str,
        entities: Dict[str, Any],
        user_message: str,
        assistant_answer: str,
    ):
        """Update conversation state attributes for future context."""
        state.last_intent = intent
        state.previous_query = user_message

        # Update relationship if explicitly mentioned
        if entities.get("relationship"):
            state.last_relationship = entities["relationship"]

        # Update month if explicitly mentioned
        if entities.get("month"):
            state.last_month = entities["month"]

        # Update person if explicitly identified
        if entities.get("person_name"):
            state.last_selected_person = entities["person_name"]
        if entities.get("person_id"):
            state.last_person_id = entities["person_id"]

        # Append to history
        state.history.append({
            "user": user_message,
            "assistant": assistant_answer,
            "intent": intent,
        })
