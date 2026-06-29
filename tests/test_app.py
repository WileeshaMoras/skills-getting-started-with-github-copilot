from urllib.parse import quote

from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


def test_remove_participant_from_activity():
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    original_participants = list(activities[activity_name]["participants"])

    try:
        response = client.delete(f"/activities/{quote(activity_name)}/participants/{quote(email)}")

        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]
    finally:
        activities[activity_name]["participants"] = original_participants
