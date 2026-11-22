"""
test_service.py - Unit tests for BirthdayService data retrieval and grounding.
CIUX Birthday Assistant - Version 5.
"""

from datetime import date
from pathlib import Path
import sys
import tempfile
import unittest
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from service import BirthdayService


class TestBirthdayService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # We test with the project Excel dataset
        cls.excel_path = PROJECT_ROOT / "data" / "people.xlsx"
        cls.service = BirthdayService(cls.excel_path)

    def test_month_filtering(self):
        """Test searching birthdays in a specific month."""
        res = self.service.search_by_month(9)  # September
        self.assertGreater(res["count"], 0)
        for r in res["results"]:
            self.assertEqual(r["dob_month"], 9)
        self.assertIn("September", res["answer"])

    def test_relationship_filtering(self):
        """Test searching birthdays by relationship (e.g. Nephew)."""
        res = self.service.search_by_relationship("Nephew")
        self.assertGreater(res["count"], 0)
        for r in res["results"]:
            self.assertEqual(r["relationship"], "Nephew")

    def test_count_birthdays(self):
        """Test counting birthdays with month and relationship filter."""
        res = self.service.count_birthdays(month=10, relationship="Nephew")
        self.assertIsInstance(res["count"], int)
        self.assertGreaterEqual(res["count"], 0)
        self.assertIn(str(res["count"]), res["answer"])

    def test_person_birthday(self):
        """Test searching birthday for a known person (Rahul Patil)."""
        res = self.service.search_by_person("Rahul Patil")
        self.assertGreaterEqual(res["count"], 1)
        r = res["results"][0]
        self.assertEqual(r["name"], "Rahul Patil")
        self.assertTrue(r["has_valid_dob"])
        self.assertIn("18 September 2004", r["dob"])

    def test_person_location(self):
        """Test looking up location for a known person."""
        res = self.service.get_person_location(name="Rahul Patil")
        self.assertGreaterEqual(res["count"], 1)
        r = res["results"][0]
        self.assertIn("Bengaluru", r["place"])
        self.assertIn("lives in **Bengaluru**", res["answer"])

    def test_upcoming_birthdays(self):
        """Test upcoming birthday calculations with a fixed reference date."""
        ref_date = date(2026, 9, 1)
        res = self.service.get_upcoming_birthdays(days=30, ref_date=ref_date)
        self.assertGreater(res["count"], 0)
        # All returned upcoming birthdays must have 0 <= days_until <= 30
        for r in res["results"]:
            self.assertGreaterEqual(r["days_until"], 0)
            self.assertLessEqual(r["days_until"], 30)

    def test_empty_results(self):
        """Test searching for non-existent person or non-existent relationship/month."""
        res = self.service.search_by_person("NonExistentPersonXYZ")
        self.assertEqual(res["count"], 0)
        self.assertIn("No records found", res["answer"])

    def test_invalid_dob_values(self):
        """Test that invalid DOB values (e.g. strings, NaNs) are handled gracefully without crashing."""
        # Create a temporary mock dataset containing missing and corrupt DOBs
        data = {
            "Person_ID": ["P991", "P992", "P993"],
            "Name": ["Valid Person", "Invalid DOB Person", "Missing DOB Person"],
            "DOB": ["1990-05-15", "INVALID_DATE_STRING", None],
            "Relationship": ["Friend", "Friend", "Friend"],
            "Place_of_Stay": ["City A", "City B", "City C"]
        }
        mock_df = pd.DataFrame(data)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            mock_df.to_excel(tmp_path, index=False)
            mock_service = BirthdayService(tmp_path)

            # Valid person birthday
            res1 = mock_service.search_by_person("Valid Person")
            self.assertEqual(res1["count"], 1)
            self.assertTrue(res1["results"][0]["has_valid_dob"])

            # Invalid person birthday
            res2 = mock_service.search_by_person("Invalid DOB Person")
            self.assertEqual(res2["count"], 1)
            self.assertFalse(res2["results"][0]["has_valid_dob"])
            self.assertIn("not recorded", res2["answer"])

            # Missing DOB person
            res3 = mock_service.search_by_person("Missing DOB Person")
            self.assertEqual(res3["count"], 1)
            self.assertFalse(res3["results"][0]["has_valid_dob"])

            # Upcoming birthdays should ignore corrupt DOBs without raising ValueError
            upcoming = mock_service.get_upcoming_birthdays(days=365, ref_date=date(2026, 1, 1))
            self.assertEqual(upcoming["count"], 1)
            self.assertEqual(upcoming["results"][0]["name"], "Valid Person")

        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass


if __name__ == "__main__":
    unittest.main()
