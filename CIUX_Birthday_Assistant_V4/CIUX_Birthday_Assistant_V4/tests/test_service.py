"""
Automated Tests for BirthdayService Module
Tests data loading, filtering, upcoming birthday calculations, location lookups,
and handling of missing or corrupted values.
"""

import unittest
from datetime import date
from pathlib import Path
import sys
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from service import BirthdayService


class TestService(unittest.TestCase):
    def setUp(self):
        self.service = BirthdayService()

    def test_dataset_loading(self):
        self.assertFalse(self.service.df.empty, "Dataset should load records")
        self.assertGreaterEqual(len(self.service.df), 10)
        self.assertIn("person_id", self.service.df.columns)
        self.assertIn("name", self.service.df.columns)
        self.assertIn("dob_parsed", self.service.df.columns)

    def test_month_filtering(self):
        # Filter by month 9 (September)
        sept_records = self.service.filter_by_month(9)
        self.assertTrue(len(sept_records) > 0)
        for r in sept_records:
            self.assertEqual(r["birth_month"], 9)

        # Test string month
        oct_records = self.service.filter_by_month("October")
        self.assertTrue(len(oct_records) > 0)
        for r in oct_records:
            self.assertEqual(r["birth_month"], 10)

    def test_relationship_filtering(self):
        nephews = self.service.filter_by_relationship("nephew")
        self.assertTrue(len(nephews) > 0)
        for r in nephews:
            self.assertIn("nephew", r["relationship"].lower())

    def test_count_results(self):
        count, records = self.service.count_birthdays(month=9, relationship="nephew")
        self.assertEqual(count, len(records))
        self.assertTrue(count >= 1)

    def test_person_birthday(self):
        matches = self.service.search_by_person_name("Rahul Patil")
        self.assertTrue(len(matches) >= 1)
        rahul = matches[0]
        self.assertEqual(rahul["person_id"], "P004")
        self.assertEqual(rahul["dob"], "2004-09-18")
        self.assertEqual(rahul["formatted_dob"], "18 September 2004")

    def test_person_id_search(self):
        matches = self.service.search_by_person_id("P004")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["name"], "Rahul Patil")

    def test_person_location(self):
        person, matches = self.service.get_person_location(name="Rahul Patil")
        self.assertIsNotNone(person)
        self.assertEqual(person["place_of_stay"], "Bengaluru")

    def test_upcoming_birthdays_calculation(self):
        # Use a fixed reference date for deterministic testing
        # Rahul Patil was born Sept 18.
        # Set reference date to 2026-09-01 (17 days before his birthday)
        ref_date = date(2026, 9, 1)
        upcoming = self.service.get_upcoming_birthdays(days=30, reference_date=ref_date)
        self.assertTrue(len(upcoming) > 0)

        # Verify sorted ascending by days_until
        days_list = [u["days_until"] for u in upcoming]
        self.assertEqual(days_list, sorted(days_list))

        # Check Rahul is in the list
        names = [u["name"] for u in upcoming]
        self.assertIn("Rahul Patil", names)
        rahul_entry = next(u for u in upcoming if u["name"] == "Rahul Patil")
        self.assertEqual(rahul_entry["days_until"], 17)
        self.assertEqual(rahul_entry["turning_age"], 22)

    def test_upcoming_year_transition(self):
        # Reference date Dec 25. Next birthday in Jan should roll over to next year
        ref_date = date(2026, 12, 25)
        upcoming = self.service.get_upcoming_birthdays(days=30, reference_date=ref_date)
        for u in upcoming:
            self.assertGreaterEqual(u["days_until"], 0)
            self.assertLessEqual(u["days_until"], 30)

    def test_empty_results_and_missing_values(self):
        # Non-existent person
        matches = self.service.search_by_person_name("NonExistentPersonXYZ")
        self.assertEqual(len(matches), 0)

        # Non-existent month
        invalid_month = self.service.filter_by_month(99)
        self.assertEqual(len(invalid_month), 0)

        # Service with empty mock DataFrame
        empty_service = BirthdayService.__new__(BirthdayService)
        empty_service.dataset_path = Path("fake.xlsx")
        empty_service.df = pd.DataFrame(columns=["person_id", "name", "dob_parsed", "relationship", "place_of_stay", "birth_month", "birth_day", "birth_year"])
        self.assertEqual(empty_service.search_by_person_name("Anyone"), [])
        self.assertEqual(empty_service.filter_by_month(5), [])
        self.assertEqual(empty_service.get_upcoming_birthdays(30), [])


if __name__ == "__main__":
    unittest.main()
