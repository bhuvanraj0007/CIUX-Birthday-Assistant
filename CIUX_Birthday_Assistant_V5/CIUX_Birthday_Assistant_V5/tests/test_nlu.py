"""
test_nlu.py - Unit tests for NLU intent classification and entity extraction.
CIUX Birthday Assistant - Version 5.
"""

from pathlib import Path
import sys
import unittest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nlu import RuleBasedNLU


class TestRuleBasedNLU(unittest.TestCase):

    def setUp(self):
        self.known_names = [
            "Lakshmi Rao", "Rahul Patil", "Ananya Patil", "Nikhil Hegde",
            "Raghavendra Gowda", "Shantha Gowda", "Sanjay Rao", "Rahul"
        ]
        self.known_relationships = ["Nephew", "Niece", "Father", "Mother", "Colleague", "Friend", "Sister"]
        self.nlu = RuleBasedNLU(self.known_names, self.known_relationships)

    def test_birthday_search_intent_and_month(self):
        """Test intent recognition and month entity extraction for birthday search."""
        res = self.nlu.parse("Show birthdays in September")
        self.assertEqual(res["intent"], "birthday_search")
        self.assertEqual(res["entities"]["month"], 9)

    def test_count_intent_and_relationship(self):
        """Test count_birthdays intent and relationship extraction."""
        res = self.nlu.parse("How many nephews have birthdays in October?")
        self.assertEqual(res["intent"], "count_birthdays")
        self.assertEqual(res["entities"]["relationship"], "Nephew")
        self.assertEqual(res["entities"]["month"], 10)

    def test_person_extraction(self):
        """Test person name extraction for person_birthday query."""
        res = self.nlu.parse("When is Rahul Patil's birthday?")
        self.assertEqual(res["intent"], "person_birthday")
        self.assertEqual(res["entities"]["person_name"], "Rahul Patil")

    def test_location_intent(self):
        """Test person_place intent and name extraction."""
        res = self.nlu.parse("Where does Rahul live?")
        self.assertEqual(res["intent"], "person_place")
        self.assertEqual(res["entities"]["person_name"], "Rahul")

    def test_tomorrow_intent(self):
        """Test tomorrow_birthdays intent and relative date extraction."""
        res = self.nlu.parse("Who has a birthday tomorrow?")
        self.assertEqual(res["intent"], "tomorrow_birthdays")
        self.assertEqual(res["entities"]["relative_date"], "tomorrow")

    def test_upcoming_intent(self):
        """Test upcoming_birthdays intent."""
        res = self.nlu.parse("Show upcoming birthdays")
        self.assertEqual(res["intent"], "upcoming_birthdays")

    def test_next_month_intent(self):
        """Test next month birthday search extraction."""
        res = self.nlu.parse("Who has birthdays next month?")
        self.assertEqual(res["intent"], "birthday_search")
        self.assertEqual(res["entities"]["relative_month"], "next")

    def test_person_id_extraction(self):
        """Test Person_ID entity extraction."""
        res = self.nlu.parse("Find person P004")
        self.assertEqual(res["entities"]["person_id"], "P004")

    def test_abbreviated_month(self):
        """Test month abbreviations like Oct, Jan, Dec."""
        res = self.nlu.parse("Birthdays in Jan")
        self.assertEqual(res["entities"]["month"], 1)

        res2 = self.nlu.parse("Birthdays in Oct")
        self.assertEqual(res2["entities"]["month"], 10)


if __name__ == "__main__":
    unittest.main()
