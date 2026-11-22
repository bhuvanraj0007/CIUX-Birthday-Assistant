"""
Automated Tests for Dialogue Management Module
CIUX Birthday Assistant V3
"""

import unittest
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from service import BirthdayService
from dialogue import DialogueManager, DialogueState


class TestDialogue(unittest.TestCase):
    def setUp(self):
        self.service = BirthdayService()
        self.dm = DialogueManager(service=self.service)

    def test_context_storage(self):
        state = DialogueState()
        self.assertIsNone(state.previous_relationship)
        self.assertIsNone(state.previous_month)

        answer, debug, state_dict = self.dm.process_message(
            "Show my nephews' birthdays in September.", state
        )
        self.assertEqual(state.previous_relationship, "nephew")
        self.assertEqual(state.previous_month, "September")
        self.assertEqual(state.previous_intent, "birthday_search")
        self.assertGreaterEqual(len(state.previous_results), 1)

    def test_context_reuse_and_follow_up(self):
        state = DialogueState()

        # Turn 1: Nephews in September
        a1, d1, s1 = self.dm.process_message("Show my nephews' birthdays in September.", state)
        self.assertEqual(state.previous_relationship, "nephew")

        # Turn 2: Follow-up "What about October?" (Must reuse relationship = nephew)
        a2, d2, s2 = self.dm.process_message("What about October?", state)
        self.assertEqual(d2["entities"]["relationship"], "nephew")
        self.assertEqual(d2["entities"]["month"], "October")
        self.assertIn("Nikhil Hegde", a2)

        # Turn 3: Follow-up "How many?" (Must count previous results: 1)
        a3, d3, s3 = self.dm.process_message("How many?", state)
        self.assertIn("1", a3)
        self.assertEqual(d3["intent"], "count_birthdays")

    def test_state_updates_and_person_location(self):
        state = DialogueState()

        # Turn 1: Where does Rahul live?
        a1, d1, s1 = self.dm.process_message("Where does Rahul live?", state)
        self.assertIn("Bengaluru", a1)
        self.assertIn("Rahul", state.previous_person)

        # Turn 2: Follow-up with pronoun "When is his birthday?"
        a2, d2, s2 = self.dm.process_message("When is his birthday?", state)
        self.assertIn("18 September 2004", a2)

    def test_reset_functionality(self):
        state = DialogueState()
        _, _, _ = self.dm.process_message("Show my nephews' birthdays in September.", state)
        self.assertIsNotNone(state.previous_relationship)

        state.reset()
        self.assertIsNone(state.previous_relationship)
        self.assertIsNone(state.previous_month)
        self.assertIsNone(state.previous_person)
        self.assertIsNone(state.previous_intent)
        self.assertEqual(len(state.previous_results), 0)
        self.assertEqual(len(state.history), 0)

    def test_state_serialization(self):
        state = DialogueState(
            previous_intent="birthday_search",
            previous_person="Rahul Patil",
            previous_person_id="P004",
            previous_relationship="nephew",
            previous_month="September",
            previous_query="When is Rahul born?",
        )
        data = state.to_dict()
        self.assertEqual(data["previous_person"], "Rahul Patil")
        self.assertEqual(data["previous_relationship"], "nephew")

        restored = DialogueState.from_dict(data)
        self.assertEqual(restored.previous_person, "Rahul Patil")
        self.assertEqual(restored.previous_person_id, "P004")
        self.assertEqual(restored.previous_relationship, "nephew")


if __name__ == "__main__":
    unittest.main()
