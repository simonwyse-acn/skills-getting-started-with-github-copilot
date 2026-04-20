"""
FastAPI Tests for Mergington High School Activities API

Uses AAA (Arrange-Act-Assert) pattern for all tests.
"""

import pytest


class TestGetRoot:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index_html(self, client):
        """
        Arrange: No setup needed
        Act: Make GET request to /
        Assert: Should redirect to /static/index.html
        """
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities_returns_dict(self, client):
        """
        Arrange: No setup needed - activities already populated
        Act: Make GET request to /activities
        Assert: Should return all activities as a dictionary
        """
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_activities_contains_all_nine_activities(self, client):
        """
        Arrange: No setup needed
        Act: Make GET request to /activities
        Assert: Should contain all 9 hardcoded activities
        """
        response = client.get("/activities")
        data = response.json()
        expected_activities = {
            "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
            "Tennis Club", "Art Studio", "Drama Club", "Debate Club", "Science Club"
        }
        assert set(data.keys()) == expected_activities

    def test_get_activity_structure_is_valid(self, client):
        """
        Arrange: No setup needed
        Act: Make GET request to /activities
        Assert: Each activity should have required fields
        """
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_contains_initial_participants(self, client):
        """
        Arrange: No setup needed
        Act: Make GET request to /activities
        Assert: Activities should contain initial participant data
        """
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestPostSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self, client):
        """
        Arrange: Prepare a new participant email
        Act: Make POST request to sign up for an activity
        Assert: Should return success message and add participant
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={new_email}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert new_email in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """
        Arrange: Prepare a new participant email
        Act: Sign up participant, then fetch activities
        Assert: New participant should appear in participants list
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"

        # Act
        client.post(f"/activities/{activity_name}/signup?email={new_email}")
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert new_email in data["Chess Club"]["participants"]

    def test_signup_duplicate_participant_returns_400(self, client):
        """
        Arrange: Select a participant already signed up
        Act: Attempt to sign up the same participant again
        Assert: Should return 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={existing_email}"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]

    def test_signup_to_nonexistent_activity_returns_404(self, client):
        """
        Arrange: Prepare a valid email and invalid activity name
        Act: Attempt to sign up to non-existent activity
        Assert: Should return 404 error
        """
        # Arrange
        fake_activity = "Fake Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{fake_activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_with_invalid_email_format_returns_400(self, client):
        """
        Arrange: Prepare an invalid email format
        Act: Attempt to sign up with invalid email
        Assert: Should return 400 error for invalid email
        """
        # Arrange
        activity_name = "Chess Club"
        invalid_email = "not-an-email"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={invalid_email}"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Invalid email format" in data["detail"]

    def test_signup_with_email_missing_domain_returns_400(self, client):
        """
        Arrange: Prepare an email missing domain
        Act: Attempt to sign up with incomplete email
        Assert: Should return 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        invalid_email = "student@"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={invalid_email}"
        )

        # Assert
        assert response.status_code == 400

    def test_signup_with_email_missing_at_symbol_returns_400(self, client):
        """
        Arrange: Prepare an email missing @ symbol
        Act: Attempt to sign up without @ symbol
        Assert: Should return 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        invalid_email = "studentmergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={invalid_email}"
        )

        # Assert
        assert response.status_code == 400

    def test_signup_then_resignup_works_after_unregister(self, client):
        """
        Arrange: A participant signs up, then unregisters
        Act: Then attempt to sign up again
        Assert: Should succeed and add participant back
        """
        # Arrange
        activity_name = "Chess Club"
        test_email = "resigner@mergington.edu"

        # Act - Sign up
        client.post(f"/activities/{activity_name}/signup?email={test_email}")

        # Unregister
        client.delete(f"/activities/{activity_name}/signup?email={test_email}")

        # Sign up again
        response = client.post(
            f"/activities/{activity_name}/signup?email={test_email}"
        )

        # Assert
        assert response.status_code == 200
        get_response = client.get("/activities")
        assert test_email in get_response.json()["Chess Club"]["participants"]


class TestDeleteSignup:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_existing_participant_success(self, client):
        """
        Arrange: Select an existing participant
        Act: Make DELETE request to unregister
        Assert: Should return success message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_removes_participant_from_activity(self, client):
        """
        Arrange: Select an existing participant
        Act: Unregister participant, then fetch activities
        Assert: Participant should not appear in list
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        client.delete(f"/activities/{activity_name}/signup?email={email}")
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert email not in data["Chess Club"]["participants"]

    def test_unregister_not_signed_up_participant_returns_400(self, client):
        """
        Arrange: Select an email not signed up for the activity
        Act: Attempt to unregister
        Assert: Should return 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        not_signed_up_email = "never_signed_up@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={not_signed_up_email}"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Student not signed up" in data["detail"]

    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        """
        Arrange: Prepare a valid email and invalid activity name
        Act: Attempt to unregister from non-existent activity
        Assert: Should return 404 error
        """
        # Arrange
        fake_activity = "Fake Activity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{fake_activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_with_invalid_email_format_returns_400(self, client):
        """
        Arrange: Prepare an invalid email format
        Act: Attempt to unregister with invalid email
        Assert: Should return 400 error for invalid email
        """
        # Arrange
        activity_name = "Chess Club"
        invalid_email = "not-an-email"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={invalid_email}"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Invalid email format" in data["detail"]

    def test_unregister_twice_returns_400_on_second_attempt(self, client):
        """
        Arrange: A participant is signed up
        Act: Unregister once (success), then unregister again
        Assert: Second attempt should return 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act - First unregister
        response1 = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Second unregister attempt
        response2 = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 400
        assert "Student not signed up" in response2.json()["detail"]

    def test_unregister_updates_participant_count(self, client):
        """
        Arrange: Know initial participant count
        Act: Unregister one participant
        Assert: Participant count should decrease by 1
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Chess Club"]["participants"])

        # Act
        client.delete(f"/activities/{activity_name}/signup?email={email}")
        final_response = client.get("/activities")
        final_count = len(final_response.json()["Chess Club"]["participants"])

        # Assert
        assert final_count == initial_count - 1
