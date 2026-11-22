"""
Automated Tests for Dialogue Management Module
Tests conversation state tracking, follow-up resolution, context reuse,
and session reset capabilities.
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
        self.assertIsNone(state.last_relationship)
        self.assertIsNone(state.last_month)

        # Process a query with relationship and month
        answer, debug, state = self.dm.process_message(
            "Show my nephews' birthdays in September", state
        )
        self.assertEqual(state.last_relationship, "nephew")
        self.assertEqual(state.last_month, "September")
        self.assertEqual(state.last_intent, "birthday_search")

    def test_follow_up_and_context_reuse(self):
        # Step 1: Query nephews in September
        state = DialogueState()
        a1, d1, state = self.dm.process_message(
            "Show my nephews' birthdays in September", state
        )
        self.assertEqual(state.last_relationship, "nephew")

        # Step 2: Follow-up query: "What about October?"
        # The dialogue manager must reuse relationship = nephew from previous turn
        a2, d2, state = self.dm.process_message("What about October?", state)
        self.assertEqual(d2["entities"]["relationship"], "nephew")
        self.assertEqual(d2["entities"]["month"], "October")
        self.assertIn("Nikhil Hegde", a2)

    def test_context_update_and_person_tracking(self):
        state = DialogueState()

        # Step 1: Query Rahul's location
        a1, d1, state = self.dm.process_message("Where does Rahul live?", state)
        self.assertIn("Bengaluru", a1)
        self.assertEqual(state.last_selected_person, "Rahul")

        # Step 2: Query birthday using pronoun "his"
        a2, d2, state = self.dm.process_message("When is his birthday?", state)
        self.assertIn("18 September 2004", a2)

    def test_context_reset(self):
        state = DialogueState()
        _, _, state = self.dm.process_message("Show my nephews in September", state)
        self.assertIsNotNone(state.last_relationship)
        self.assertIsNotNone(state.last_month)

        state.reset()
        self.assertIsNone(state.last_relationship)
        self.assertIsNone(state.last_month)
        self.assertIsNone(state.last_selected_person)
        self.assertEqual(len(state.history), 0)

    def test_state_serialization(self):
        state = DialogueState(
            last_selected_person="Rahul Patil",
            last_person_id="P004",
            last_relationship="nephew",
            last_month="September",
            last_intent="birthday_search",
        )
        serialized = state.to_dict()
        self.assertEqual(serialized["last_selected_person"], "Rahul Patil")
        self.assertEqual(serialized["last_relationship"], "nephew")

        restored = DialogueState.from_dict(serialized)
        self.assertEqual(restored.last_selected_person, "Rahul Patil")
        self.assertEqual(restored.last_person_id, "P004")
        self.assertEqual(restored.last_relationship, "nephew")


if __name__ == "__main__":
    unittest.main()
