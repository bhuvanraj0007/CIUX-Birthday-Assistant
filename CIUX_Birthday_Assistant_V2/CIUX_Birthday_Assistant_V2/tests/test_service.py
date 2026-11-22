"""
test_service.py - Unit Tests for Birthday Service (service.py).

Tests data filtering, birthday queries, date computations, location lookups,
and handling of missing/empty results.
"""

from datetime import date
import pytest
from service import BirthdayService
from config import EXCEL_PATH


@pytest.fixture
def service():
    """Initialize BirthdayService with actual dataset."""
    return BirthdayService(excel_path=EXCEL_PATH)


class TestBirthdayService:
    """Test suite for business logic in BirthdayService."""

    def test_dataset_loaded(self, service):
        assert not service.df.empty
        assert "Person_ID" in service.df.columns
        assert "Name" in service.df.columns
        assert "DOB_Formatted" in service.df.columns
        assert "Birth_Month" in service.df.columns

    def test_search_by_month(self, service):
        # September search
        results = service.search_birthdays(month="September")
        assert len(results) > 0
        for r in results:
            assert r["Birth_Month"] == 9

    def test_search_by_relationship(self, service):
        results = service.search_birthdays(relationship="nephew")
        assert len(results) > 0
        for r in results:
            assert "nephew" in r["Relationship"].lower()

    def test_search_by_name(self, service):
        results = service.search_birthdays(name="Rahul")
        assert len(results) >= 1
        rahul = results[0]
        assert "Rahul" in rahul["Name"]
        assert rahul["Person_ID"] == "P004"

    def test_search_by_person_id(self, service):
        results = service.search_birthdays(person_id="P004")
        assert len(results) == 1
        assert results[0]["Name"] == "Rahul Patil"

    def test_combined_search(self, service):
        # Nephews with birthday in September
        results = service.search_birthdays(month="September", relationship="nephew")
        assert len(results) > 0
        for r in results:
            assert r["Birth_Month"] == 9
            assert "nephew" in r["Relationship"].lower()

    def test_count_birthdays(self, service):
        total = service.count_birthdays()
        assert total == len(service.df)

        sep_count = service.count_birthdays(month="September")
        assert sep_count > 0
        assert sep_count < total

        nephew_oct_count = service.count_birthdays(month="October", relationship="nephew")
        assert isinstance(nephew_oct_count, int)

    def test_person_birthday_query(self, service):
        res = service.get_person_birthday(name="Rahul")
        assert "Rahul Patil" in res
        assert "2004-09-18" in res
        assert "P004" in res

    def test_person_location_query(self, service):
        res = service.get_person_location(name="Rahul")
        assert "Rahul Patil" in res
        assert "Bengaluru" in res

    def test_person_not_found(self, service):
        res = service.get_person_birthday(name="NonExistentNameXYZ")
        assert "No records found" in res

        loc = service.get_person_location(name="NonExistentNameXYZ")
        assert "No records found" in loc

    def test_upcoming_birthdays_fixed_date(self, service):
        # Use fixed reference date 2026-09-10
        # Rahul Patil's birthday is on Sept 18 (8 days later)
        ref = date(2026, 9, 10)
        upcoming = service.get_upcoming_birthdays(days=15, reference_date=ref)
        assert len(upcoming) > 0

        # Rahul should be among upcoming birthdays
        pids = [r["Person_ID"] for r in upcoming]
        assert "P004" in pids

        # Ensure sorted by Days_Until
        days = [r["Days_Until"] for r in upcoming]
        assert days == sorted(days)

    def test_tomorrow_birthdays_fixed_date(self, service):
        # Reference date Sept 17, 2026 -> tomorrow is Sept 18 (Rahul's birthday)
        ref = date(2026, 9, 17)
        tomorrow_list = service.get_tomorrow_birthdays(reference_date=ref)
        assert len(tomorrow_list) > 0
        pids = [r["Person_ID"] for r in tomorrow_list]
        assert "P004" in pids

    def test_process_nlu_query_routing(self, service):
        nlu_res = {
            "intent": "birthday_search",
            "entities": {
                "person_name": None,
                "person_id": None,
                "month": "September",
                "relationship": None,
                "relative_date": None
            }
        }
        answer = service.process_nlu_query(nlu_res)
        assert "September" in answer
        assert "P004" in answer
