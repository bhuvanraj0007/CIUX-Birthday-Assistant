"""
Natural Language Understanding (NLU) Module for CIUX Birthday Assistant V4
Rule-based intent recognition and entity extraction.
"""

import calendar
import re
from typing import Any, Dict, List, Optional, Tuple

# Supported Intents
INTENTS = [
    "birthday_search",
    "count_birthdays",
    "upcoming_birthdays",
    "person_place",
    "person_birthday",
    "tomorrow_birthdays",
    "unknown",
]

# Supported Relationships and Variants
RELATIONSHIPS = {
    "nephew": ["nephew", "nephews"],
    "niece": ["niece", "nieces"],
    "friend": ["friend", "friends", "pal", "pals", "buddy", "buddies"],
    "brother": ["brother", "brothers", "bro"],
    "sister": ["sister", "sisters", "sis"],
    "uncle": ["uncle", "uncles"],
    "aunt": ["aunt", "aunts", "aunty", "aunties"],
    "cousin": ["cousin", "cousins"],
    "colleague": ["colleague", "colleagues", "coworker", "coworkers"],
    "student": ["student", "students"],
    "neighbour": ["neighbour", "neighbours", "neighbor", "neighbors"],
    "wife": ["wife", "wives", "spouse", "spouses"],
    "father": ["father", "fathers", "dad", "daddy"],
    "mother": ["mother", "mothers", "mom", "mommy"],
    "son": ["son", "sons"],
    "daughter": ["daughter", "daughters"],
    "sister-in-law": ["sister-in-law", "sisters-in-law", "sister in law"],
    "brother-in-law": ["brother-in-law", "brothers-in-law", "brother in law"],
}

# Month Mapping
MONTH_PATTERNS = {
    1: ["january", "jan"],
    2: ["february", "feb"],
    3: ["march", "mar"],
    4: ["april", "apr"],
    5: ["may"],
    6: ["june", "jun"],
    7: ["july", "jul"],
    8: ["august", "aug"],
    9: ["september", "sep", "sept"],
    10: ["october", "oct"],
    11: ["november", "nov"],
    12: ["december", "dec"],
}


