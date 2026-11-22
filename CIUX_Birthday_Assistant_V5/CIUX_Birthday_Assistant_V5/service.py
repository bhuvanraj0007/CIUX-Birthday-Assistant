"""
service.py - Factual Data and Query Resolution Service for CIUX Birthday Assistant V5.

Strictly grounded in the Excel dataset (data/people.xlsx).
Single source of truth. Never fabricates birthdays, relationships, or locations.
"""

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

from config import DEFAULT_UPCOMING_DAYS, EXCEL_PATH

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

# Mapping common relationship variations/plurals to canonical labels
RELATIONSHIP_NORMALIZATION = {
    "nephews": "Nephew", "nephew": "Nephew",
    "nieces": "Niece", "niece": "Niece",
    "uncles": "Uncle", "uncle": "Uncle",
    "aunts": "Aunt", "aunt": "Aunt",
    "cousins": "Cousin", "cousin": "Cousin",
    "colleagues": "Colleague", "colleague": "Colleague", "coworker": "Colleague", "coworkers": "Colleague",
    "students": "Student", "student": "Student",
    "friends": "Friend", "friend": "Friend", "buddies": "Friend", "buddy": "Friend",
    "brothers": "Brother", "brother": "Brother",
    "sisters": "Sister", "sister": "Sister",
    "fathers": "Father", "father": "Father", "dad": "Father", "papa": "Father",
    "mothers": "Mother", "mother": "Mother", "mom": "Mother", "mama": "Mother",
    "wives": "Wife", "wife": "Wife", "spouse": "Spouse", "spouses": "Spouse",
    "husbands": "Husband", "husband": "Husband",
    "neighbours": "Neighbour", "neighbour": "Neighbour", "neighbors": "Neighbour", "neighbor": "Neighbour",
    "sister-in-law": "Sister-in-law", "sisters-in-law": "Sister-in-law",
    "brother-in-law": "Brother-in-law", "brothers-in-law": "Brother-in-law",
    "daughters": "Daughter", "daughter": "Daughter",
    "sons": "Son", "son": "Son"
}


