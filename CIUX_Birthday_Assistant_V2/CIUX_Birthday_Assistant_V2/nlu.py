"""
nlu.py - Rule-based Natural Language Understanding (NLU) Module.

Extracts user intent and key entities from birthday-related natural language queries.
Standardized output format:
{
    "intent": "<intent_name>",
    "entities": {
        "person_name": str | None,
        "person_id": str | None,
        "month": str | None,
        "relationship": str | None,
        "relative_date": str | None
    }
}
"""

import re
from typing import Dict, Any, Optional

# Supported months mapping (lowercase input -> Title Case month name)
MONTHS_MAP = {
    "january": "January", "jan": "January",
    "february": "February", "feb": "February",
    "march": "March", "mar": "March",
    "april": "April", "apr": "April",
    "may": "May",
    "june": "June", "jun": "June",
    "july": "July", "jul": "July",
    "august": "August", "aug": "August",
    "september": "September", "sep": "September", "sept": "September",
    "october": "October", "oct": "October",
    "november": "November", "nov": "November",
    "december": "December", "dec": "December",
}

# Supported relationships mapping (lowercase/plurals -> canonical singular form)
RELATIONSHIPS_MAP = {
    "nephew": "nephew", "nephews": "nephew",
    "niece": "niece", "nieces": "niece",
    "cousin": "cousin", "cousins": "cousin",
    "brother": "brother", "brothers": "brother",
    "sister": "sister", "sisters": "sister",
    "uncle": "uncle", "uncles": "uncle",
    "aunt": "aunt", "aunts": "aunt", "aunty": "aunt", "aunties": "aunt",
    "father": "father", "dad": "father", "appa": "father",
    "mother": "mother", "mom": "mother", "amma": "mother",
    "wife": "wife", "spouse": "wife",
    "friend": "friend", "friends": "friend",
    "student": "student", "students": "student",
    "colleague": "colleague", "colleagues": "colleague", "coworker": "colleague", "coworkers": "colleague",
    "neighbour": "neighbour", "neighbours": "neighbour", "neighbor": "neighbour", "neighbors": "neighbour",
    "sister-in-law": "sister-in-law", "sisters-in-law": "sister-in-law", "sister in law": "sister-in-law",
    "brother-in-law": "brother-in-law", "brothers-in-law": "brother-in-law", "brother in law": "brother-in-law",
}

# Stopwords to filter out when extracting person names
NAME_STOPWORDS = {
    "show", "find", "get", "tell", "me", "when", "is", "where", "does", "do",
    "live", "lives", "living", "stay", "stays", "staying", "place", "birthday",
    "birthdays", "born", "was", "the", "a", "an", "my", "our", "their", "his",
    "her", "who", "whom", "has", "have", "in", "on", "at", "for", "about",
    "what", "how", "many", "count", "person", "of", "and", "or"
}


def extract_person_id(text: str) -> Optional[str]:
    """Extract Person_ID such as P001, P04, p010."""
    match = re.search(r"\b[pP](\d{1,4})\b", text)
    if match:
        num = int(match.group(1))
        return f"P{num:03d}"
    return None


def extract_month(text: str) -> Optional[str]:
    """Extract and normalize month from text."""
    lowered = text.lower()
    for key, month_name in sorted(MONTHS_MAP.items(), key=lambda x: -len(x[0])):
        pattern = rf"\b{re.escape(key)}\b"
        if re.search(pattern, lowered):
            return month_name
    return None


def extract_relationship(text: str) -> Optional[str]:
    """Extract and normalize relationship from text."""
    lowered = text.lower()
    for key, canonical in sorted(RELATIONSHIPS_MAP.items(), key=lambda x: -len(x[0])):
        pattern = rf"\b{re.escape(key)}\b"
        if re.search(pattern, lowered):
            return canonical
    return None


def extract_relative_date(text: str) -> Optional[str]:
    """Extract relative date expressions."""
    lowered = text.lower()
    if re.search(r"\btomorrow\b", lowered):
        return "tomorrow"
    if re.search(r"\b(upcoming|coming up|next|soon|nearest)\b", lowered):
        return "upcoming"
    if re.search(r"\btoday\b", lowered):
        return "today"
    return None


