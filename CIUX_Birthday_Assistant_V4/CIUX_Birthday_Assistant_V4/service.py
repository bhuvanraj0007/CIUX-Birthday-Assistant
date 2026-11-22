"""
Data Service Module for CIUX Birthday Assistant V4
Responsible for loading, validating, querying, and formatting Excel birthday data.
Strict rule: Dataset is the ONLY source of factual information. Never invent data.
"""

import calendar
import logging
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

from config import DATASET_PATH, DEFAULT_UPCOMING_DAYS

logger = logging.getLogger(__name__)

# Column name alias mapping for robust dataset loading
COLUMN_ALIASES = {
    "person_id": ["person_id", "id", "personid", "pid", "code", "emp_id"],
    "name": ["name", "full_name", "fullname", "person_name", "first_name"],
    "nickname": ["nickname", "nick_name", "alias", "pet_name"],
    "dob": ["dob", "dateofbirth", "date_of_birth", "birthdate", "birth_date", "birth_day"],
    "place_of_stay": ["place_of_stay", "place", "location", "city", "address", "town", "residence"],
    "relationship": ["relationship", "relation", "relation_type", "relationship_type"],
    "relationship_group": ["relationship_group", "rel_group", "group"],
    "relationship_detail": ["relationship_detail", "detail", "sub_relation"],
    "notes": ["notes", "note", "remarks", "comment"],
}

# Month names mapping
MONTH_NAME_TO_INT = {
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
    "december": 12, "dec": 12,
}

# Relationship normalizations (plural to singular, synonyms)
RELATIONSHIP_SYNONYMS = {
    "nephews": "nephew",
    "nieces": "niece",
    "friends": "friend",
    "brothers": "brother",
    "sisters": "sister",
    "uncles": "uncle",
    "aunts": "aunt",
    "cousins": "cousin",
    "colleagues": "colleague",
    "students": "student",
    "neighbours": "neighbour",
    "neighbors": "neighbour",
    "neighbour": "neighbour",
    "wives": "wife",
    "spouse": "wife",  # In the dataset, wife is the primary spouse relationship
    "spouses": "wife",
    "fathers": "father",
    "mothers": "mother",
    "parents": ["father", "mother"],
    "sister-in-laws": "sister-in-law",
    "sisters-in-law": "sister-in-law",
    "brother-in-laws": "brother-in-law",
    "brothers-in-law": "brother-in-law",
}


