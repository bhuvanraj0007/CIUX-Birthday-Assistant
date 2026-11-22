"""
Automated Tests for NLU Module (Rule-based & Hybrid NLU)
Tests intent recognition and entity extraction across all supported categories.
"""

import unittest
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nlu import RuleBasedNLU
from llm_nlu import HybridNLU


class TestNLU(unittest.TestCase):
    def setUp(self):
        self.known_names = ["Rahul Patil", "Lakshmi Rao", "Nikhil Hegde", "Ananya Patil"]
        self.nlu = RuleBasedNLU(known_names=self.known_names)
        self.hybrid = HybridNLU(known_names=self.known_names)

    def test_birthday_search_intent(self):
        result = self.nlu.parse("Show birthdays in September")
        self.assertEqual(result["intent"], "birthday_search")
        self.assertEqual(result["entities"]["month"], "September")

    def test_count_intent(self):
        result = self.nlu.parse("How many nephews have birthdays in October?")
        self.assertEqual(result["intent"], "count_birthdays")
        self.assertEqual(result["entities"]["relationship"], "nephew")
        self.assertEqual(result["entities"]["month"], "October")

    def test_month_extraction(self):
        # Numeric extraction test
        month_num, month_name = self.nlu.extract_month("celebrations in August")
        self.assertEqual(month_num, 8)
        self.assertEqual(month_name, "August")

        # Abbreviated month
        month_num, month_name = self.nlu.extract_month("born in jan")
        self.assertEqual(month_num, 1)
        self.assertEqual(month_name, "January")

    def test_relationship_extraction(self):
        # Plural normalized to singular
        self.assertEqual(self.nlu.extract_relationship("all my friends"), "friend")
        self.assertEqual(self.nlu.extract_relationship("list nephews"), "nephew")
        self.assertEqual(self.nlu.extract_relationship("nieces in town"), "niece")
        self.assertEqual(self.nlu.extract_relationship("my wife"), "wife")

    def test_person_extraction(self):
        # Known name extraction
        name = self.nlu.extract_person_name("Where does Rahul live?")
        self.assertEqual(name, "Rahul")

        name2 = self.nlu.extract_person_name("When is Lakshmi Rao's birthday?")
        self.assertEqual(name2, "Lakshmi Rao")

    def test_location_intent(self):
        result = self.nlu.parse("Where does Rahul live?")
        self.assertEqual(result["intent"], "person_place")
        self.assertEqual(result["entities"]["person_name"], "Rahul")

        result2 = self.nlu.parse("What is Rahul's location?")
        self.assertEqual(result2["intent"], "person_place")

    def test_tomorrow_intent(self):
        result = self.nlu.parse("Tomorrow's birthdays")
        self.assertEqual(result["intent"], "tomorrow_birthdays")
        self.assertEqual(result["entities"]["relative_date"], "tomorrow")

        result2 = self.nlu.parse("Who has birthdays tomorrow?")
        self.assertEqual(result2["intent"], "tomorrow_birthdays")

    def test_next_month_intent(self):
        result = self.nlu.parse("Show birthdays next month")
        self.assertEqual(result["intent"], "birthday_search")
        self.assertEqual(result["entities"]["relative_month"], "next_month")

    def test_person_id_extraction(self):
        pid = self.nlu.extract_person_id("What is the birthday of P004?")
        self.assertEqual(pid, "P004")

        pid_lower = self.nlu.extract_person_id("check p001 details")
        self.assertEqual(pid_lower, "P001")

    def test_hybrid_fallback(self):
        # When LLM key is absent or invalid, hybrid falls back to rule-based smoothly
        res = self.hybrid.parse("Show birthdays in September")
        self.assertEqual(res["intent"], "birthday_search")
        self.assertIn("entities", res)


if __name__ == "__main__":
    unittest.main()
