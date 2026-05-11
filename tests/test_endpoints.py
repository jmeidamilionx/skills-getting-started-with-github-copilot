"""Integration and unit tests for the Mergington High School Activities API endpoints."""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, test_app, sample_activities):
        """Test that GET /activities returns all activities."""
        # Arrange
        expected_count = 3

        # Act
        response = test_app.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == expected_count
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_response_structure(self, test_app, sample_activities):
        """Test that each activity has the correct structure."""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = test_app.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in data.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_data, dict)
            assert set(activity_data.keys()) == required_fields
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_includes_participants(self, test_app, sample_activities):
        """Test that activities include existing participants."""
        # Arrange
        # Act
        response = test_app.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert "existing@mergington.edu" in data["Chess Club"]["participants"]
        assert len(data["Gym Class"]["participants"]) == 2


class TestRootRedirect:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_static_index(self, test_app, sample_activities):
        """Test that GET / redirects to /static/index.html."""
        # Arrange
        # Act
        response = test_app.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, test_app, sample_activities):
        """Test successful signup for an activity."""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Programming Class"

        # Act
        response = test_app.post(
            f"/activities/{activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == f"Signed up {email} for {activity}"
        assert email in sample_activities[activity]["participants"]

    def test_signup_duplicate_email_error(self, test_app, sample_activities):
        """Test that signing up twice with same email is rejected."""
        # Arrange
        email = "existing@mergington.edu"
        activity = "Chess Club"

        # Act
        response = test_app.post(
            f"/activities/{activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_error(self, test_app, sample_activities):
        """Test that signing up for nonexistent activity returns 404."""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Nonexistent Activity"

        # Act
        response = test_app.post(
            f"/activities/{activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_adds_to_participants_list(self, test_app, sample_activities):
        """Test that signup correctly adds participant to activity."""
        # Arrange
        email = "student3@mergington.edu"
        activity = "Gym Class"
        initial_count = len(sample_activities[activity]["participants"])

        # Act
        response = test_app.post(
            f"/activities/{activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert len(sample_activities[activity]["participants"]) == initial_count + 1
        assert email in sample_activities[activity]["participants"]


class TestRemoveParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint."""

    def test_remove_participant_success(self, test_app, sample_activities):
        """Test successful removal of a participant from an activity."""
        # Arrange
        email = "existing@mergington.edu"
        activity = "Chess Club"
        initial_count = len(sample_activities[activity]["participants"])

        # Act
        response = test_app.delete(
            f"/activities/{activity}/participants/{email}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == f"Removed {email} from {activity}"
        assert email not in sample_activities[activity]["participants"]
        assert len(sample_activities[activity]["participants"]) == initial_count - 1

    def test_remove_participant_not_registered_error(self, test_app, sample_activities):
        """Test that removing unregistered participant returns 404."""
        # Arrange
        email = "notregistered@mergington.edu"
        activity = "Chess Club"

        # Act
        response = test_app.delete(
            f"/activities/{activity}/participants/{email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not registered" in data["detail"].lower()

    def test_remove_participant_nonexistent_activity_error(self, test_app, sample_activities):
        """Test that removing from nonexistent activity returns 404."""
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"

        # Act
        response = test_app.delete(
            f"/activities/{activity}/participants/{email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_remove_leaves_other_participants(self, test_app, sample_activities):
        """Test that removing a participant doesn't affect others."""
        # Arrange
        email_to_remove = "student1@mergington.edu"
        email_to_keep = "student2@mergington.edu"
        activity = "Gym Class"

        # Act
        response = test_app.delete(
            f"/activities/{activity}/participants/{email_to_remove}"
        )

        # Assert
        assert response.status_code == 200
        assert email_to_remove not in sample_activities[activity]["participants"]
        assert email_to_keep in sample_activities[activity]["participants"]
