"""
Automated Tests for Service Module
CIUX Birthday Assistant V3
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

    def test_birthday_filtering(self):
        # Combined search by month and relationship
        results = self.service.search_birthdays(month="September", relationship="nephew")
        self.assertGreaterEqual(len(results), 1)
        for r in results:
            self.assertEqual(r["birth_month"], 9)
            self.assertIn("nephew", r["relationship"].lower())

    def test_month_filtering(self):
        results = self.service.filter_by_month("September")
        self.assertGreaterEqual(len(results), 1)
        for r in results:
            self.assertEqual(r["birth_month"], 9)

        # Numeric month test
        results_num = self.service.filter_by_month(1)
        for r in results_num:
            self.assertEqual(r["birth_month"], 1)

    def test_relationship_filtering(self):
        nephews = self.service.filter_by_relationship("nephew")
        self.assertGreaterEqual(len(nephews), 1)
        for r in nephews:
            self.assertIn("nephew", r["relationship"].lower())

    def test_count(self):
        count, records = self.service.count_birthdays(month=9, relationship="nephew")
        self.assertEqual(count, len(records))
        self.assertGreaterEqual(count, 1)

    def test_person_birthday(self):
        matches = self.service.search_by_person_name("Rahul Patil")
        self.assertGreaterEqual(len(matches), 1)
        person = matches[0]
        self.assertEqual(person["person_id"], "P004")
        self.assertEqual(person["dob"], "2004-09-18")
        self.assertEqual(person["formatted_dob"], "18 September 2004")

    def test_person_location(self):
        person, matches = self.service.get_person_location(name="Rahul Patil")
        self.assertIsNotNone(person)
        self.assertEqual(person["place_of_stay"], "Bengaluru")

    def test_upcoming_birthdays(self):
        # Fixed reference date: 17 days before Rahul Patil's birthday (Sept 18)
        ref_date = date(2026, 9, 1)
        upcoming = self.service.get_upcoming_birthdays(days=30, reference_date=ref_date)
        self.assertGreater(len(upcoming), 0)

        # Check sorted order
        days_seq = [u["days_until"] for u in upcoming]
        self.assertEqual(days_seq, sorted(days_seq))

        # Check Rahul is present
        rahul_entry = next((u for u in upcoming if u["person_id"] == "P004"), None)
        self.assertIsNotNone(rahul_entry)
        self.assertEqual(rahul_entry["days_until"], 17)
        self.assertEqual(rahul_entry["turning_age"], 22)

    def test_tomorrow_birthdays(self):
        # Reference date 2026-09-17 (so Sept 18 is tomorrow)
        ref_date = date(2026, 9, 17)
        tomorrow_list = self.service.get_tomorrow_birthdays(reference_date=ref_date)
        pids = [p["person_id"] for p in tomorrow_list]
        self.assertIn("P004", pids)

    def test_empty_results(self):
        # Nonexistent person
        matches = self.service.search_by_person_name("ZzzNonExistent")
        self.assertEqual(len(matches), 0)

        # Nonexistent ID
        id_matches = self.service.search_by_person_id("P99999")
        self.assertEqual(len(id_matches), 0)

        # Invalid month
        empty_month = self.service.filter_by_month(99)
        self.assertEqual(len(empty_month), 0)


if __name__ == "__main__":
    unittest.main()
