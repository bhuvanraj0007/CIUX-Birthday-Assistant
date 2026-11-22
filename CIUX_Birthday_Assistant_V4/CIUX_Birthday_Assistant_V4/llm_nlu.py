"""
LLM-powered Natural Language Understanding Module for CIUX Birthday Assistant V4
Uses OpenAI API (Official Python SDK) with structured JSON output and automatic Rule-based fallback.
Strict requirement: LLM is responsible ONLY for intent and entity interpretation, NEVER for factual data.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from config import OPENAI_API_KEY, OPENAI_MODEL
from nlu import INTENTS, RuleBasedNLU

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an intent recognition and entity extraction engine for a Birthday Assistant.
Analyze the user's input and output ONLY a valid JSON object.

Allowed intents:
- "birthday_search": User wants to find birthdays (e.g., by month, relationship, next month).
- "count_birthdays": User wants to count how many birthdays match criteria.
- "upcoming_birthdays": User wants upcoming birthdays (e.g. next 30 days).
- "person_place": User wants to know where someone lives, stays, or their location.
- "person_birthday": User asks for a specific person's birthday or DOB.
- "tomorrow_birthdays": User asks about birthdays occurring tomorrow.
- "unknown": Greetings, irrelevant questions, or queries not related to birthdays or locations.

Allowed entities:
- "person_name": String (e.g., "Rahul", "Lakshmi Rao") or null.
- "person_id": String (e.g., "P001", "P004") or null.
- "month": Integer 1-12 (e.g., 9 for September, 10 for October) or null.
- "relationship": Normalized singular string (e.g., "nephew", "niece", "friend", "wife", "father", "mother", "brother", "sister", "cousin", "student", "colleague") or null.
- "relative_date": String ("tomorrow", "today") or null.
- "relative_month": String ("next_month", "this_month") or null.

CRITICAL RULES:
1. Output ONLY valid JSON matching this schema. No preamble, no explanation.
2. DO NOT answer the user's question.
3. DO NOT invent any facts, names, or dates.
4. Extract ONLY what is explicitly mentioned in the user's prompt.

Example output format:
{
  "intent": "count_birthdays",
  "entities": {
    "person_name": null,
    "person_id": null,
    "month": 10,
    "relationship": "nephew",
    "relative_date": null,
    "relative_month": null
  }
}
"""


class HybridNLU:
    """Combines OpenAI LLM NLU with reliable Rule-based NLU fallback."""

    def __init__(self, known_names: Optional[List[str]] = None):
        self.rule_nlu = RuleBasedNLU(known_names=known_names)
        self.api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "").strip()
        self.model = OPENAI_MODEL or os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.client = None
        self._init_openai_client()

    def _init_openai_client(self):
        """Safely initialize OpenAI client if API key is present."""
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info(f"OpenAI LLM NLU client initialized with model '{self.model}'")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}. Falling back to Rule-based NLU.")
                self.client = None
        else:
            logger.info("No OPENAI_API_KEY found. HybridNLU will operate using Rule-based NLU.")

    def is_llm_available(self) -> bool:
        """Check if LLM engine is configured and ready."""
        return self.client is not None and bool(self.api_key)

    def parse(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parse user query text.
        Attempts LLM-based parsing if available, automatically falling back to Rule-based NLU.
        """
        cleaned = text.strip()
        if not cleaned:
            return {
                "intent": "unknown",
                "entities": {
                    "person_name": None,
                    "person_id": None,
                    "month": None,
                    "relationship": None,
                    "relative_date": None,
                    "relative_month": None,
                },
                "raw_text": "",
                "engine": "rule_based",
            }

        # If LLM client is available, attempt LLM parsing
        if self.is_llm_available():
            try:
                result = self._call_llm(cleaned)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"LLM NLU invocation failed ({e}). Falling back to Rule-based NLU.")

        # Fallback to Rule-based NLU
        rule_result = self.rule_nlu.parse(cleaned)
        rule_result["engine"] = "rule_based" if not self.is_llm_available() else "rule_based_fallback"
        return rule_result

    def _call_llm(self, text: str) -> Optional[Dict[str, Any]]:
        """Call OpenAI API with JSON mode and validate output."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=250,
        )

        content = response.choices[0].message.content
        if not content:
            return None

        parsed = json.loads(content)
        intent = parsed.get("intent", "unknown")
        if intent not in INTENTS:
            intent = "unknown"

        raw_entities = parsed.get("entities", {})
        entities = {
            "person_name": raw_entities.get("person_name") or None,
            "person_id": raw_entities.get("person_id") or None,
            "month": self._normalize_month(raw_entities.get("month")),
            "relationship": self._normalize_relationship(raw_entities.get("relationship")),
            "relative_date": raw_entities.get("relative_date") or None,
            "relative_month": raw_entities.get("relative_month") or None,
        }

        # Normalize person_id to uppercase if present
        if entities["person_id"]:
            entities["person_id"] = str(entities["person_id"]).strip().upper()

        return {
            "intent": intent,
            "entities": entities,
            "raw_text": text,
            "engine": "openai_llm",
            "model": self.model,
        }

    def _normalize_month(self, m: Any) -> Optional[int]:
        """Ensure month is an integer 1-12 or None."""
        if m is None:
            return None
        if isinstance(m, int) and 1 <= m <= 12:
            return m
        try:
            val = int(m)
            if 1 <= val <= 12:
                return val
        except (ValueError, TypeError):
            pass
        return None

    def _normalize_relationship(self, rel: Any) -> Optional[str]:
        """Normalize relationship to lowercase singular string."""
        if not rel or not isinstance(rel, str):
            return None
        cleaned = rel.strip().lower()
        if cleaned.endswith("s") and cleaned[:-1] in [
            "nephew", "niece", "friend", "brother", "sister", "uncle", "aunt", "cousin", "student", "colleague"
        ]:
            return cleaned[:-1]
        return cleaned
