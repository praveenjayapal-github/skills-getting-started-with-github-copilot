import unittest

from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)


class UnregisterActivityTests(unittest.TestCase):
    activity_name = "Unregister Test Activity"

    def tearDown(self):
        activities.pop(self.activity_name, None)

    def test_unregister_removes_participant(self):
        email = "student@example.com"
        activities[self.activity_name] = {
            "description": "Test activity",
            "schedule": "Test schedule",
            "max_participants": 5,
            "participants": [email, email],
        }

        response = client.delete(
            f"/activities/{self.activity_name}/signup",
            params={"email": email},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(activities[self.activity_name]["participants"], [])
        self.assertEqual(
            response.json(),
            {"message": f"Unregistered {email} from {self.activity_name}"},
        )

    def test_unregister_returns_not_found_when_not_signed_up(self):
        activities[self.activity_name] = {
            "description": "Test activity",
            "schedule": "Test schedule",
            "max_participants": 5,
            "participants": [],
        }

        response = client.delete(
            f"/activities/{self.activity_name}/signup",
            params={"email": "student@example.com"},
        )

        self.assertEqual(response.status_code, 404)

    def test_activities_response_reflects_signup_without_caching(self):
        email = "student@example.com"
        activities[self.activity_name] = {
            "description": "Test activity",
            "schedule": "Test schedule",
            "max_participants": 5,
            "participants": [],
        }

        signup_response = client.post(
            f"/activities/{self.activity_name}/signup",
            params={"email": email},
        )
        activities_response = client.get("/activities")

        self.assertEqual(signup_response.status_code, 200)
        self.assertEqual(activities_response.headers["cache-control"], "no-store")
        self.assertIn(
            email,
            activities_response.json()[self.activity_name]["participants"],
        )
