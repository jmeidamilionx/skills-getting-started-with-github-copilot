"""Pytest configuration and fixtures for the API tests."""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def test_app():
    """Provide a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_activities():
    """
    Reset activities to a known state before each test.
    Provides clean test data for isolation.
    """
    # Store original activities
    original = activities.copy()
    
    # Reset to test data
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["existing@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": []
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["student1@mergington.edu", "student2@mergington.edu"]
        }
    })
    
    # Yield for test execution
    yield activities
    
    # Restore original activities after test
    activities.clear()
    activities.update(original)
