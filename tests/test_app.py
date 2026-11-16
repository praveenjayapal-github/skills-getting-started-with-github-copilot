import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_activity_name():
    name = "API Test Activity"
    previous_activity = activities.pop(name, None)
    activities[name] = {
        "description": "Test activity",
        "schedule": "Test schedule",
        "max_participants": 5,
        "participants": [],
    }

    yield name

    activities.pop(name, None)
    if previous_activity is not None:
        activities[name] = previous_activity


def test_root_redirects_to_web_app(client):
    # Arrange
    follow_redirects = False

    # Act
    response = client.get("/", follow_redirects=follow_redirects)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data_without_caching(
    client, test_activity_name
):
    # Arrange
    expected_participants = []

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert (
        response.json()[test_activity_name]["participants"]
        == expected_participants
    )


def test_signup_adds_participant(client, test_activity_name):
    # Arrange
    email = "student@example.com"

    # Act
    response = client.post(
        f"/activities/{test_activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {test_activity_name}"
    }
    assert activities[test_activity_name]["participants"] == [email]


def test_signup_rejects_duplicate_participant(client, test_activity_name):
    # Arrange
    email = "student@example.com"
    activities[test_activity_name]["participants"].append(email)

    # Act
    response = client.post(
        f"/activities/{test_activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert activities[test_activity_name]["participants"] == [email]


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    email = "student@example.com"
    unknown_activity = "Unknown Activity"

    # Act
    response = client.post(
        f"/activities/{unknown_activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404


def test_unregister_removes_participant(client, test_activity_name):
    # Arrange
    email = "student@example.com"
    activities[test_activity_name]["participants"] = [email, email]

    # Act
    response = client.delete(
        f"/activities/{test_activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert activities[test_activity_name]["participants"] == []
    assert response.json() == {
        "message": f"Unregistered {email} from {test_activity_name}"
    }


def test_unregister_returns_not_found_when_not_signed_up(
    client, test_activity_name
):
    # Arrange
    email = "student@example.com"

    # Act
    response = client.delete(
        f"/activities/{test_activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404


def test_unregister_returns_not_found_for_unknown_activity(client):
    # Arrange
    email = "student@example.com"
    unknown_activity = "Unknown Activity"

    # Act
    response = client.delete(
        f"/activities/{unknown_activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404


def test_activities_response_reflects_signup_immediately(
    client, test_activity_name
):
    # Arrange
    email = "student@example.com"
    signup_url = f"/activities/{test_activity_name}/signup"

    # Act
    signup_response = client.post(signup_url, params={"email": email})
    activities_response = client.get("/activities")

    # Assert
    assert signup_response.status_code == 200
    assert signup_response.json()["message"] == (
        f"Signed up {email} for {test_activity_name}"
    )
    assert activities_response.headers["cache-control"] == "no-store"
    assert email in activities_response.json()[test_activity_name]["participants"]