class RuleBasedNLU:
    """Rule-based Intent Classifier and Entity Extractor."""

    def __init__(self, known_names: Optional[List[str]] = None):
        self.known_names = [n.strip() for n in known_names if n.strip()] if known_names else []
        # Sort known names longest first for greedy matching
        self.known_names.sort(key=len, reverse=True)

    def extract_person_id(self, text: str) -> Optional[str]:
        """Extract Person ID such as P001, P004, P102."""
        match = re.search(r"\b([pP]\d{3,4})\b", text)
        if match:
            return match.group(1).upper()
        return None

    def extract_month(self, text: str) -> Tuple[Optional[int], Optional[str]]:
        """Extract month number (1-12) and capitalized name."""
        text_lower = text.lower()
        for month_num, patterns in MONTH_PATTERNS.items():
            for pat in patterns:
                # Match as whole word
                if re.search(rf"\b{pat}\b", text_lower):
                    return month_num, calendar.month_name[month_num]
        return None, None

    def extract_relationship(self, text: str) -> Optional[str]:
        """Extract and normalize relationship entity."""
        text_lower = text.lower()
        for canonical, aliases in RELATIONSHIPS.items():
            for alias in aliases:
                if re.search(rf"\b{re.escape(alias)}\b", text_lower):
                    return canonical
        return None

    def extract_relative_date(self, text: str) -> Optional[str]:
        """Extract relative date keywords like tomorrow, today."""
        text_lower = text.lower()
        if re.search(r"\btomorrow('?s)?\b", text_lower):
            return "tomorrow"
        if re.search(r"\btoday('?s)?\b", text_lower):
            return "today"
        return None

    def extract_relative_month(self, text: str) -> Optional[str]:
        """Extract relative month keywords like next month, this month."""
        text_lower = text.lower()
        if re.search(r"\bnext\s+month\b", text_lower):
            return "next_month"
        if re.search(r"\bthis\s+month\b", text_lower):
            return "this_month"
        return None

    def extract_person_name(self, text: str) -> Optional[str]:
        """Extract person's name using known dataset names and regex patterns."""
        # 1. Match against known names from dataset (greedy match)
        if self.known_names:
            text_lower = text.lower()
            for name in self.known_names:
                # Match full name
                if re.search(rf"\b{re.escape(name.lower())}\b", text_lower):
                    return name
                # Match first name if at least 3 letters
                parts = name.split()
                if parts and len(parts[0]) >= 3:
                    first_name = parts[0]
                    if re.search(rf"\b{re.escape(first_name.lower())}('?s)?\b", text_lower):
                        # Make sure first name is not a keyword like 'show', 'count', 'next'
                        if first_name.lower() not in ["show", "next", "this", "what", "where", "when", "does", "have"]:
                            return first_name

        # 2. Pattern: "Where does <name> live / stay?"
        match = re.search(
            r"\bwhere\s+(?:does|is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:live|stay|located|reside)",
            text,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()

        # 3. Pattern: "When is <name>'s birthday / DOB?"
        match = re.search(
            r"\bwhen\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:'s)?\s+(?:birthday|dob|date of birth)",
            text,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()

        # 4. Pattern: "<name>'s birthday / location / place"
        match = re.search(
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:'s)\s+(?:birthday|dob|location|place|home|house)",
            text,
            re.IGNORECASE,
        )
        if match:
            cand = match.group(1).strip()
            if cand.lower() not in ["tomorrow", "today", "yesterday", "anyone", "everyone", "somebody"]:
                return cand

        # 5. Pattern: "Where is <name>?"
        match = re.search(r"\bwhere\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", text, re.IGNORECASE)
        if match:
            cand = match.group(1).strip()
            if cand.lower() not in ["he", "she", "it", "my", "your", "everyone", "located", "staying"]:
                return cand

        # 6. Pattern: "Birthday of <name>"
        match = re.search(
            r"\b(?:birthday|dob|location|place)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
            text,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()

        # 7. Pattern: "Find <name>"
        match = re.search(r"\b(?:find|search|lookup)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", text, re.IGNORECASE)
        if match:
            cand = match.group(1).strip()
            if cand.lower() not in ["birthday", "birthdays", "someone", "person", "nephew", "niece", "friend"]:
                return cand

        return None

    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse user query text and return structured intent and entities.
        """
        cleaned = text.strip()
        cleaned_lower = cleaned.lower()

        # Extract all potential entities
        pid = self.extract_person_id(cleaned)
        month_num, month_name = self.extract_month(cleaned)
        relationship = self.extract_relationship(cleaned)
        rel_date = self.extract_relative_date(cleaned)
        rel_month = self.extract_relative_month(cleaned)
        person_name = self.extract_person_name(cleaned)

        # Do not allow person_name to shadow relationship if name happens to be identical
        if person_name and relationship and person_name.lower() == relationship.lower():
            person_name = None

        intent = "unknown"

        # 1. Count intent check ("how many", "count", "total number of")
        if re.search(r"\b(how\s+many|count|total\s+number|number\s+of)\b", cleaned_lower):
            intent = "count_birthdays"

        # 2. Tomorrow's birthdays check
        elif rel_date == "tomorrow" or "tomorrow" in cleaned_lower:
            intent = "tomorrow_birthdays"

        # 3. Upcoming birthdays check
        elif (
            re.search(r"\b(upcoming|coming\s+up|soon|next\s+\d+\s+days|next\s+birthdays)\b", cleaned_lower)
            and not rel_month
            and not month_num
        ):
            intent = "upcoming_birthdays"

        # 4. Location check ("where does", "where is", "place of stay", "location", "live", "reside")
        elif (
            re.search(r"\b(where\s+does|where\s+is|location|place\s+of\s+stay|reside|live|staying|city)\b", cleaned_lower)
            and not re.search(r"\bbirthday\b", cleaned_lower)
        ):
            intent = "person_place"

        # 5. Person-specific birthday check
        elif (
            (person_name or pid)
            and not relationship
            and not month_num
            and not rel_month
            and re.search(r"\b(birthday|dob|born|when|date of birth)\b", cleaned_lower)
        ):
            intent = "person_birthday"

        # 6. Person name directly queried ("Rahul Patil", "Lakshmi Rao")
        elif (person_name or pid) and not month_num and not relationship and not rel_month and not rel_date:
            # If query is just a person's name or ID, default to person_birthday
            intent = "person_birthday"

        # 7. General birthday search (by month, by relationship, next month, this month, etc.)
        elif (
            month_num
            or rel_month
            or relationship
            or re.search(r"\b(birthday|birthdays|born|dob|celebrat(?:e|ing))\b", cleaned_lower)
            or re.search(r"\b(what\s+about|and|how\s+about)\b", cleaned_lower)
        ):
            intent = "birthday_search"

        # 8. Upcoming fallback if "upcoming" appeared anywhere
        elif "upcoming" in cleaned_lower:
            intent = "upcoming_birthdays"

        # Fallback intent if unknown but month or relationship present
        if intent == "unknown" and (month_num or relationship or rel_month):
            intent = "birthday_search"

        return {
            "intent": intent,
            "entities": {
                "person_name": person_name,
                "person_id": pid,
                "month": month_name if month_name else month_num,
                "relationship": relationship,
                "relative_date": rel_date,
                "relative_month": rel_month,
            },
            "raw_text": cleaned,
            "engine": "rule_based",
        }
