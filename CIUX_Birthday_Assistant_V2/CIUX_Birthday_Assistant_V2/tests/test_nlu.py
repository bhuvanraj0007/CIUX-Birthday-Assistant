"""
test_nlu.py - Unit Tests for Natural Language Understanding (nlu.py).

Tests intent recognition and entity extraction across all supported query types.
"""

import pytest
from nlu import parse_query, extract_person_name, extract_person_id, extract_month, extract_relationship


class TestNLU:
    """Test suite for rule-based NLU."""

    def test_birthday_search_by_month(self):
        result = parse_query("Show birthdays in September.")
        assert result["intent"] == "birthday_search"
        assert result["entities"]["month"] == "September"

    def test_count_birthdays_intent(self):
        result = parse_query("How many nephews have birthdays in October?")
        assert result["intent"] == "count_birthdays"
        assert result["entities"]["relationship"] == "nephew"
        assert result["entities"]["month"] == "October"

    def test_general_count_birthdays(self):
        result = parse_query("Count birthdays.")
        assert result["intent"] == "count_birthdays"

    def test_person_location_intent(self):
        result = parse_query("Where does Rahul live?")
        assert result["intent"] == "person_place"
        assert result["entities"]["person_name"] == "Rahul"

    def test_person_location_with_id(self):
        result = parse_query("Where does P004 live?")
        assert result["intent"] == "person_place"
        assert result["entities"]["person_id"] == "P004"

    def test_person_birthday_intent(self):
        result = parse_query("When is Rahul's birthday?")
        assert result["intent"] == "person_birthday"
        assert result["entities"]["person_name"] == "Rahul"

    def test_find_person_birthday(self):
        result = parse_query("Find Rahul's birthday.")
        assert result["intent"] == "person_birthday"
        assert result["entities"]["person_name"] == "Rahul"

    def test_person_birthday_with_id(self):
        result = parse_query("Find birthday for P004.")
        assert result["intent"] == "person_birthday"
        assert result["entities"]["person_id"] == "P004"

    def test_upcoming_birthdays_intent(self):
        result = parse_query("Show upcoming birthdays.")
        assert result["intent"] == "upcoming_birthdays"
        assert result["entities"]["relative_date"] == "upcoming"

    def test_tomorrow_birthdays_intent(self):
        result = parse_query("Who has a birthday tomorrow?")
        assert result["intent"] == "tomorrow_birthdays"
        assert result["entities"]["relative_date"] == "tomorrow"

    def test_relationship_variations(self):
        # Plural to singular canonical
        assert extract_relationship("cousins") == "cousin"
        assert extract_relationship("my nephews") == "nephew"
        assert extract_relationship("sisters-in-law") == "sister-in-law"
        assert extract_relationship("aunties") == "aunt"

    def test_month_variations(self):
        assert extract_month("in Jan") == "January"
        assert extract_month("born in Sept") == "September"
        assert extract_month("during August") == "August"

    def test_unknown_query(self):
        result = parse_query("What is the capital of France?")
        assert result["intent"] == "unknown"

    def test_empty_query(self):
        result = parse_query("")
        assert result["intent"] == "unknown"
        assert result["entities"]["person_name"] is None
