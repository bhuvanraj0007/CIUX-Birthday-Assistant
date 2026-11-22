"""
llm_nlu.py - LLM-Assisted Natural Language Understanding with Rule-Based Fallback.
CIUX Birthday Assistant - Version 5.

Uses OpenAI Structured Outputs to interpret intent and extract entities.
Strictly interpretation-only: The LLM NEVER generates factual birthday data.
If the API key is missing or calls fail, seamlessly falls back to RuleBasedNLU without crashing.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from config import OPENAI_API_KEY, OPENAI_MODEL
from nlu import RuleBasedNLU

logger = logging.getLogger("CIUX_LLM_NLU")

ALLOWED_INTENTS = {
    "birthday_search",
    "count_birthdays",
    "upcoming_birthdays",
    "person_place",
    "person_birthday",
    "tomorrow_birthdays",
    "unknown"
}

SYSTEM_PROMPT = """You are a Natural Language Understanding parser for the CIUX Birthday Assistant.
Your task is ONLY to interpret the user's message, classify their intent, and extract mentioned entities into structured JSON.
You must NEVER generate factual data, answer birthday questions directly, or invent birthdays, names, or relationships.

Allowed intents:
1. birthday_search: User wants to search birthdays by month, relationship, or general inquiry.
2. count_birthdays: User asks how many people have birthdays (e.g. "How many nephews have birthdays in October?").
3. upcoming_birthdays: User asks about upcoming birthdays soon or approaching.
4. person_place: User asks where a person lives or stays (e.g. "Where does Rahul live?").
5. person_birthday: User asks for a specific person's birthday (e.g. "When is Rahul's birthday?").
6. tomorrow_birthdays: User asks about birthdays occurring tomorrow.
7. unknown: Greeting or query unrelated to birthdays, people, or locations.

Extract the following entities (use null if not present):
- person_name: Person's name (string or null)
- person_id: Person's ID like P001, P004 (string or null)
- month: Integer 1 to 12 (integer or null, e.g. 9 for September, 10 for October)
- relationship: Relationship term normalized to singular title case (string or null, e.g. "Nephew", "Sister", "Friend")
- relative_date: "tomorrow", "today", or null
- relative_month: "next", "this", or null

You must respond with ONLY valid JSON adhering exactly to this format:
{
    "intent": "birthday_search",
    "entities": {
        "person_name": null,
        "person_id": null,
        "month": 9,
        "relationship": null,
        "relative_date": null,
        "relative_month": null
    }
}
"""


class LLMAssistedNLU:
    """NLU engine combining OpenAI LLM understanding with a robust rule-based fallback."""

    def __init__(
        self,
        rule_based_nlu: RuleBasedNLU,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.rule_based_nlu = rule_based_nlu
        self.api_key = api_key if api_key is not None else OPENAI_API_KEY
        self.model_name = model_name if model_name is not None else OPENAI_MODEL
        self._openai_client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {e}. Will use rule-based NLU.")

    def _validate_entities(self, raw_entities: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted entities against known dataset constraints."""
        clean_entities: Dict[str, Any] = {
            "person_name": None,
            "person_id": None,
            "month": None,
            "relationship": None,
            "relative_date": None,
            "relative_month": None
        }

        # Validate month
        month = raw_entities.get("month")
        if isinstance(month, int) and 1 <= month <= 12:
            clean_entities["month"] = month
        elif isinstance(month, str) and month.isdigit():
            m_int = int(month)
            if 1 <= m_int <= 12:
                clean_entities["month"] = m_int

        # Validate person_id
        pid = raw_entities.get("person_id")
        if pid and isinstance(pid, str):
            clean_entities["person_id"] = pid.strip().upper()

        # Validate relative date / month
        rel_date = raw_entities.get("relative_date")
        if rel_date in ("tomorrow", "today"):
            clean_entities["relative_date"] = rel_date

        rel_month = raw_entities.get("relative_month")
        if rel_month in ("next", "this"):
            clean_entities["relative_month"] = rel_month

        # Validate relationship
        rel = raw_entities.get("relationship")
        if rel and isinstance(rel, str) and rel.strip():
            # Check rule-based normalization
            norm_rel = self.rule_based_nlu.extract_relationship(rel) or rel.strip().title()
            clean_entities["relationship"] = norm_rel

        # Validate person_name
        name = raw_entities.get("person_name")
        if name and isinstance(name, str) and name.strip():
            name_clean = name.strip()
            # If dataset known names available, check if partial or exact match
            matched = False
            for kn in self.rule_based_nlu.known_names:
                if kn.lower() == name_clean.lower() or name_clean.lower() in kn.lower():
                    clean_entities["person_name"] = kn
                    matched = True
                    break
            if not matched:
                clean_entities["person_name"] = name_clean

        return clean_entities

    def parse(self, message: str) -> Dict[str, Any]:
        """
        Parse user message into structured intent and entities.
        Tries OpenAI LLM if configured; otherwise seamlessly executes rule-based NLU.
        """
        message_clean = message.strip()
        if not message_clean:
            return {
                "intent": "unknown",
                "entities": {
                    "person_name": None,
                    "person_id": None,
                    "month": None,
                    "relationship": None,
                    "relative_date": None,
                    "relative_month": None
                },
                "engine": "rule_based",
                "raw_message": ""
            }

        # If no client or no key, immediately use rule-based engine
        if not self._openai_client or not self.api_key:
            result = self.rule_based_nlu.parse(message_clean)
            result["engine"] = "rule_based"
            return result

        # Try LLM parse
        try:
            response = self._openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message_clean}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )

            response_content = response.choices[0].message.content
            parsed = json.loads(response_content)

            intent = parsed.get("intent", "unknown")
            if intent not in ALLOWED_INTENTS:
                intent = "unknown"

            raw_entities = parsed.get("entities", {})
            validated_entities = self._validate_entities(raw_entities)

            return {
                "intent": intent,
                "entities": validated_entities,
                "engine": "llm",
                "model": self.model_name,
                "raw_message": message_clean
            }

        except Exception as e:
            logger.warning(f"OpenAI API call failed ({e}). Falling back to rule-based NLU.")
            fallback_result = self.rule_based_nlu.parse(message_clean)
            fallback_result["engine"] = "rule_based_fallback"
            fallback_result["llm_error"] = str(e)
            return fallback_result
