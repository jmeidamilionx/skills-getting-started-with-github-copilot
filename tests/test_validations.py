"""Tests for validation and edge cases."""

import pytest
from urllib.parse import quote


class TestActivityNameValidation:
    """Tests for activity name handling."""

    def test_signup_case_sensitive_activity_names(self, test_app, sample_activities):
        """Test that activity names are case-sensitive."""
        # Arrange
        email = "student@mergington.edu"
        correct_name = "Chess Club"
        wrong_case = "chess club"

        # Act
        response = test_app.post(
            f"/activities/{wrong_case}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert email not in sample_activities[correct_name]["participants"]

    def test_signup_with_special_characters_in_activity_name(self, test_app, sample_activities):
        """Test URL encoding of activity names with special characters."""
        # Arrange
        email = "student@mergington.edu"
        activity = "Programming Class"

        # Act - Activity name should be URL encoded
        response = test_app.post(
            f"/activities/Programming%20Class/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert email in sample_activities[activity]["participants"]

    def test_remove_participant_category_name_case_sensitive(self, test_app, sample_activities):
        """Test that activity names are case-sensitive in delete endpoint."""
        # Arrange
        email = "existing@mergington.edu"
        wrong_case = "chess club"

        # Act
        response = test_app.delete(
            f"/activities/{wrong_case}/participants/{email}"
        )

        # Assert
        assert response.status_code == 404


class TestEmailValidation:
    """Tests for email handling."""

    def test_signup_with_various_email_formats(self, test_app, sample_activities):
        """Test that various valid email formats are accepted."""
        # Arrange
        activity = "Programming Class"
        valid_emails = [
            "student@mergington.edu",
            "first.last@mergington.edu",
            "student+tag@mergington.edu",
            "student_123@mergington.edu"
        ]

        # Act & Assert
        for email in valid_emails:
            response = test_app.post(
                f"/activities/{activity}/signup?email={quote(email)}"
            )
            assert response.status_code == 200
            assert email in sample_activities[activity]["participants"]
            # Clean up for next iteration
            sample_activities[activity]["participants"].remove(email)

    def test_signup_preserves_email_case(self, test_app, sample_activities):
        """Test that email case is preserved as provided."""
        # Arrange
        email_mixed = "Student@Mergington.edu"
        activity = "Programming Class"

        # Act
        response = test_app.post(
            f"/activities/{activity}/signup?email={quote(email_mixed)}"
        )

        # Assert
        assert response.status_code == 200
        # Stored email should preserve the case provided
        assert email_mixed in sample_activities[activity]["participants"]

    def test_remove_participant_with_url_encoded_email(self, test_app, sample_activities):
        """Test that URL encoding works for email addresses."""
        # Arrange
        email = "student.name@mergington.edu"
        activity = "Chess Club"
        sample_activities[activity]["participants"].append(email)

        # Act
        response = test_app.delete(
            f"/activities/{activity}/participants/student.name@mergington.edu"
        )

        # Assert
        assert response.status_code == 200
        assert email not in sample_activities[activity]["participants"]


class TestParticipantCountValidation:
    """Tests for participant count and list integrity."""

    def test_max_participants_field_is_integer(self, test_app, sample_activities):
        """Test that max_participants is an integer."""
        # Arrange
        # Act
        response = test_app.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["max_participants"], int)
            assert activity_data["max_participants"] > 0

    def test_participants_list_maintains_order(self, test_app, sample_activities):
        """Test that participants list maintains insertion order."""
        # Arrange
        activity = "Programming Class"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]

        # Act
        for email in emails:
            test_app.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        response = test_app.get("/activities")
        data = response.json()
        participants = data[activity]["participants"]
        assert participants == emails

    def test_no_duplicate_participants_in_list(self, test_app, sample_activities):
        """Test that the same participant doesn't appear twice in the list."""
        # Arrange
        email = "student1@mergington.edu"
        activity = "Gym Class"

        # Act - Try to sign up twice (second should fail)
        test_app.post(f"/activities/{activity}/signup?email={email}")
        response = test_app.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 400
        participant_count = sample_activities[activity]["participants"].count(email)
        assert participant_count == 1  # Only appears once


class TestEmptyActivityHandling:
    """Tests for activities with no participants."""

    def test_empty_activity_returns_empty_list(self, test_app, sample_activities):
        """Test that activities with no participants return an empty list."""
        # Arrange
        activity = "Programming Class"
        assert len(sample_activities[activity]["participants"]) == 0

        # Act
        response = test_app.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert data[activity]["participants"] == []

    def test_activity_becomes_empty_after_removal(self, test_app, sample_activities):
        """Test that activity participant list becomes empty after removing only member."""
        # Arrange
        email = "existing@mergington.edu"
        activity = "Chess Club"
        sample_activities[activity]["participants"] = [email]

        # Act
        response = test_app.delete(
            f"/activities/{activity}/participants/{email}"
        )

        # Assert
        assert response.status_code == 200
        assert sample_activities[activity]["participants"] == []
