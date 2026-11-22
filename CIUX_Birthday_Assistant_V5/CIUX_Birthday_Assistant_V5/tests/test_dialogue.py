"""
test_dialogue.py - Unit tests for multi-turn dialogue management and context tracking.
CIUX Birthday Assistant - Version 5.
"""

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dialogue import DialogueManager
from nlu import RuleBasedNLU
from service import BirthdayService


class TestDialogueManager(unittest.TestCase):

    def setUp(self):
        self.excel_path = PROJECT_ROOT / "data" / "people.xlsx"
        self.service = BirthdayService(self.excel_path)
        self.nlu = RuleBasedNLU(
            self.service.get_known_names(),
            self.service.get_known_relationships()
        )
        self.dialogue_manager = DialogueManager()
        self.session_id = "test_user_session_abc"

    def test_context_storage(self):
        """Test initial context state initialization."""
        ctx = self.dialogue_manager.get_context(self.session_id)
        self.assertIsNotNone(ctx)
        self.assertIsNone(ctx["last_person"])
        self.assertIsNone(ctx["last_relationship"])
        self.assertIsNone(ctx["last_month"])

    def test_context_update(self):
        """Test that executing a turn properly updates context variables."""
        nlu_res = self.nlu.parse("Show my nephews' birthdays in September")
        reply = self.dialogue_manager.process_turn(self.session_id, nlu_res, self.service)

        ctx = self.dialogue_manager.get_context(self.session_id)
        self.assertEqual(ctx["last_relationship"], "Nephew")
        self.assertEqual(ctx["last_month"], 9)
        self.assertEqual(ctx["last_intent"], "birthday_search")
        self.assertGreater(len(ctx["history"]), 0)

    def test_context_reuse_ellipsis(self):
        """Test that follow-up query 'What about October?' inherits previous relationship."""
        # Turn 1: Establish relationship (Nephew) and month (September)
        nlu_res1 = self.nlu.parse("Show my nephews' birthdays in September")
        self.dialogue_manager.process_turn(self.session_id, nlu_res1, self.service)

        # Turn 2: Follow-up query provides only month (October)
        nlu_res2 = self.nlu.parse("What about October?")
        reply2 = self.dialogue_manager.process_turn(self.session_id, nlu_res2, self.service)

        # Should retain Nephew as relationship and change month to 10
        self.assertEqual(reply2["debug"]["entities"]["relationship"], "Nephew")
        self.assertEqual(reply2["debug"]["entities"]["month"], 10)
        self.assertIn("Nikhil Hegde", reply2["answer"])

    def test_context_reuse_pronoun(self):
        """Test that 'Where does he live?' resolves to last mentioned person."""
        # Turn 1: Ask about Rahul Patil
        nlu_res1 = self.nlu.parse("When is Rahul's birthday?")
        self.dialogue_manager.process_turn(self.session_id, nlu_res1, self.service)

        # Turn 2: Follow up with location query referring to Rahul
        nlu_res2 = self.nlu.parse("Where does he live?")
        reply2 = self.dialogue_manager.process_turn(self.session_id, nlu_res2, self.service)

        self.assertEqual(reply2["debug"]["entities"]["person_name"], "Rahul")
        self.assertIn("Bengaluru", reply2["answer"])

    def test_entity_replacement(self):
        """Test that introducing a new explicit entity replaces the previous context value."""
        # Turn 1: Month 9
        nlu_res1 = self.nlu.parse("Show birthdays in September")
        self.dialogue_manager.process_turn(self.session_id, nlu_res1, self.service)
        ctx = self.dialogue_manager.get_context(self.session_id)
        self.assertEqual(ctx["last_month"], 9)

        # Turn 2: Explicitly query March
        nlu_res2 = self.nlu.parse("Show birthdays in March")
        self.dialogue_manager.process_turn(self.session_id, nlu_res2, self.service)
        ctx = self.dialogue_manager.get_context(self.session_id)
        self.assertEqual(ctx["last_month"], 3)

    def test_context_reset(self):
        """Test that reset_context completely purges the conversational state."""
        nlu_res = self.nlu.parse("Show my nephews' birthdays in September")
        self.dialogue_manager.process_turn(self.session_id, nlu_res, self.service)

        # Reset
        self.dialogue_manager.reset_context(self.session_id)
        ctx = self.dialogue_manager.get_context(self.session_id)

        self.assertIsNone(ctx["last_person"])
        self.assertIsNone(ctx["last_relationship"])
        self.assertIsNone(ctx["last_month"])
        self.assertIsNone(ctx["last_intent"])
        self.assertEqual(len(ctx["history"]), 0)


if __name__ == "__main__":
    unittest.main()
