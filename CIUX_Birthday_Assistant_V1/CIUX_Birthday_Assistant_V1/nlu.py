import calendar
import re

MONTHS = {
    m.lower(): i
    for i, m in enumerate(calendar.month_name)
    if m
}


def parse(message, people):
    text = message.lower().strip()

    result = {
        "intent": "unknown",
        "entities": {}
    }

    # Intent classification
    if "how many" in text or "count" in text:
        result["intent"] = "count_birthdays"

    elif "where" in text or "stay" in text or "live" in text:
        result["intent"] = "person_place"

    elif "upcoming" in text:
        result["intent"] = "upcoming_birthdays"

    else:
        result["intent"] = "birthday_search"

    # Extract relative date
    if "tomorrow" in text:
        result["entities"]["relative_date"] = "tomorrow"

    if "next month" in text:
        result["entities"]["relative_month"] = "next"

    # Extract month
    for name, number in MONTHS.items():
        if name in text:
            result["entities"]["month"] = number

    # Extract relationship
    for rel in sorted(
        people["Relationship"].dropna().unique(),
        key=len,
        reverse=True
    ):
        token = rel.lower()

        if token in text or token + "s" in text:
            result["entities"]["relationship"] = rel
            break

    # Extract person name
    for _, row in people.iterrows():

        candidates = [
            str(row["Name"]),
            str(row.get("Nickname", ""))
        ]

        for candidate in candidates:

            candidate = candidate.lower().strip()

            if candidate and candidate != "nan":

                if re.search(
                    r"\b" + re.escape(candidate) + r"\b",
                    text
                ):
                    result["entities"]["person_id"] = row["Person_ID"]
                    result["entities"]["person_name"] = row["Name"]
                    break

        if "person_id" in result["entities"]:
            break

    return result