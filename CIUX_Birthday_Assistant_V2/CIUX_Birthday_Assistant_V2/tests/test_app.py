"""
test_app.py - Integration Tests for Flask Endpoints (app.py).

Verifies GET /, GET /health, POST /chat, input validation, and Port 5002 configuration.
"""

import pytest
from app import app
from config import PORT


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestAppEndpoints:
    """Test suite for Flask routes."""

    def test_index_route(self, client):
        response = client.get("/")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "CIUX Birthday Assistant" in html
        assert "Port 5002" in html

    def test_health_route(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["port"] == PORT
        assert data["port"] == 5002
        assert data["dataset_records"] > 0

    def test_chat_valid_query(self, client):
        response = client.post("/chat", json={"message": "Show birthdays in September"})
        assert response.status_code == 200
        data = response.get_json()
        assert "answer" in data
        assert "debug" in data
        assert data["debug"]["intent"] == "birthday_search"
        assert data["debug"]["entities"]["month"] == "September"

    def test_chat_person_birthday(self, client):
        response = client.post("/chat", json={"message": "When is Rahul's birthday?"})
        assert response.status_code == 200
        data = response.get_json()
        assert "Rahul Patil" in data["answer"]
        assert data["debug"]["intent"] == "person_birthday"

    def test_chat_person_location(self, client):
        response = client.post("/chat", json={"message": "Where does Rahul live?"})
        assert response.status_code == 200
        data = response.get_json()
        assert "Bengaluru" in data["answer"]
        assert data["debug"]["intent"] == "person_place"

    def test_chat_empty_query(self, client):
        response = client.post("/chat", json={"message": "   "})
        assert response.status_code == 400
        data = response.get_json()
        assert "answer" in data
