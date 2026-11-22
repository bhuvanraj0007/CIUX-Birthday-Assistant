"""
Automated Tests for NLU Module (Rule-based Intent Recognition & Entity Extraction)
CIUX Birthday Assistant V3
"""

import unittest
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nlu import RuleBasedNLU


class TestNLU(unittest.TestCase):
    def setUp(self):
        self.known_names = ["Rahul Patil", "Lakshmi Rao", "Nikhil Hegde", "Ananya Patil"]
        self.nlu = RuleBasedNLU(known_names=self.known_names)

    def test_birthday_intent(self):
        result = self.nlu.parse("Show birthdays in September.")
        self.assertEqual(result["intent"], "birthday_search")
        self.assertEqual(result["entities"]["month"], "September")

    def test_count_intent(self):
        result = self.nlu.parse("How many nephews have birthdays in October?")
        self.assertEqual(result["intent"], "count_birthdays")
        self.assertEqual(result["entities"]["relationship"], "nephew")
        self.assertEqual(result["entities"]["month"], "October")

    def test_month_extraction(self):
        month = self.nlu.extract_month("celebrations in August")
        self.assertEqual(month, "August")

        month_abbr = self.nlu.extract_month("born in jan")
        self.assertEqual(month_abbr, "January")

    def test_relationship_extraction(self):
        self.assertEqual(self.nlu.extract_relationship("Show my nephews' birthdays"), "nephew")
        self.assertEqual(self.nlu.extract_relationship("list all friends"), "friend")
        self.assertEqual(self.nlu.extract_relationship("nieces in town"), "niece")
        self.assertEqual(self.nlu.extract_relationship("my wife"), "wife")

    def test_person_name_extraction(self):
        name1 = self.nlu.extract_person_name("Where does Rahul live?")
        self.assertEqual(name1, "Rahul")

        name2 = self.nlu.extract_person_name("When is Lakshmi Rao's birthday?")
        self.assertEqual(name2, "Lakshmi Rao")

    def test_location_intent(self):
        result = self.nlu.parse("Where does Rahul live?")
        self.assertEqual(result["intent"], "person_place")
        self.assertEqual(result["entities"]["person_name"], "Rahul")

    def test_tomorrow_intent(self):
        result = self.nlu.parse("Show birthdays tomorrow.")
        self.assertEqual(result["intent"], "tomorrow_birthdays")
        self.assertEqual(result["entities"]["relative_date"], "tomorrow")

    def test_upcoming_intent(self):
        result = self.nlu.parse("Show upcoming birthdays.")
        self.assertEqual(result["intent"], "upcoming_birthdays")

    def test_person_id_extraction(self):
        pid = self.nlu.extract_person_id("What is the birthday of P004?")
        self.assertEqual(pid, "P004")

    def test_consistent_structure(self):
        result = self.nlu.parse("Hello assistant")
        self.assertIn("intent", result)
        self.assertIn("entities", result)
        entities = result["entities"]
        for key in ["person_name", "person_id", "month", "relationship", "relative_date", "relative_month"]:
            self.assertIn(key, entities)


if __name__ == "__main__":
    unittest.main()
