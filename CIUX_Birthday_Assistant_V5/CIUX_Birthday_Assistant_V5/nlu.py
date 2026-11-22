"""
nlu.py - Rule-Based Natural Language Understanding Module.
CIUX Birthday Assistant - Version 5.

Performs robust intent recognition and entity extraction across varied phrasings,
capitalization, singular/plural forms, and conversational variations.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

# Canonical month dictionary (full names and abbreviations)
MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}

# Relationship keyword regex patterns to canonical dataset relationship names
RELATIONSHIP_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b(sister-in-law|sisters-in-law)\b", re.IGNORECASE), "Sister-in-law"),
    (re.compile(r"\b(brother-in-law|brothers-in-law)\b", re.IGNORECASE), "Brother-in-law"),
    (re.compile(r"\b(nephews?)\b", re.IGNORECASE), "Nephew"),
    (re.compile(r"\b(nieces?)\b", re.IGNORECASE), "Niece"),
    (re.compile(r"\b(uncles?)\b", re.IGNORECASE), "Uncle"),
    (re.compile(r"\b(aunts?|aunties?)\b", re.IGNORECASE), "Aunt"),
    (re.compile(r"\b(cousins?)\b", re.IGNORECASE), "Cousin"),
    (re.compile(r"\b(colleagues?|coworkers?|co-workers?)\b", re.IGNORECASE), "Colleague"),
    (re.compile(r"\b(students?)\b", re.IGNORECASE), "Student"),
    (re.compile(r"\b(friends?|buddies|buddy|besties?)\b", re.IGNORECASE), "Friend"),
    (re.compile(r"\b(brothers?)\b", re.IGNORECASE), "Brother"),
    (re.compile(r"\b(sisters?)\b", re.IGNORECASE), "Sister"),
    (re.compile(r"\b(fathers?|dads?|papa)\b", re.IGNORECASE), "Father"),
    (re.compile(r"\b(mothers?|moms?|mummy|mama)\b", re.IGNORECASE), "Mother"),
    (re.compile(r"\b(wives|wife)\b", re.IGNORECASE), "Wife"),
    (re.compile(r"\b(husbands?)\b", re.IGNORECASE), "Husband"),
    (re.compile(r"\b(spouses?)\b", re.IGNORECASE), "Spouse"),
    (re.compile(r"\b(neighbours?|neighbors?)\b", re.IGNORECASE), "Neighbour"),
    (re.compile(r"\b(daughters?)\b", re.IGNORECASE), "Daughter"),
    (re.compile(r"\b(sons?)\b", re.IGNORECASE), "Son")
]

# Common non-person words that should never be identified as person names
EXCLUDED_NAME_TOKENS = {
    "show", "find", "get", "tell", "count", "where", "what", "when", "how", "who", "whom",
    "many", "does", "do", "did", "live", "stay", "birthday", "birthdays", "bday", "month", "year",
    "today", "tomorrow", "yesterday", "upcoming", "next", "this", "all", "any", "people",
    "person", "someone", "anyone", "place", "location", "lives", "stays", "about",
    "he", "she", "him", "her", "they", "them", "his", "hers", "their", "it", "my", "your",
    "nephew", "nephews", "niece", "nieces", "uncle", "uncles", "aunt", "aunts",
    "brother", "sister", "friend", "colleague", "student", "cousin", "father", "mother",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december"
}


class RuleBasedNLU:
    """Rule-based Natural Language Understanding engine."""

    def __init__(self, known_names: Optional[List[str]] = None, known_relationships: Optional[List[str]] = None):
        self.known_names = known_names or []
        self.known_relationships = known_relationships or []

    def set_known_entities(self, names: List[str], relationships: List[str]) -> None:
        """Update known names and relationships dynamically from the dataset."""
        self.known_names = names
        self.known_relationships = relationships

    def extract_person_id(self, text: str) -> Optional[str]:
        """Extract person ID matching P001, P101, etc."""
        m = re.search(r"\b(P\d{3,4})\b", text, re.IGNORECASE)
        return m.group(1).upper() if m else None

    def extract_month(self, text: str) -> Optional[int]:
        """Extract calendar month (1-12) from full names and standard abbreviations."""
        lower_text = text.lower()

        # Handle 'may' carefully (distinguish modal 'may I' vs month 'in May')
        words = re.findall(r"\b\w+\b", lower_text)
        for i, word in enumerate(words):
            if word == "may":
                # Check surrounding context
                prev_word = words[i - 1] if i > 0 else ""
                next_word = words[i + 1] if i < len(words) - 1 else ""
                if prev_word in ("in", "of", "during", "for", "born") or next_word in ("birthdays", "bday", "born", "1st", "2nd"):
                    return 5
                # If query is short or mentions month
                if "month" in lower_text or "birthday" in lower_text:
                    return 5
                continue

            if word in MONTH_MAP and word != "may":
                return MONTH_MAP[word]

        return None

    def extract_relationship(self, text: str) -> Optional[str]:
        """Extract relationship using canonical regex patterns."""
        for pattern, canonical_rel in RELATIONSHIP_PATTERNS:
            if pattern.search(text):
                return canonical_rel
        return None

    def extract_relative_date(self, text: str) -> Optional[str]:
        """Extract relative date references (e.g. tomorrow, today)."""
        lower = text.lower()
        if re.search(r"\b(tomorrow|tomorrow's|tmrw)\b", lower):
            return "tomorrow"
        if re.search(r"\b(today|today's)\b", lower):
            return "today"
        return None

    def extract_relative_month(self, text: str) -> Optional[str]:
        """Extract relative month references (e.g. next month, this month)."""
        lower = text.lower()
        if re.search(r"\b(next month|upcoming month)\b", lower):
            return "next"
        if re.search(r"\b(this month|current month)\b", lower):
            return "this"
        return None

    def extract_person_name(self, text: str) -> Optional[str]:
        """
        Extract person name from text.
        Prioritizes:
        1. Known names in dataset (longest match first)
        2. Syntactic patterns (e.g. 'Where does X live', 'When is X's birthday')
        """
        lower_text = text.lower()

        # Check against known dataset names (sorted longest first)
        for name in self.known_names:
            name_clean = name.strip()
            if not name_clean or len(name_clean) < 2:
                continue

            # Match as whole word / phrase
            escaped = re.escape(name_clean.lower())
            if re.search(rf"\b{escaped}\b", lower_text):
                return name_clean

        # Syntactic pattern extraction if dataset check did not match
        patterns = [
            # "where does X live/stay"
            r"\b(?:where\s+(?:does|is|do))\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:live|stay)\b",
            # "where is X living/staying"
            r"\b(?:where\s+is)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:living|staying)\b",
            # "when is X's birthday"
            r"\b(?:when|what)\s+is\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)(?:'s)?\s+birthday\b",
            # "X's birthday"
            r"\b([A-Za-z]+(?:\s+[A-Za-z]+)?)(?:'s)\s+birthday\b",
            # "birthday of X"
            r"\bbirthday\s+of\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b",
            # "location of X"
            r"\b(?:location|place|address)\s+of\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b",
            # "find X"
            r"\b(?:find|search|lookup)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b"
        ]

        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()
                tokens = candidate.lower().split()
                # Ensure candidate doesn't consist of excluded tokens
                if not any(t in EXCLUDED_NAME_TOKENS for t in tokens) and len(candidate) > 1:
                    return candidate

        return None

    def classify_intent(self, text: str, entities: Dict[str, Any]) -> str:
        """Classify user intent based on grammar triggers and extracted entities."""
        lower = text.lower().strip()

        # 1. Count intent
        if re.search(r"\b(how\s+many|count|number\s+of|total\s+number)\b", lower):
            return "count_birthdays"

        # 2. Location / Place intent
        if re.search(r"\b(where\s+does|where\s+do|where\s+is|where\s+are)\b", lower) or \
           re.search(r"\b(location|place\s+of\s+stay|residence|lives?|stays?|living|staying)\b", lower):
            # Only if it refers to a person or place lookup
            if entities.get("person_name") or entities.get("person_id") or "live" in lower or "stay" in lower or "where" in lower:
                return "person_place"

        # 3. Tomorrow's birthdays intent
        if entities.get("relative_date") == "tomorrow" or re.search(r"\b(tomorrow|tmrw)\b", lower):
            return "tomorrow_birthdays"

        # 4. Upcoming birthdays intent
        if re.search(r"\b(upcoming|coming\s+up|approaching|next\s+\d+\s+days|next\s+few\s+days|soon)\b", lower):
            return "upcoming_birthdays"

        # 5. Person birthday intent
        if re.search(r"\b(when\s+is|what\s+date|when\s+was|born\s+on)\b", lower) and entities.get("person_name"):
            return "person_birthday"

        if entities.get("person_name") and not entities.get("month") and not entities.get("relationship"):
            # e.g. "Rahul Patil", "Rahul Patil birthday"
            if re.search(r"\b(birthday|bday|born)\b", lower) or len(lower.split()) <= 3:
                return "person_birthday"

        # 6. Birthday search intent
        if entities.get("month") or entities.get("relationship") or entities.get("relative_month") or \
           re.search(r"\b(birthday|birthdays|bday|bdays|born|celebrate|list|show)\b", lower):
            return "birthday_search"

        # 7. Fallback or greeting
        if re.search(r"\b(hi|hello|hey|greetings|help)\b", lower):
            return "unknown"

        return "unknown"

    def parse(self, message: str) -> Dict[str, Any]:
        """
        Parse raw user message into structured intent and entities.
        Returns a dictionary adhering to the system specification.
        """
        clean_text = message.strip()

        # Extract individual entities
        person_id = self.extract_person_id(clean_text)
        month = self.extract_month(clean_text)
        relationship = self.extract_relationship(clean_text)
        relative_date = self.extract_relative_date(clean_text)
        relative_month = self.extract_relative_month(clean_text)
        person_name = self.extract_person_name(clean_text)

        entities: Dict[str, Any] = {
            "person_name": person_name,
            "person_id": person_id,
            "month": month,
            "relationship": relationship,
            "relative_date": relative_date,
            "relative_month": relative_month
        }

        intent = self.classify_intent(clean_text, entities)

        return {
            "intent": intent,
            "entities": entities,
            "raw_message": clean_text
        }
