import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create an async test client for the FastAPI app"""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


class TestActivitiesAPI:
    """Test cases for the Activities API"""

    def test_root_redirect(self, client):
        """Test that root endpoint serves the static HTML file"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Mergington High School Activities" in response.text

    def test_get_activities(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200

        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0

        # Check that each activity has the required fields
        for name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)

    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        # Use an activity that exists and an email that's not signed up
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@example.com"
        )
        assert response.status_code == 200

        result = response.json()
        assert "message" in result
        assert "test@example.com" in result["message"]
        assert "Chess Club" in result["message"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonExistent/signup?email=test@example.com"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_already_signed_up(self, client):
        """Test signup when student is already signed up"""
        # First signup
        client.post("/activities/Chess%20Club/signup?email=duplicate@example.com")

        # Try to signup again
        response = client.post(
            "/activities/Chess%20Club/signup?email=duplicate@example.com"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_unregister_successful(self, client):
        """Test successful unregister from an activity"""
        # First signup
        client.post("/activities/Programming%20Class/signup?email=unregister@example.com")

        # Then unregister
        response = client.delete(
            "/activities/Programming%20Class/unregister?email=unregister@example.com"
        )
        assert response.status_code == 200

        result = response.json()
        assert "message" in result
        assert "unregister@example.com" in result["message"]
        assert "Programming Class" in result["message"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/NonExistent/unregister?email=test@example.com"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_signed_up(self, client):
        """Test unregister when student is not signed up"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=notsignedup@example.com"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_activities_data_integrity(self, client):
        """Test that activities data remains consistent"""
        # Get initial activities
        response = client.get("/activities")
        initial_activities = response.json()

        # Make some changes
        client.post("/activities/Gym%20Class/signup?email=integrity@example.com")
        client.delete("/activities/Gym%20Class/unregister?email=integrity@example.com")

        # Get activities again
        response = client.get("/activities")
        final_activities = response.json()

        # Data should be back to initial state (since we added and removed the same participant)
        assert initial_activities == final_activities