def extract_person_name(text: str) -> Optional[str]:
    """
    Extract a person's name from query patterns.
    E.g.: 'Where does Rahul live?', 'When is Rahul Patil's birthday?',
          'Find Rahul's birthday', 'Birthday of Sneha'.
    """
    cleaned = text.strip()

    # Pattern 1: Where does <Name> live / stay?
    m = re.search(
        r"\bwhere\s+(?:does|is|do)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:live|stay|staying|reside)\b",
        cleaned,
        re.IGNORECASE,
    )
    if m:
        candidate = m.group(1).strip()
        if candidate.lower() not in NAME_STOPWORDS and candidate.lower() not in RELATIONSHIPS_MAP:
            return candidate.title()

    # Pattern 2: Place / location / city of <Name>
    m = re.search(
        r"\b(?:place(?:\s+of\s+stay)?|location|city|address)\s+of\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b",
        cleaned,
        re.IGNORECASE,
    )
    if m:
        candidate = m.group(1).strip()
        if candidate.lower() not in NAME_STOPWORDS and candidate.lower() not in RELATIONSHIPS_MAP:
            return candidate.title()

    # Pattern 3: When is <Name>'s birthday / When was <Name> born
    m = re.search(
        r"\b(?:when\s+is|when\s+was|find|get|show|check)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)(?:'s|’s|\s+is|\s+was)?\s+(?:birthday|bday|born)\b",
        cleaned,
        re.IGNORECASE,
    )
    if m:
        candidate = m.group(1).strip()
        if candidate.lower() not in NAME_STOPWORDS and candidate.lower() not in RELATIONSHIPS_MAP:
            return candidate.title()

    # Pattern 4: Birthday / DOB of <Name>
    m = re.search(
        r"\b(?:birthday|bday|dob)\s+of\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b",
        cleaned,
        re.IGNORECASE,
    )
    if m:
        candidate = m.group(1).strip()
        if candidate.lower() not in NAME_STOPWORDS and candidate.lower() not in RELATIONSHIPS_MAP:
            return candidate.title()

    # Pattern 5: <Name>'s birthday / <Name>'s location / <Name>'s place
    m = re.search(
        r"\b([A-Za-z]+(?:\s+[A-Za-z]+)?)(?:'s|’s)\s+(?:birthday|bday|place|location|city|stay)\b",
        cleaned,
        re.IGNORECASE,
    )
    if m:
        candidate = m.group(1).strip()
        if candidate.lower() not in NAME_STOPWORDS and candidate.lower() not in RELATIONSHIPS_MAP:
            return candidate.title()

    # Pattern 6: Tell me about <Name> / details of <Name> / info on <Name>
    m = re.search(
        r"\b(?:tell\s+me\s+about|details\s+of|info\s+(?:about|on)|search\s+for)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b",
        cleaned,
        re.IGNORECASE,
    )
    if m:
        candidate = m.group(1).strip()
        if candidate.lower() not in NAME_STOPWORDS and candidate.lower() not in RELATIONSHIPS_MAP and candidate.lower() not in MONTHS_MAP:
            return candidate.title()

    return None


def parse_query(text: str) -> Dict[str, Any]:
    """
    Parse a user query into intent and extracted entities.
    Returns:
    {
        "intent": str,
        "entities": {
            "person_name": Optional[str],
            "person_id": Optional[str],
            "month": Optional[str],
            "relationship": Optional[str],
            "relative_date": Optional[str]
        }
    }
    """
    if not text or not text.strip():
        return {
            "intent": "unknown",
            "entities": {
                "person_name": None,
                "person_id": None,
                "month": None,
                "relationship": None,
                "relative_date": None,
            },
        }

    cleaned = text.strip()
    lowered = cleaned.lower()

    # Extract all entities
    person_id = extract_person_id(cleaned)
    month = extract_month(cleaned)
    relationship = extract_relationship(cleaned)
    relative_date = extract_relative_date(cleaned)
    person_name = extract_person_name(cleaned)

    # If person_id matched, do not confuse it with person_name
    if person_id and person_name and person_id.lower() == person_name.lower():
        person_name = None

    # Determine intent using rule hierarchy
    intent = "unknown"

    # Rule 1: Count intent
    if re.search(r"\b(how many|count|number of|total)\b", lowered):
        intent = "count_birthdays"

    # Rule 2: Person place / location intent
    elif re.search(r"\b(where\s+(?:does|is|do)|place\s+of\s+stay|location|where\s+.*live|where\s+.*stay|address|city)\b", lowered):
        intent = "person_place"

    # Rule 3: Tomorrow's birthdays intent
    elif relative_date == "tomorrow" or re.search(r"\btomorrow\b", lowered):
        intent = "tomorrow_birthdays"
        relative_date = "tomorrow"

    # Rule 4: Upcoming birthdays intent
    elif relative_date == "upcoming" or re.search(r"\b(upcoming|coming up|nearest|soon)\b", lowered):
        intent = "upcoming_birthdays"
        relative_date = "upcoming"

    # Rule 5: Specific person birthday intent
    elif (person_name or person_id) and (
        re.search(r"\b(when|birthday|bday|born|find|dob)\b", lowered)
        or re.search(r"(?:'s|’s)\s+birthday", lowered)
    ):
        intent = "person_birthday"

    # Rule 6: Birthday search intent (by month, relationship, or general list)
    elif (
        month
        or relationship
        or re.search(r"\b(birthday|birthdays|born|who has|show|list)\b", lowered)
    ):
        intent = "birthday_search"

    # Fallback: if only person_name was provided (e.g., 'Rahul' or 'Find Rahul')
    elif person_name or person_id:
        intent = "person_birthday"

    return {
        "intent": intent,
        "entities": {
            "person_name": person_name,
            "person_id": person_id,
            "month": month,
            "relationship": relationship,
            "relative_date": relative_date,
        },
    }