class BirthdayService:
    """Service to load, filter, and format factual information strictly from Excel."""

    def __init__(self, excel_path: Optional[Union[str, Path]] = None):
        self.excel_path = Path(excel_path) if excel_path else EXCEL_PATH
        self._df: Optional[pd.DataFrame] = None
        self._col_id = "Person_ID"
        self._col_name = "Name"
        self._col_dob = "DOB"
        self._col_rel = "Relationship"
        self._col_place = "Place_of_Stay"
        self._col_nick = "Nickname"
        self._col_group = "Relationship_Group"
        self._col_detail = "Relationship_Detail"
        self.load_data()

    def _detect_columns(self, df: pd.DataFrame) -> None:
        """Map existing Excel columns flexibly to canonical internal names."""
        cols = {str(c).strip().lower(): c for c in df.columns}

        # ID column
        for cand in ["person_id", "id", "pid", "personid"]:
            if cand in cols:
                self._col_id = cols[cand]
                break

        # Name column
        for cand in ["name", "full_name", "person_name", "fullname"]:
            if cand in cols:
                self._col_name = cols[cand]
                break

        # DOB column
        for cand in ["dob", "dateofbirth", "date_of_birth", "birthdate", "birth_date"]:
            if cand in cols:
                self._col_dob = cols[cand]
                break

        # Relationship column
        for cand in ["relationship", "relation", "relation_type"]:
            if cand in cols:
                self._col_rel = cols[cand]
                break

        # Place / Location column
        for cand in ["place_of_stay", "place", "location", "city", "stay", "residence", "address"]:
            if cand in cols:
                self._col_place = cols[cand]
                break

        # Optional columns
        for cand in ["nickname", "nick_name", "alias"]:
            if cand in cols:
                self._col_nick = cols[cand]
                break

        for cand in ["relationship_group", "group"]:
            if cand in cols:
                self._col_group = cols[cand]
                break

        for cand in ["relationship_detail", "detail"]:
            if cand in cols:
                self._col_detail = cols[cand]
                break

    def load_data(self, force_reload: bool = False) -> pd.DataFrame:
        """Load, validate, and normalize the Excel dataset."""
        if self._df is not None and not force_reload:
            return self._df

        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel dataset not found at {self.excel_path}")

        raw_df = pd.read_excel(self.excel_path)
        raw_df.columns = [str(c).strip() for c in raw_df.columns]
        self._detect_columns(raw_df)

        df = raw_df.copy()

        # String columns cleanup
        str_cols = [self._col_id, self._col_name, self._col_rel, self._col_place]
        if self._col_nick in df.columns:
            str_cols.append(self._col_nick)
        if self._col_group in df.columns:
            str_cols.append(self._col_group)
        if self._col_detail in df.columns:
            str_cols.append(self._col_detail)

        for col in str_cols:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        # Safe DOB parsing (coerce errors to NaT without crashing)
        if self._col_dob in df.columns:
            df["_clean_dob"] = pd.to_datetime(df[self._col_dob], errors="coerce")
            df["_dob_month"] = df["_clean_dob"].dt.month
            df["_dob_day"] = df["_clean_dob"].dt.day
            df["_dob_year"] = df["_clean_dob"].dt.year
        else:
            df["_clean_dob"] = pd.NaT
            df["_dob_month"] = None
            df["_dob_day"] = None
            df["_dob_year"] = None

        self._df = df
        return self._df

    def get_known_names(self) -> List[str]:
        """Return unique list of registered person names and nicknames for NLU extraction."""
        df = self.load_data()
        names = set()
        for _, row in df.iterrows():
            name = str(row.get(self._col_name, "")).strip()
            if name:
                names.add(name)
            if self._col_nick in df.columns:
                nick = str(row.get(self._col_nick, "")).strip()
                if nick:
                    names.add(nick)
        return sorted(list(names), key=len, reverse=True)

    def get_known_relationships(self) -> List[str]:
        """Return unique relationships present in the dataset."""
        df = self.load_data()
        rels = set()
        for r in df[self._col_rel].dropna().unique():
            cleaned = str(r).strip()
            if cleaned:
                rels.add(cleaned)
        return sorted(list(rels))

    def _row_to_dict(self, row: pd.Series) -> Dict[str, Any]:
        """Convert a pandas row to a clean serializable dictionary."""
        dob_val = row.get("_clean_dob")
        dob_str = ""
        birth_month = None
        birth_day = None
        birth_year = None

        if pd.notna(dob_val):
            dob_date = dob_val.date() if isinstance(dob_val, pd.Timestamp) else dob_val
            dob_str = dob_date.strftime("%d %B %Y")
            birth_month = dob_date.month
            birth_day = dob_date.day
            birth_year = dob_date.year

        result = {
            "person_id": str(row.get(self._col_id, "")).strip(),
            "name": str(row.get(self._col_name, "")).strip(),
            "dob": dob_str,
            "dob_month": birth_month,
            "dob_day": birth_day,
            "dob_year": birth_year,
            "has_valid_dob": pd.notna(dob_val),
            "relationship": str(row.get(self._col_rel, "")).strip(),
            "place": str(row.get(self._col_place, "")).strip()
        }

        if self._col_nick in row:
            result["nickname"] = str(row.get(self._col_nick, "")).strip()
        if self._col_group in row:
            result["relationship_group"] = str(row.get(self._col_group, "")).strip()
        if self._col_detail in row:
            result["relationship_detail"] = str(row.get(self._col_detail, "")).strip()

        return result

    def calculate_upcoming_details(self, dob_date: date, ref_date: Optional[date] = None) -> Tuple[int, date, int]:
        """
        Calculate days until next birthday, next birthday date, and next age.
        Correctly handles:
        - Past birthdays in the current calendar year (rolls over to next year)
        - December-to-January transitions
        - Leap years (Feb 29 on non-leap year falls on March 1)
        """
        if ref_date is None:
            ref_date = date.today()

        # Birthday in reference year
        try:
            bday_this_year = dob_date.replace(year=ref_date.year)
        except ValueError:
            # Leap day birthday on non-leap year
            bday_this_year = date(ref_date.year, 3, 1)

        if bday_this_year < ref_date:
            # Has already passed this year -> next year
            next_year = ref_date.year + 1
            try:
                next_bday = dob_date.replace(year=next_year)
            except ValueError:
                next_bday = date(next_year, 3, 1)
        else:
            next_bday = bday_this_year

        days_until = (next_bday - ref_date).days
        upcoming_age = next_bday.year - dob_date.year
        return days_until, next_bday, upcoming_age

    def _normalize_relationship_query(self, rel_query: Optional[str]) -> Optional[str]:
        """Normalize plural/informal relationship strings to dataset standards."""
        if not rel_query:
            return None
        cleaned = rel_query.strip().lower()
        if cleaned in RELATIONSHIP_NORMALIZATION:
            return RELATIONSHIP_NORMALIZATION[cleaned]
        return rel_query.strip()

    def search_birthdays(
        self,
        month: Optional[int] = None,
        relationship: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search birthdays filtered by calendar month and/or relationship."""
        df = self.load_data()
        filtered = df.copy()

        # Filter out rows with invalid or missing DOB
        filtered = filtered[filtered["_clean_dob"].notna()]

        rel_norm = self._normalize_relationship_query(relationship)
        if rel_norm:
            # Match against relationship or detail
            rel_lower = rel_norm.lower()
            mask = filtered[self._col_rel].str.lower() == rel_lower
            if self._col_detail in filtered.columns:
                mask = mask | filtered[self._col_detail].str.lower().str.contains(rel_lower, na=False)
            filtered = filtered[mask]

        if month is not None:
            filtered = filtered[filtered["_dob_month"] == month]

        records = [self._row_to_dict(row) for _, row in filtered.iterrows()]
        records.sort(key=lambda r: (r["dob_month"] or 0, r["dob_day"] or 0, r["name"]))

        month_label = MONTH_NAMES.get(month, f"month {month}") if month else None
        filter_desc = []
        if rel_norm:
            filter_desc.append(f"relationship '{rel_norm}'")
        if month_label:
            filter_desc.append(f"in {month_label}")

        desc_str = " ".join(filter_desc) if filter_desc else "in the dataset"

        if not records:
            answer = f"No birthdays found for {desc_str}."
        else:
            lines = [f"Found {len(records)} birthday{'s' if len(records) > 1 else ''} for {desc_str}:"]
            for r in records:
                place_info = f" • Lives in {r['place']}" if r['place'] else ""
                lines.append(f"• **{r['name']}** ({r['relationship']}) – {r['dob']}{place_info}")
            answer = "\n".join(lines)

        return {
            "count": len(records),
            "results": records,
            "answer": answer,
            "query_type": "birthday_search",
            "filters": {"month": month, "relationship": rel_norm}
        }

    def search_by_month(self, month: int) -> Dict[str, Any]:
        """Search all birthdays in a given calendar month (1-12)."""
        return self.search_birthdays(month=month)

    def search_by_relationship(self, relationship: str) -> Dict[str, Any]:
        """Search all birthdays for a specific relationship."""
        return self.search_birthdays(relationship=relationship)

    def count_birthdays(
        self,
        month: Optional[int] = None,
        relationship: Optional[str] = None
    ) -> Dict[str, Any]:
        """Count birthdays matching month and/or relationship filters."""
        res = self.search_birthdays(month=month, relationship=relationship)
        cnt = res["count"]
        month_label = MONTH_NAMES.get(month, "") if month else ""
        rel_label = res["filters"]["relationship"] or "people"

        parts = []
        if res["filters"]["relationship"]:
            parts.append(f"{res['filters']['relationship']}(s)")
        else:
            parts.append("people")

        if month_label:
            parts.append(f"in {month_label}")

        target_desc = " ".join(parts)

        if cnt == 0:
            answer = f"There are 0 birthdays found for {target_desc}."
        elif cnt == 1:
            person = res["results"][0]
            answer = f"There is 1 birthday for {target_desc}: **{person['name']}** on {person['dob']}."
        else:
            answer = f"There are **{cnt}** birthdays for {target_desc}."

        return {
            "count": cnt,
            "results": res["results"],
            "answer": answer,
            "query_type": "count_birthdays",
            "filters": {"month": month, "relationship": res["filters"]["relationship"]}
        }

    def search_by_person(self, name: str) -> Dict[str, Any]:
        """Search birthday and details for a specific person name or nickname."""
        df = self.load_data()
        cleaned_query = name.strip().lower()

        # Step 1: Exact full name match
        exact_matches = df[df[self._col_name].str.lower() == cleaned_query]

        # Step 2: Nickname match
        if exact_matches.empty and self._col_nick in df.columns:
            exact_matches = df[df[self._col_nick].str.lower() == cleaned_query]

        # Step 3: First name / word boundary match
        if exact_matches.empty:
            matches = df[df[self._col_name].str.lower().apply(
                lambda val: any(w == cleaned_query for w in val.split()) or cleaned_query in val
            )]
        else:
            matches = exact_matches

        records = [self._row_to_dict(row) for _, row in matches.iterrows()]

        if not records:
            answer = f"No records found for '{name}' in the dataset."
        elif len(records) == 1:
            r = records[0]
            if r["has_valid_dob"]:
                answer = f"**{r['name']}**'s birthday is on **{r['dob']}** ({r['relationship']})."
                if r["place"]:
                    answer += f" They live in {r['place']}."
            else:
                answer = f"**{r['name']}** ({r['relationship']}) is listed in the dataset, but their date of birth is not recorded."
                if r["place"]:
                    answer += f" Place of stay: {r['place']}."
        else:
            lines = [f"Found {len(records)} people matching '{name}':"]
            for r in records:
                bday_info = r['dob'] if r['has_valid_dob'] else "DOB not recorded"
                lines.append(f"• **{r['name']}** [ID: {r['person_id']}] ({r['relationship']}) – Birthday: {bday_info}, Lives in: {r['place']}")
            answer = "\n".join(lines)

        return {
            "count": len(records),
            "results": records,
            "answer": answer,
            "query_type": "person_birthday",
            "person_name": name
        }

    def search_by_person_id(self, person_id: str) -> Dict[str, Any]:
        """Search a person strictly by Person_ID."""
        df = self.load_data()
        pid_clean = person_id.strip().upper()
        matches = df[df[self._col_id].str.upper() == pid_clean]
        records = [self._row_to_dict(row) for _, row in matches.iterrows()]

        if not records:
            answer = f"No person found with ID '{person_id}'."
        else:
            r = records[0]
            bday_str = r['dob'] if r['has_valid_dob'] else "DOB not recorded"
            place_str = f" Lives in {r['place']}." if r['place'] else ""
            answer = f"**{r['name']}** [ID: {r['person_id']}] ({r['relationship']}) – Birthday: {bday_str}.{place_str}"

        return {
            "count": len(records),
            "results": records,
            "answer": answer,
            "query_type": "person_id_search",
            "person_id": person_id
        }

    def get_person_location(self, name: str = "", person_id: Optional[str] = None) -> Dict[str, Any]:
        """Look up where a person lives / stays."""
        df = self.load_data()

        if person_id:
            matches = df[df[self._col_id].str.upper() == person_id.strip().upper()]
        elif name:
            clean_name = name.strip().lower()
            matches = df[df[self._col_name].str.lower() == clean_name]
            if matches.empty and self._col_nick in df.columns:
                matches = df[df[self._col_nick].str.lower() == clean_name]
            if matches.empty:
                matches = df[df[self._col_name].str.lower().apply(
                    lambda val: any(w == clean_name for w in val.split()) or clean_name in val
                )]
        else:
            return {
                "count": 0,
                "results": [],
                "answer": "Please specify a person's name or ID to look up their location.",
                "query_type": "person_place"
            }

        records = [self._row_to_dict(row) for _, row in matches.iterrows()]

        if not records:
            target = person_id if person_id else name
            answer = f"No location records found for '{target}' in the dataset."
        elif len(records) == 1:
            r = records[0]
            if r["place"]:
                answer = f"**{r['name']}** lives in **{r['place']}** ({r['relationship']})."
            else:
                answer = f"**{r['name']}** is in the dataset, but their place of stay is not specified."
        else:
            lines = [f"Found {len(records)} matching records:"]
            for r in records:
                loc = r['place'] if r['place'] else "Location unknown"
                lines.append(f"• **{r['name']}** [ID: {r['person_id']}] ({r['relationship']}) – Lives in {loc}")
            answer = "\n".join(lines)

        return {
            "count": len(records),
            "results": records,
            "answer": answer,
            "query_type": "person_place",
            "target": name or person_id
        }

    def get_upcoming_birthdays(
        self,
        days: int = DEFAULT_UPCOMING_DAYS,
        ref_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Retrieve all birthdays occurring within the next `days` (default 30).
        Calculates exact days until birthday, age turning, and handles year boundaries.
        """
        if ref_date is None:
            ref_date = date.today()

        df = self.load_data()
        valid_df = df[df["_clean_dob"].notna()]

        upcoming_list = []
        for _, row in valid_df.iterrows():
            dob_ts = row["_clean_dob"]
            dob_date = dob_ts.date() if isinstance(dob_ts, pd.Timestamp) else dob_ts
            days_until, next_bday, next_age = self.calculate_upcoming_details(dob_date, ref_date)

            if 0 <= days_until <= days:
                rec = self._row_to_dict(row)
                rec["days_until"] = days_until
                rec["next_birthday"] = next_bday.strftime("%d %B %Y")
                rec["upcoming_age"] = next_age
                upcoming_list.append(rec)

        # Sort chronologically by days remaining
        upcoming_list.sort(key=lambda r: (r["days_until"], r["name"]))

        if not upcoming_list:
            answer = f"No upcoming birthdays found in the next {days} days from {ref_date.strftime('%d %B %Y')}."
        else:
            lines = [f"Found {len(upcoming_list)} upcoming birthday{'s' if len(upcoming_list) > 1 else ''} in the next {days} days:"]
            for r in upcoming_list:
                if r["days_until"] == 0:
                    countdown = "🎉 **TODAY!**"
                elif r["days_until"] == 1:
                    countdown = "tomorrow (in 1 day)"
                else:
                    countdown = f"in {r['days_until']} days"

                age_info = f", turning {r['upcoming_age']}" if r['upcoming_age'] > 0 else ""
                lines.append(f"• **{r['name']}** ({r['relationship']}) – {r['next_birthday']} ({countdown}{age_info})")
            answer = "\n".join(lines)

        return {
            "count": len(upcoming_list),
            "results": upcoming_list,
            "answer": answer,
            "query_type": "upcoming_birthdays",
            "days_window": days,
            "reference_date": ref_date.strftime("%Y-%m-%d")
        }

    def get_tomorrow_birthdays(self, ref_date: Optional[date] = None) -> Dict[str, Any]:
        """Retrieve birthdays occurring exactly tomorrow."""
        if ref_date is None:
            ref_date = date.today()

        tomorrow = ref_date + timedelta(days=1)
        df = self.load_data()
        valid_df = df[df["_clean_dob"].notna()]

        # Filter by month and day matching tomorrow
        matches = valid_df[(valid_df["_dob_month"] == tomorrow.month) & (valid_df["_dob_day"] == tomorrow.day)]
        records = []
        for _, row in matches.iterrows():
            dob_ts = row["_clean_dob"]
            dob_date = dob_ts.date() if isinstance(dob_ts, pd.Timestamp) else dob_ts
            turning_age = tomorrow.year - dob_date.year
            rec = self._row_to_dict(row)
            rec["upcoming_age"] = turning_age
            records.append(rec)

        records.sort(key=lambda r: r["name"])

        tomorrow_str = tomorrow.strftime("%d %B")
        if not records:
            answer = f"No one in the dataset has a birthday tomorrow ({tomorrow_str})."
        elif len(records) == 1:
            r = records[0]
            age_info = f", turning {r['upcoming_age']}" if r['upcoming_age'] > 0 else ""
            answer = f"🎂 Tomorrow ({tomorrow_str}), **{r['name']}** ({r['relationship']}) has a birthday{age_info}!"
        else:
            lines = [f"🎂 Found {len(records)} birthdays tomorrow ({tomorrow_str}):"]
            for r in records:
                age_info = f" (turning {r['upcoming_age']})" if r['upcoming_age'] > 0 else ""
                lines.append(f"• **{r['name']}** ({r['relationship']}){age_info} – Lives in {r['place']}")
            answer = "\n".join(lines)

        return {
            "count": len(records),
            "results": records,
            "answer": answer,
            "query_type": "tomorrow_birthdays",
            "target_date": tomorrow.strftime("%Y-%m-%d")
        }

    def get_next_month_birthdays(self, ref_date: Optional[date] = None) -> Dict[str, Any]:
        """Retrieve all birthdays occurring in the upcoming calendar month."""
        if ref_date is None:
            ref_date = date.today()

        next_month = (ref_date.month % 12) + 1
        res = self.search_by_month(next_month)
        month_label = MONTH_NAMES.get(next_month, str(next_month))

        if res["count"] == 0:
            res["answer"] = f"No birthdays found for next month ({month_label})."
        else:
            res["answer"] = res["answer"].replace(f"in {month_label}", f"next month ({month_label})")

        res["query_type"] = "next_month_birthdays"
        return res