class BirthdayService:
    """Service to load, clean, query and format birthday data from Excel."""

    def __init__(self, dataset_path: Optional[Union[str, Path]] = None):
        self.dataset_path = Path(dataset_path) if dataset_path else DATASET_PATH
        self.df: pd.DataFrame = pd.DataFrame()
        self.canonical_columns: Dict[str, str] = {}
        self.load_dataset()

    def _normalize_column_name(self, col: str) -> str:
        """Strip and normalize column names for fuzzy mapping."""
        return re.sub(r"[_\s\-]+", "_", str(col).strip().lower())

    def load_dataset(self, path: Optional[Union[str, Path]] = None) -> bool:
        """Load and clean the Excel dataset."""
        if path:
            self.dataset_path = Path(path)

        if not self.dataset_path.exists():
            logger.warning(f"Dataset file not found at {self.dataset_path}")
            self.df = pd.DataFrame(columns=["person_id", "name", "dob", "relationship", "place_of_stay"])
            return False

        try:
            raw_df = pd.read_excel(self.dataset_path, engine="openpyxl")
        except Exception as e:
            logger.error(f"Error reading Excel dataset: {e}")
            self.df = pd.DataFrame(columns=["person_id", "name", "dob", "relationship", "place_of_stay"])
            return False

        if raw_df.empty:
            self.df = pd.DataFrame(columns=["person_id", "name", "dob", "relationship", "place_of_stay"])
            return True

        # Detect columns dynamically
        col_mapping = {}
        normalized_raw = {self._normalize_column_name(c): c for c in raw_df.columns}

        for canonical, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                norm_alias = self._normalize_column_name(alias)
                if norm_alias in normalized_raw:
                    col_mapping[normalized_raw[norm_alias]] = canonical
                    break

        # Rename mapped columns
        df = raw_df.rename(columns=col_mapping).copy()

        # Ensure essential columns exist
        for essential in ["person_id", "name", "dob", "relationship", "place_of_stay"]:
            if essential not in df.columns:
                df[essential] = None

        # Clean string columns
        for str_col in ["person_id", "name", "relationship", "place_of_stay"]:
            if str_col in df.columns:
                df[str_col] = df[str_col].fillna("").astype(str).str.strip()

        # Drop rows where both name and person_id are missing/empty
        df = df[(df["name"] != "") | (df["person_id"] != "")].copy()

        # Deduplicate based on person_id if available, otherwise name and dob
        if "person_id" in df.columns and df["person_id"].ne("").any():
            df = df.drop_duplicates(subset=["person_id"], keep="first")
        else:
            df = df.drop_duplicates(subset=["name", "dob"], keep="first")

        # Parse DOB into datetime
        df["dob_parsed"] = pd.to_datetime(df["dob"], errors="coerce")

        # Extract month and day safely
        df["birth_month"] = df["dob_parsed"].dt.month
        df["birth_day"] = df["dob_parsed"].dt.day
        df["birth_year"] = df["dob_parsed"].dt.year

        self.df = df.reset_index(drop=True)
        logger.info(f"Loaded {len(self.df)} valid records from {self.dataset_path}")
        return True

    def get_all_people(self) -> List[Dict[str, Any]]:
        """Return all cleaned records as list of dicts."""
        return self._records_to_list(self.df)

    def _records_to_list(self, df_subset: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert a subset DataFrame to a serializable dictionary format."""
        records = []
        for _, row in df_subset.iterrows():
            dob_dt = row.get("dob_parsed")
            formatted_dob = ""
            iso_dob = ""
            if pd.notna(dob_dt):
                formatted_dob = dob_dt.strftime("%d %B %Y")
                iso_dob = dob_dt.strftime("%Y-%m-%d")
            elif row.get("dob"):
                formatted_dob = str(row.get("dob"))
                iso_dob = formatted_dob

            records.append({
                "person_id": str(row.get("person_id", "")),
                "name": str(row.get("name", "")),
                "nickname": str(row.get("nickname", "")) if pd.notna(row.get("nickname")) else "",
                "dob": iso_dob,
                "formatted_dob": formatted_dob,
                "relationship": str(row.get("relationship", "")),
                "place_of_stay": str(row.get("place_of_stay", "")),
                "birth_month": int(row["birth_month"]) if pd.notna(row.get("birth_month")) else None,
                "birth_day": int(row["birth_day"]) if pd.notna(row.get("birth_day")) else None,
                "birth_year": int(row["birth_year"]) if pd.notna(row.get("birth_year")) else None,
            })
        return records

    @staticmethod
    def parse_month(month_input: Any) -> Optional[int]:
        """Convert month string or number to integer 1-12."""
        if month_input is None:
            return None
        if isinstance(month_input, int) and 1 <= month_input <= 12:
            return month_input
        s = str(month_input).strip().lower()
        if s.isdigit():
            val = int(s)
            return val if 1 <= val <= 12 else None
        return MONTH_NAME_TO_INT.get(s)

    @staticmethod
    def normalize_relationship(rel_input: Any) -> Union[str, List[str]]:
        """Normalize relationship string, handling plurals and synonyms."""
        if not rel_input:
            return ""
        cleaned = str(rel_input).strip().lower()
        # Direct dictionary synonym lookup
        if cleaned in RELATIONSHIP_SYNONYMS:
            return RELATIONSHIP_SYNONYMS[cleaned]
        # Basic plural stripping
        if cleaned.endswith("s") and cleaned[:-1] in [
            "nephew", "niece", "friend", "brother", "sister", "uncle", "aunt", "cousin", "student", "colleague"
        ]:
            return cleaned[:-1]
        return cleaned

    def search_by_person_id(self, person_id: str) -> List[Dict[str, Any]]:
        """Search by exact or case-insensitive Person ID."""
        if not person_id or self.df.empty:
            return []
        pid_clean = person_id.strip().lower()
        matches = self.df[self.df["person_id"].str.lower() == pid_clean]
        return self._records_to_list(matches)

    def search_by_person_name(self, name: str) -> List[Dict[str, Any]]:
        """Search by person name or nickname (case-insensitive substring/token match)."""
        if not name or self.df.empty:
            return []
        name_clean = name.strip().lower()

        # 1. Exact match on full name
        exact = self.df[self.df["name"].str.lower() == name_clean]
        if not exact.empty:
            return self._records_to_list(exact)

        # 2. Match on nickname if column exists
        if "nickname" in self.df.columns:
            nick_exact = self.df[self.df["nickname"].str.lower() == name_clean]
            if not nick_exact.empty:
                return self._records_to_list(nick_exact)

        # 3. Substring match on name
        sub = self.df[self.df["name"].str.lower().str.contains(re.escape(name_clean), na=False)]
        if not sub.empty:
            return self._records_to_list(sub)

        # 4. Token-level matching (e.g., 'Rahul' matches 'Rahul Patil')
        tokens = [t for t in name_clean.split() if len(t) > 2]
        if tokens:
            pattern = "|".join([re.escape(t) for t in tokens])
            token_matches = self.df[self.df["name"].str.lower().str.contains(pattern, na=False)]
            return self._records_to_list(token_matches)

        return []

    def filter_by_month(self, month: Union[int, str], records: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Filter records by birth month (1-12)."""
        month_int = self.parse_month(month)
        if not month_int:
            return []

        if records is not None:
            return [r for r in records if r.get("birth_month") == month_int]

        if self.df.empty:
            return []

        matched = self.df[self.df["birth_month"] == month_int]
        # Sort by birth day
        matched = matched.sort_values(by="birth_day")
        return self._records_to_list(matched)

    def filter_by_relationship(self, relationship: str, records: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Filter records by relationship (case-insensitive, handling synonyms)."""
        if not relationship:
            return records if records is not None else self._records_to_list(self.df)

        norm = self.normalize_relationship(relationship)
        targets = norm if isinstance(norm, list) else [norm]

        def matches_rel(rel_str: str) -> bool:
            rel_lower = str(rel_str).strip().lower()
            return any(t in rel_lower for t in targets)

        if records is not None:
            return [r for r in records if matches_rel(r.get("relationship", ""))]

        if self.df.empty:
            return []

        mask = self.df["relationship"].apply(matches_rel)
        matched = self.df[mask]
        return self._records_to_list(matched)

    def search_birthdays(
        self,
        month: Optional[Union[int, str]] = None,
        relationship: Optional[str] = None,
        person_name: Optional[str] = None,
        person_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Combined search across all filters."""
        if self.df.empty:
            return []

        # If person_id provided, look up by ID
        if person_id:
            return self.search_by_person_id(person_id)

        # If person_name provided, look up by name
        if person_name:
            results = self.search_by_person_name(person_name)
            if relationship:
                results = self.filter_by_relationship(relationship, records=results)
            if month:
                results = self.filter_by_month(month, records=results)
            return results

        # Start with full dataset
        subset = self.df.copy()

        # Filter by relationship
        if relationship:
            norm = self.normalize_relationship(relationship)
            targets = norm if isinstance(norm, list) else [norm]
            mask = subset["relationship"].apply(lambda r: any(t in str(r).lower() for t in targets))
            subset = subset[mask]

        # Filter by month
        if month:
            month_int = self.parse_month(month)
            if month_int:
                subset = subset[subset["birth_month"] == month_int]

        # Sort by birth day
        if not subset.empty and "birth_day" in subset.columns:
            subset = subset.sort_values(by="birth_day")

        return self._records_to_list(subset)

    def count_birthdays(
        self,
        month: Optional[Union[int, str]] = None,
        relationship: Optional[str] = None,
        person_name: Optional[str] = None,
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Count birthdays matching the specified criteria."""
        records = self.search_birthdays(month=month, relationship=relationship, person_name=person_name)
        return len(records), records

    def get_upcoming_birthdays(
        self,
        days: int = DEFAULT_UPCOMING_DAYS,
        reference_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculate birthdays occurring within the next N days from reference_date.
        Handles:
        - Passed birthdays this calendar year (rolls over to next year)
        - Leap year births (February 29 mapped to February 28 in non-leap years)
        - Year transition / rollover
        - Sorted ascending by days remaining
        """
        if self.df.empty:
            return []

        ref = reference_date if reference_date else date.today()
        upcoming_list = []

        for _, row in self.df.iterrows():
            dob_dt = row.get("dob_parsed")
            if pd.isna(dob_dt):
                continue

            b_month = int(row["birth_month"])
            b_day = int(row["birth_day"])
            b_year = int(row["birth_year"])

            # Compute birthday in current reference year
            try:
                candidate = date(ref.year, b_month, b_day)
            except ValueError:
                # Handle Feb 29 on non-leap year
                candidate = date(ref.year, 2, 28)

            # If birthday has already passed this year, roll over to next year
            if candidate < ref:
                try:
                    candidate = date(ref.year + 1, b_month, b_day)
                except ValueError:
                    candidate = date(ref.year + 1, 2, 28)

            days_until = (candidate - ref).days

            if 0 <= days_until <= days:
                turning_age = candidate.year - b_year
                upcoming_list.append({
                    "person_id": str(row.get("person_id", "")),
                    "name": str(row.get("name", "")),
                    "relationship": str(row.get("relationship", "")),
                    "place_of_stay": str(row.get("place_of_stay", "")),
                    "dob": dob_dt.strftime("%Y-%m-%d"),
                    "formatted_dob": dob_dt.strftime("%d %B %Y"),
                    "next_birthday": candidate.strftime("%d %B %Y"),
                    "next_birthday_iso": candidate.strftime("%Y-%m-%d"),
                    "days_until": days_until,
                    "turning_age": turning_age,
                })

        # Sort by days until next birthday
        upcoming_list.sort(key=lambda x: (x["days_until"], x["name"]))
        return upcoming_list

    def get_tomorrow_birthdays(self, reference_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Get birthdays occurring tomorrow."""
        ref = reference_date if reference_date else date.today()
        tomorrow = ref + timedelta(days=1)
        return self.get_upcoming_birthdays(days=1, reference_date=ref)

    def get_next_month_birthdays(self, reference_date: Optional[date] = None) -> Tuple[int, str, List[Dict[str, Any]]]:
        """Get birthdays occurring in the next calendar month."""
        ref = reference_date if reference_date else date.today()
        next_month = 1 if ref.month == 12 else ref.month + 1
        month_name = calendar.month_name[next_month]
        records = self.filter_by_month(next_month)
        return next_month, month_name, records

    def get_person_location(
        self,
        name: Optional[str] = None,
        person_id: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Lookup location (Place_of_Stay) for a person.
        Returns (single_record_if_unique, all_matches).
        """
        if person_id:
            matches = self.search_by_person_id(person_id)
        elif name:
            matches = self.search_by_person_name(name)
        else:
            return None, []

        if len(matches) == 1:
            return matches[0], matches
        return None, matches

    # -------------------------------------------------------------
    # Formatting Helpers - Generate strict factual text for user
    # -------------------------------------------------------------

    def format_birthday_records(
        self,
        records: List[Dict[str, Any]],
        title: str = "Birthday Records",
        context_notes: str = "",
    ) -> str:
        """Format a list of birthday records into readable Markdown with factual details."""
        if not records:
            return f"No records found matching your criteria in the dataset."

        count = len(records)
        header = f"### {title} ({count} {'person' if count == 1 else 'people'})"
        if context_notes:
            header += f"\n*{context_notes}*"

        lines = [header, ""]
        for idx, r in enumerate(records, start=1):
            name = r.get("name", "Unknown")
            pid = r.get("person_id", "")
            dob = r.get("formatted_dob", r.get("dob", "Unknown"))
            rel = r.get("relationship", "Unknown")
            place = r.get("place_of_stay", "Unknown")

            item = f"{idx}. **{name}** (`{pid}`)\n"
            item += f"   - **Date of Birth:** {dob}\n"
            item += f"   - **Relationship:** {rel}\n"
            item += f"   - **Place of Stay:** {place}"
            lines.append(item)

        return "\n".join(lines)

    def format_upcoming_records(
        self,
        records: List[Dict[str, Any]],
        days: int = DEFAULT_UPCOMING_DAYS,
    ) -> str:
        """Format upcoming birthday records."""
        if not records:
            return f"There are no upcoming birthdays in the next {days} days based on the dataset."

        lines = [
            f"### Upcoming Birthdays in the Next {days} Days ({len(records)} found)",
            "",
        ]
        for idx, r in enumerate(records, start=1):
            name = r.get("name", "Unknown")
            pid = r.get("person_id", "")
            next_bday = r.get("next_birthday", "")
            days_until = r.get("days_until", 0)
            turning_age = r.get("turning_age", "")
            rel = r.get("relationship", "Unknown")
            place = r.get("place_of_stay", "Unknown")

            if days_until == 0:
                due_str = "**Today!**"
            elif days_until == 1:
                due_str = "**Tomorrow!**"
            else:
                due_str = f"in {days_until} days"

            age_str = f"(Turning {turning_age})" if turning_age else ""

            item = f"{idx}. **{name}** (`{pid}`) — {due_str} {age_str}\n"
            item += f"   - **Next Birthday:** {next_bday}\n"
            item += f"   - **Relationship:** {rel} | **Location:** {place}"
            lines.append(item)

        return "\n".join(lines)

    def format_count_response(
        self,
        count: int,
        relationship: Optional[str] = None,
        month: Optional[Union[int, str]] = None,
        records: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Format response for count_birthdays query."""
        rel_str = f"{relationship}" if relationship else "people"
        month_str = ""
        if month:
            m_int = self.parse_month(month)
            if m_int:
                month_str = f" in {calendar.month_name[m_int]}"

        if count == 0:
            return f"Found **0** birthdays for {rel_str}{month_str} in the dataset."

        res = f"There {'is' if count == 1 else 'are'} **{count}** birthday{' ' if count == 1 else 's '}for **{rel_str}**{month_str}.\n\n"
        if records:
            res += self.format_birthday_records(records, title=f"Matching {rel_str.capitalize()}{month_str}")
        return res

    def format_location_response(self, person: Dict[str, Any]) -> str:
        """Format location lookup response."""
        name = person.get("name", "Unknown")
        pid = person.get("person_id", "")
        place = person.get("place_of_stay", "Not recorded")
        rel = person.get("relationship", "Unknown")
        return (
            f"**{name}** (`{pid}`) resides in **{place}**.\n"
            f"- Relationship: {rel}"
        )
