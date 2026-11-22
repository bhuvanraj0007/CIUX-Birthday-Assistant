from datetime import date, timedelta


def format_rows(rows):

    if rows.empty:
        return "No matching people found."

    return "\n".join(
        f"{r.Name} - {r.DOB.strftime('%d %B')} ({r.Relationship})"
        for _, r in rows.iterrows()
    )


def execute(parsed, df):

    intent = parsed["intent"]
    entities = parsed["entities"]

    work = df.copy()
    today = date.today()

    # Search by person
    if "person_id" in entities:

        row = df[
            df.Person_ID == entities["person_id"]
        ].iloc[0]

        if intent == "person_place":
            return f"{row.Name} stays in {row.Place_of_Stay}."

        return (
            f"{row.Name}'s birthday is "
            f"{row.DOB.strftime('%d %B %Y')}."
        )

    # Filter by relationship
    if "relationship" in entities:

        work = work[
            work.Relationship.str.lower()
            == entities["relationship"].lower()
        ]

    # Filter tomorrow's birthdays
    if entities.get("relative_date") == "tomorrow":

        tomorrow = today + timedelta(days=1)

        work = work[
            (work.DOB.dt.month == tomorrow.month)
            & (work.DOB.dt.day == tomorrow.day)
        ]

    # Filter by month
    month = entities.get("month")

    if entities.get("relative_month") == "next":

        month = 1 if today.month == 12 else today.month + 1

    if month:

        work = work[
            work.DOB.dt.month == month
        ]

    # Count birthdays
    if intent == "count_birthdays":

        return f"I found {len(work)} matching birthdays."

    # Upcoming birthdays
    if intent == "upcoming_birthdays":

        def days_until(row):

            birthday = date(
                today.year,
                row.DOB.month,
                row.DOB.day
            )

            if birthday < today:

                birthday = date(
                    today.year + 1,
                    row.DOB.month,
                    row.DOB.day
                )

            return (birthday - today).days

        work = work.assign(
            _days=work.apply(days_until, axis=1)
        )

        work = work[
            (work._days >= 0)
            & (work._days <= 30)
        ].sort_values("_days")

    return format_rows(work)