"""
service.py - Business Logic and Birthday Service.

Loads and cleans the Excel dataset (data/people.xlsx), handles queries,
computes upcoming/tomorrow birthdays, counts, and filters.
The Excel dataset is the ONLY source of truth. No records are ever invented.
"""

from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
from config import EXCEL_PATH, DEFAULT_UPCOMING_DAYS


MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

MONTH_NAME_TO_INT = {name.lower(): idx for idx, name in enumerate(MONTH_NAMES) if name}


class BirthdayService:
    """Service to load, clean, and query the birthday dataset."""

    def __init__(self, excel_path=EXCEL_PATH):
        self.excel_path = excel_path
        self.df: pd.DataFrame = pd.DataFrame()
        self.load_dataset()

    def load_dataset(self) -> None:
        """
        Load Excel dataset using Pandas and clean data:
        - Handle missing values
        - Parse DOB safely with errors='coerce'
        - Filter out invalid DOB rows
        - Strip whitespace from string columns
        - Deduplicate records by Person_ID
        """
        try:
            raw_df = pd.read_excel(self.excel_path)
        except Exception as e:
            print(f"[ERROR] Failed to load dataset from {self.excel_path}: {e}")
            self.df = pd.DataFrame(columns=[
                "Person_ID", "Name", "Nickname", "DOB",
                "Place_of_Stay", "Relationship", "Relationship_Group",
                "Relationship_Detail", "Notes", "Birth_Month", "Birth_Day", "DOB_Date"
            ])
            return

        # Ensure required columns exist
        required_cols = ["Person_ID", "Name", "DOB", "Relationship", "Place_of_Stay"]
        for col in required_cols:
            if col not in raw_df.columns:
                raw_df[col] = ""

        # Drop exact duplicate rows or duplicate Person_IDs
        df = raw_df.drop_duplicates(subset=["Person_ID"]).copy()

        # Clean string columns
        str_cols = ["Person_ID", "Name", "Relationship", "Place_of_Stay"]
        if "Nickname" in df.columns:
            str_cols.append("Nickname")
        for col in str_cols:
            df[col] = df[col].fillna("").astype(str).str.strip()

        # Parse DOB into datetime
        df["DOB_Parsed"] = pd.to_datetime(df["DOB"], errors="coerce")
        # Keep only records with valid DOB and non-empty Name
        df = df[df["DOB_Parsed"].notna() & (df["Name"] != "")].copy()

        # Extract month and day for fast birthday matching
        df["Birth_Month"] = df["DOB_Parsed"].dt.month
        df["Birth_Day"] = df["DOB_Parsed"].dt.day
        df["DOB_Date"] = df["DOB_Parsed"].dt.date
        df["DOB_Formatted"] = df["DOB_Parsed"].dt.strftime("%Y-%m-%d")

        self.df = df.reset_index(drop=True)
        print(f"[INFO] Loaded {len(self.df)} valid records from {self.excel_path.name}")

    def get_all_records(self) -> List[Dict[str, Any]]:
        """Return all cleaned records as list of dicts."""
        return self.df.to_dict(orient="records")

    def find_person(self, name: Optional[str] = None, person_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for person by Person_ID or case-insensitive Name / Nickname match.
        """
        if self.df.empty:
            return []

        if person_id:
            pid = person_id.strip().upper()
            matched = self.df[self.df["Person_ID"].str.upper() == pid]
            if not matched.empty:
                return matched.to_dict(orient="records")

        if name:
            q = name.strip().lower()
            # Match in full Name or Nickname
            mask = (
                self.df["Name"].str.lower().str.contains(q, regex=False)
            )
            if "Nickname" in self.df.columns:
                mask = mask | (self.df["Nickname"].str.lower() == q)
            matched = self.df[mask]
            return matched.to_dict(orient="records")

        return []

    def get_person_birthday(self, name: Optional[str] = None, person_id: Optional[str] = None) -> str:
        """Find person's birthday from Excel."""
        matches = self.find_person(name=name, person_id=person_id)
        if not matches:
            target = person_id if person_id else (name if name else "that person")
            return f"No records found for '{target}' in the dataset."

        lines = []
        for p in matches:
            dob_str = p.get("DOB_Formatted", str(p.get("DOB", "")))
            b_month = MONTH_NAMES[p["Birth_Month"]] if p.get("Birth_Month") else ""
            b_day = p.get("Birth_Day", "")
            lines.append(
                f"🎂 **{p['Name']}** ({p['Person_ID']})\n"
                f"- **Relationship:** {p.get('Relationship', 'N/A')}\n"
                f"- **Date of Birth:** {dob_str} ({b_month} {b_day})\n"
                f"- **Place of Stay:** {p.get('Place_of_Stay', 'N/A')}"
            )
        return "\n\n".join(lines)

    def get_person_location(self, name: Optional[str] = None, person_id: Optional[str] = None) -> str:
        """Find person's place of stay / location from Excel."""
        matches = self.find_person(name=name, person_id=person_id)
        if not matches:
            target = person_id if person_id else (name if name else "that person")
            return f"No records found for '{target}' in the dataset."

        lines = []
        for p in matches:
            place = p.get("Place_of_Stay", "").strip() or "Not specified"
            lines.append(
                f"📍 **{p['Name']}** ({p['Person_ID']}) lives in **{place}**.\n"
                f"- **Relationship:** {p.get('Relationship', 'N/A')}\n"
                f"- **DOB:** {p.get('DOB_Formatted', 'N/A')}"
            )
        return "\n\n".join(lines)

    def search_birthdays(
        self,
        month: Optional[str] = None,
        relationship: Optional[str] = None,
        name: Optional[str] = None,
        person_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search birthdays filtered by Month, Relationship, Name, or Person_ID.
        Supports combined filtering.
        """
        if self.df.empty:
            return []

        filtered = self.df.copy()

        # Filter by Person_ID
        if person_id:
            filtered = filtered[filtered["Person_ID"].str.upper() == person_id.strip().upper()]

        # Filter by Name
        if name:
            q = name.strip().lower()
            mask = filtered["Name"].str.lower().str.contains(q, regex=False)
            if "Nickname" in filtered.columns:
                mask = mask | (filtered["Nickname"].str.lower() == q)
            filtered = filtered[mask]

        # Filter by Month
        if month:
            m_idx = MONTH_NAME_TO_INT.get(month.lower())
            if m_idx:
                filtered = filtered[filtered["Birth_Month"] == m_idx]

        # Filter by Relationship
        if relationship:
            r_lower = relationship.strip().lower()
            filtered = filtered[filtered["Relationship"].str.lower().str.contains(r_lower, regex=False)]

        return filtered.to_dict(orient="records")

    def count_birthdays(
        self,
        month: Optional[str] = None,
        relationship: Optional[str] = None,
    ) -> int:
        """Count birthdays matching month and/or relationship."""
        results = self.search_birthdays(month=month, relationship=relationship)
        return len(results)

    def get_upcoming_birthdays(
        self,
        days: int = DEFAULT_UPCOMING_DAYS,
        reference_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculate next birthdays within the given number of days from reference_date.
        If this year's birthday has passed, next year's is used.
        Sorted by nearest upcoming birthday.
        """
        if self.df.empty:
            return []

        ref = reference_date or date.today()
        upcoming_list = []

        for _, row in self.df.iterrows():
            b_month = int(row["Birth_Month"])
            b_day = int(row["Birth_Day"])

            # Handle leap day (Feb 29) on non-leap years
            try:
                candidate = date(ref.year, b_month, b_day)
            except ValueError:
                candidate = date(ref.year, 2, 28)

            if candidate < ref:
                # Birthday has passed this year, calculate for next year
                try:
                    candidate = date(ref.year + 1, b_month, b_day)
                except ValueError:
                    candidate = date(ref.year + 1, 2, 28)

            days_until = (candidate - ref).days
            if 0 <= days_until <= days:
                record = row.to_dict()
                record["Next_Birthday"] = candidate
                record["Days_Until"] = days_until
                upcoming_list.append(record)

        # Sort by nearest upcoming birthday
        upcoming_list.sort(key=lambda x: (x["Days_Until"], x["Next_Birthday"]))
        return upcoming_list

    def get_tomorrow_birthdays(
        self,
        reference_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Find people whose birthday falls exactly tomorrow."""
        ref = reference_date or date.today()
        tomorrow = ref + timedelta(days=1)

        if self.df.empty:
            return []

        matches = []
        for _, row in self.df.iterrows():
            b_month = int(row["Birth_Month"])
            b_day = int(row["Birth_Day"])
            if b_month == tomorrow.month and b_day == tomorrow.day:
                record = row.to_dict()
                record["Next_Birthday"] = tomorrow
                record["Days_Until"] = 1
                matches.append(record)

        return matches

    def process_nlu_query(self, nlu_result: Dict[str, Any], reference_date: Optional[date] = None) -> str:
        """
        Route parsed NLU output to appropriate service function and return
        a friendly, accurate natural language response.
        """
        intent = nlu_result.get("intent", "unknown")
        entities = nlu_result.get("entities", {})

        person_name = entities.get("person_name")
        person_id = entities.get("person_id")
        month = entities.get("month")
        relationship = entities.get("relationship")

        # 1. Person Location
        if intent == "person_place":
            return self.get_person_location(name=person_name, person_id=person_id)

        # 2. Specific Person Birthday
        if intent == "person_birthday":
            return self.get_person_birthday(name=person_name, person_id=person_id)

        # 3. Tomorrow's Birthdays
        if intent == "tomorrow_birthdays":
            results = self.get_tomorrow_birthdays(reference_date=reference_date)
            if not results:
                ref = reference_date or date.today()
                tomorrow_str = (ref + timedelta(days=1)).strftime("%B %d")
                return f"No birthdays tomorrow ({tomorrow_str}) in the dataset."
            lines = [f"🎉 **Birthdays Tomorrow ({len(results)} found):**"]
            for r in results:
                lines.append(
                    f"- **{r['Name']}** ({r['Person_ID']}) | {r.get('Relationship', 'N/A')} | "
                    f"DOB: {r['DOB_Formatted']} | Lives in: {r.get('Place_of_Stay', 'N/A')}"
                )
            return "\n".join(lines)

        # 4. Upcoming Birthdays
        if intent == "upcoming_birthdays":
            results = self.get_upcoming_birthdays(days=DEFAULT_UPCOMING_DAYS, reference_date=reference_date)
            if not results:
                return f"No birthdays found in the next {DEFAULT_UPCOMING_DAYS} days."
            lines = [f"📅 **Upcoming Birthdays (Next {DEFAULT_UPCOMING_DAYS} days - {len(results)} found):**"]
            for r in results:
                day_word = "day" if r["Days_Until"] == 1 else "days"
                timing = "Today!" if r["Days_Until"] == 0 else (
                    "Tomorrow" if r["Days_Until"] == 1 else f"in {r['Days_Until']} {day_word}"
                )
                b_date = r["Next_Birthday"].strftime("%B %d")
                lines.append(
                    f"- **{r['Name']}** ({r['Person_ID']}) — **{b_date}** ({timing})\n"
                    f"  Relationship: {r.get('Relationship', 'N/A')} | Born: {r['DOB_Formatted']} | Location: {r.get('Place_of_Stay', 'N/A')}"
                )
            return "\n".join(lines)

        # 5. Count Birthdays
        if intent == "count_birthdays":
            count = self.count_birthdays(month=month, relationship=relationship)
            filter_desc = []
            if relationship:
                filter_desc.append(f"relationship '{relationship}'")
            if month:
                filter_desc.append(f"in {month}")
            scope = f" with {' and '.join(filter_desc)}" if filter_desc else ""
            return f"📊 Total birthdays found{scope}: **{count}**."

        # 6. Birthday Search (by month / relationship / combined)
        if intent == "birthday_search":
            results = self.search_birthdays(month=month, relationship=relationship, name=person_name, person_id=person_id)
            if not results:
                filters = []
                if relationship:
                    filters.append(f"relationship '{relationship}'")
                if month:
                    filters.append(f"in {month}")
                desc = " with " + " and ".join(filters) if filters else ""
                return f"No birthdays found{desc} in the dataset."

            header_parts = []
            if relationship:
                header_parts.append(relationship.capitalize())
            if month:
                header_parts.append(f"in {month}")
            title = f"{' '.join(header_parts)} Birthdays" if header_parts else "Birthday Records"

            lines = [f"🎂 **{title} ({len(results)} found):**"]
            for r in results:
                lines.append(
                    f"- **{r['Name']}** ({r['Person_ID']}) — DOB: **{r['DOB_Formatted']}** | "
                    f"Relationship: {r.get('Relationship', 'N/A')} | Place: {r.get('Place_of_Stay', 'N/A')}"
                )
            return "\n".join(lines)

        # 7. Fallback for Unknown
        return (
            "I'm your **CIUX Birthday Assistant V2**! 🎂\n\n"
            "You can ask me questions like:\n"
            "- *Show birthdays in September.*\n"
            "- *How many nephews have birthdays in October?*\n"
            "- *When is Rahul's birthday?*\n"
            "- *Where does Rahul live?*\n"
            "- *Show upcoming birthdays.*\n"
            "- *Who has a birthday tomorrow?*"
        )
