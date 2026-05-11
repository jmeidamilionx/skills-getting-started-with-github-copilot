"""Integration tests for complex workflows and multi-step scenarios."""

import pytest
from copy import deepcopy


class TestSignupAndRemovalWorkflow:
    """Tests for signup followed by removal workflows."""

    def test_signup_then_remove_workflow(self, test_app, sample_activities):
        """Test complete workflow: signup, verify, then remove."""
        # Arrange
        email = "workflow@mergington.edu"
        activity = "Programming Class"

        # Act - Sign up
        signup_response = test_app.post(
            f"/activities/{activity}/signup?email={email}"
        )

        # Assert signup
        assert signup_response.status_code == 200
        assert email in sample_activities[activity]["participants"]

        # Act - Remove
        remove_response = test_app.delete(
            f"/activities/{activity}/participants/{email}"
        )

        # Assert removal
        assert remove_response.status_code == 200
        assert email not in sample_activities[activity]["participants"]

    def test_signup_verify_then_remove(self, test_app, sample_activities):
        """Test signup, get activities to verify, then remove."""
        # Arrange
        email = "verify@mergington.edu"
        activity = "Gym Class"

        # Act - Sign up
        test_app.post(f"/activities/{activity}/signup?email={email}")

        # Act - Verify via GET
        get_response = test_app.get("/activities")
        data = get_response.json()

        # Assert verification
        assert email in data[activity]["participants"]

        # Act - Remove
        test_app.delete(f"/activities/{activity}/participants/{email}")

        # Assert removal
        get_response = test_app.get("/activities")
        data = get_response.json()
        assert email not in data[activity]["participants"]


class TestMultipleStudentSignups:
    """Tests for multiple students signing up for same activity."""

    def test_multiple_students_signup_same_activity(self, test_app, sample_activities):
        """Test that multiple students can sign up for the same activity."""
        # Arrange
        activity = "Programming Class"
        students = [
            "alice@mergington.edu",
            "bob@mergington.edu",
            "charlie@mergington.edu"
        ]

        # Act
        for student in students:
            response = test_app.post(
                f"/activities/{activity}/signup?email={student}"
            )
            assert response.status_code == 200

        # Assert
        response = test_app.get("/activities")
        data = response.json()
        participants = data[activity]["participants"]
        assert len(participants) == len(students)
        for student in students:
            assert student in participants

    def test_multiple_students_signup_different_activities(self, test_app, sample_activities):
        """Test that same student can verify enrollment in multiple activities."""
        # Arrange
        student = "multi@mergington.edu"
        activities = ["Chess Club", "Programming Class", "Gym Class"]

        # Act
        for activity in activities:
            response = test_app.post(
                f"/activities/{activity}/signup?email={student}"
            )
            assert response.status_code == 200

        # Assert
        response = test_app.get("/activities")
        data = response.json()
        for activity in activities:
            assert student in data[activity]["participants"]

    def test_remove_one_student_from_activity_with_multiple(self, test_app, sample_activities):
        """Test removing a student doesn't affect others in same activity."""
        # Arrange
        activity = "Programming Class"
        to_remove = "remove_me@mergington.edu"
        to_keep = ["keep1@mergington.edu", "keep2@mergington.edu"]

        # Act - Sign up multiple
        test_app.post(f"/activities/{activity}/signup?email={to_remove}")
        for student in to_keep:
            test_app.post(f"/activities/{activity}/signup?email={student}")

        # Act - Remove one
        response = test_app.delete(
            f"/activities/{activity}/participants/{to_remove}"
        )

        # Assert
        assert response.status_code == 200
        response = test_app.get("/activities")
        data = response.json()
        participants = data[activity]["participants"]
        assert to_remove not in participants
        for student in to_keep:
            assert student in participants


class TestActivityStateManagement:
    """Tests for correct activity state management across operations."""

    def test_activity_state_after_signup(self, test_app, sample_activities):
        """Test that activity state is correctly updated after signup."""
        # Arrange
        email = "statecheck@mergington.edu"
        activity = "Programming Class"
        initial_data = deepcopy(sample_activities[activity])

        # Act
        test_app.post(f"/activities/{activity}/signup?email={email}")

        # Assert - Check all fields are preserved except participants
        activity_data = sample_activities[activity]
        assert activity_data["description"] == initial_data["description"]
        assert activity_data["schedule"] == initial_data["schedule"]
        assert activity_data["max_participants"] == initial_data["max_participants"]
        assert len(activity_data["participants"]) == len(initial_data["participants"]) + 1

    def test_other_activities_unaffected_by_signup(self, test_app, sample_activities):
        """Test that signup to one activity doesn't affect others."""
        # Arrange
        email = "isolated@mergington.edu"
        activities_list = ["Chess Club", "Programming Class", "Gym Class"]
        original_states = {
            activity: deepcopy(sample_activities[activity]["participants"])
            for activity in activities_list
        }

        # Act - Sign up to one activity
        test_app.post(f"/activities/Programming Class/signup?email={email}")

        # Assert - Only Programming Class should be affected
        for activity in activities_list:
            if activity == "Programming Class":
                assert email in sample_activities[activity]["participants"]
            else:
                assert sample_activities[activity]["participants"] == original_states[activity]

    def test_remove_restores_previous_state(self, test_app, sample_activities):
        """Test that removing a participant restores activity to previous state."""
        # Arrange
        email = "tempstudent@mergington.edu"
        activity = "Chess Club"
        initial_participants = sample_activities[activity]["participants"].copy()

        # Act - Sign up then remove
        test_app.post(f"/activities/{activity}/signup?email={email}")
        test_app.delete(f"/activities/{activity}/participants/{email}")

        # Assert
        assert sample_activities[activity]["participants"] == initial_participants


class TestErrorRecovery:
    """Tests for error recovery and state consistency."""

    def test_failed_signup_doesnt_add_participant(self, test_app, sample_activities):
        """Test that failed signup doesn't partially add participant."""
        # Arrange
        email = "duplicate@mergington.edu"
        activity = "Chess Club"
        sample_activities[activity]["participants"] = [email]
        initial_count = len(sample_activities[activity]["participants"])

        # Act
        response = test_app.post(
            f"/activities/{activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert len(sample_activities[activity]["participants"]) == initial_count
        assert sample_activities[activity]["participants"].count(email) == 1

    def test_failed_remove_doesnt_affect_participants(self, test_app, sample_activities):
        """Test that failed removal doesn't affect participant list."""
        # Arrange
        activity = "Chess Club"
        initial_participants = sample_activities[activity]["participants"].copy()

        # Act
        response = test_app.delete(
            f"/activities/{activity}/participants/nonexistent@mergington.edu"
        )

        # Assert
        assert response.status_code == 404
        assert sample_activities[activity]["participants"] == initial_participants

    def test_repeated_signup_attempts_fail_consistently(self, test_app, sample_activities):
        """Test that repeated signup attempts consistently fail."""
        # Arrange
        email = "retry@mergington.edu"
        activity = "Programming Class"

        # Act - First signup succeeds
        response1 = test_app.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response1.status_code == 200

        # Act - Repeated attempts should fail consistently
        response2 = test_app.post(
            f"/activities/{activity}/signup?email={email}"
        )
        response3 = test_app.post(
            f"/activities/{activity}/signup?email={email}"
        )

        # Assert
        assert response2.status_code == 400
        assert response3.status_code == 400
        assert sample_activities[activity]["participants"].count(email) == 1
