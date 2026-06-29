"""
Comprehensive test suite for the Mergington High School Activity API.

Tests follow the Arrange-Act-Assert (AAA) pattern for clarity and maintainability.
- Arrange: Set up test data and initial conditions
- Act: Execute the API call being tested
- Assert: Verify the response and side effects
"""

from urllib.parse import quote

from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


# ============================================================================
# GET / (Redirect to static index)
# ============================================================================

def test_root_endpoint_redirects_to_static():
    """Arrange: Initialize client
    Act: Call GET /
    Assert: Verify redirect to /static/index.html"""
    # Arrange
    # (client is already initialized globally)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


# ============================================================================
# GET /activities
# ============================================================================

def test_get_all_activities_returns_9_activities():
    """Arrange: Client ready
    Act: Call GET /activities
    Assert: Verify all 9 activities are returned"""
    # Arrange
    expected_activity_names = {
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Basketball Team",
        "Soccer Practice",
        "Art Club",
        "Drama Club",
        "Robotics Club",
        "Debate Team"
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    returned_activities = response.json()
    assert len(returned_activities) == 9
    assert set(returned_activities.keys()) == expected_activity_names


def test_get_activities_response_structure():
    """Arrange: Client ready
    Act: Call GET /activities
    Assert: Verify response structure includes required fields"""
    # Arrange
    required_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities_data = response.json()
    for activity_name, activity_data in activities_data.items():
        assert set(activity_data.keys()) >= required_fields, \
            f"Activity '{activity_name}' missing required fields"


def test_get_activities_participants_are_lists():
    """Arrange: Client ready
    Act: Call GET /activities
    Assert: Verify participants field is a list for all activities"""
    # Arrange
    # (activities structure known)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities_data = response.json()
    for activity_name, activity_data in activities_data.items():
        assert isinstance(activity_data["participants"], list), \
            f"Activity '{activity_name}' participants is not a list"


# ============================================================================
# POST /activities/{activity_name}/signup
# ============================================================================

def test_signup_valid_email_adds_participant():
    """Arrange: Pick activity with participant slots, prepare test email
    Act: POST signup with valid email
    Assert: Verify email added to participants and success message returned"""
    # Arrange
    activity_name = "Programming Class"
    test_email = "test.signup@example.com"
    original_participants = list(activities[activity_name]["participants"])

    try:
        # Act
        response = client.post(
            f"/activities/{quote(activity_name)}/signup",
            params={"email": test_email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {test_email} for {activity_name}"
        assert test_email in activities[activity_name]["participants"]
    finally:
        # Cleanup: Restore original state
        activities[activity_name]["participants"] = original_participants


def test_signup_duplicate_email_fails():
    """Arrange: Pick activity with existing participant
    Act: POST signup with email already in activity
    Assert: Verify 400 error and participant list unchanged"""
    # Arrange
    activity_name = "Chess Club"
    duplicate_email = "michael@mergington.edu"  # Already in Chess Club
    original_participants = list(activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": duplicate_email}
    )

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]
    assert activities[activity_name]["participants"] == original_participants


def test_signup_nonexistent_activity_returns_404():
    """Arrange: Prepare nonexistent activity name
    Act: POST signup for activity that doesn't exist
    Assert: Verify 404 error"""
    # Arrange
    nonexistent_activity = "Nonexistent Activity"
    test_email = "test@example.com"

    # Act
    response = client.post(
        f"/activities/{quote(nonexistent_activity)}/signup",
        params={"email": test_email}
    )

    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_signup_missing_email_parameter_fails():
    """Arrange: Prepare POST without email parameter
    Act: POST signup without email query param
    Assert: Verify validation error (422)"""
    # Arrange
    activity_name = "Art Club"

    # Act
    response = client.post(f"/activities/{quote(activity_name)}/signup")

    # Assert
    assert response.status_code == 422  # Unprocessable Entity (validation error)
    assert "email" in response.json()["detail"][0]["loc"]


def test_signup_with_spaces_in_activity_name():
    """Arrange: Pick activity with spaces, prepare valid email
    Act: POST signup for activity with spaces (URL encoded)
    Assert: Verify successful signup"""
    # Arrange
    activity_name = "Basketball Team"
    test_email = "basketball.fan@example.com"
    original_participants = list(activities[activity_name]["participants"])

    try:
        # Act
        response = client.post(
            f"/activities/{quote(activity_name)}/signup",
            params={"email": test_email}
        )

        # Assert
        assert response.status_code == 200
        assert test_email in activities[activity_name]["participants"]
    finally:
        # Cleanup
        activities[activity_name]["participants"] = original_participants


# ============================================================================
# DELETE /activities/{activity_name}/participants/{email}
# ============================================================================

def test_remove_participant_from_activity():
    """Arrange: Pick activity with participant to remove
    Act: DELETE participant from activity
    Assert: Verify participant removed and success message returned"""
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    original_participants = list(activities[activity_name]["participants"])

    try:
        # Act
        response = client.delete(
            f"/activities/{quote(activity_name)}/participants/{quote(email)}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]
    finally:
        # Cleanup: Restore original state
        activities[activity_name]["participants"] = original_participants


def test_remove_nonexistent_participant_returns_404():
    """Arrange: Prepare email not in activity
    Act: DELETE nonexistent participant from activity
    Assert: Verify 404 error and participant list unchanged"""
    # Arrange
    activity_name = "Drama Club"
    nonexistent_email = "nonexistent@example.com"
    original_participants = list(activities[activity_name]["participants"])

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/participants/{quote(nonexistent_email)}"
    )

    # Assert
    assert response.status_code == 404
    assert "Participant not found" in response.json()["detail"]
    assert activities[activity_name]["participants"] == original_participants


def test_remove_participant_from_nonexistent_activity_returns_404():
    """Arrange: Prepare nonexistent activity
    Act: DELETE participant from activity that doesn't exist
    Assert: Verify 404 error"""
    # Arrange
    nonexistent_activity = "Nonexistent Activity"
    test_email = "test@example.com"

    # Act
    response = client.delete(
        f"/activities/{quote(nonexistent_activity)}/participants/{quote(test_email)}"
    )

    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_remove_participant_with_special_characters_in_email():
    """Arrange: Add participant with special chars in email, prepare to remove
    Act: DELETE participant with special chars (URL encoded)
    Assert: Verify successful removal"""
    # Arrange
    activity_name = "Robotics Club"
    email_with_plus = "student+robotics@example.com"
    original_participants = list(activities[activity_name]["participants"])

    try:
        # Add the special email first
        activities[activity_name]["participants"].append(email_with_plus)

        # Act
        response = client.delete(
            f"/activities/{quote(activity_name)}/participants/{quote(email_with_plus)}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email_with_plus} from {activity_name}"
        assert email_with_plus not in activities[activity_name]["participants"]
    finally:
        # Cleanup
        activities[activity_name]["participants"] = original_participants


def test_remove_last_participant_from_activity():
    """Arrange: Create activity with single participant and remove them
    Act: DELETE the only participant from activity
    Assert: Verify successful removal, activity now has empty participants list"""
    # Arrange
    activity_name = "Debate Team"
    email_to_remove = "sophia@mergington.edu"
    original_participants = list(activities[activity_name]["participants"])

    try:
        # Make this the only participant (temporarily)
        activities[activity_name]["participants"] = [email_to_remove]

        # Act
        response = client.delete(
            f"/activities/{quote(activity_name)}/participants/{quote(email_to_remove)}"
        )

        # Assert
        assert response.status_code == 200
        assert len(activities[activity_name]["participants"]) == 0
    finally:
        # Cleanup
        activities[activity_name]["participants"] = original_participants
