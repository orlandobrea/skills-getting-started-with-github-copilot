"""
Comprehensive test suite for Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def fresh_activities():
    """Reset activities to a known state before each test"""
    # Store original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield activities
    
    # Restore original state after test
    for name, details in original_activities.items():
        activities[name]["participants"] = details["participants"].copy()


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity_data in activities_data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
    
    def test_get_activities_participants_is_list(self, client):
        """Test that participants field is a list"""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity_data in activities_data.items():
            assert isinstance(activity_data["participants"], list)
    
    def test_get_activities_has_chess_club(self, client):
        """Test that Chess Club activity exists"""
        response = client.get("/activities")
        activities_data = response.json()
        assert "Chess Club" in activities_data


class TestSignupForActivity:
    """Tests for POST /activities/{activity}/signup endpoint"""
    
    def test_signup_new_student_success(self, client, fresh_activities):
        """Test successful signup of a new student"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "message" in response.json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_returns_success_message(self, client, fresh_activities):
        """Test that signup returns a success message"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_already_registered(self, client, fresh_activities):
        """Test signup fails if student already registered"""
        # Student is already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_multiple_students_same_activity(self, client, fresh_activities):
        """Test multiple students can sign up for same activity"""
        student1 = "student1@mergington.edu"
        student2 = "student2@mergington.edu"
        
        response1 = client.post(
            f"/activities/Chess Club/signup?email={student1}"
        )
        response2 = client.post(
            f"/activities/Chess Club/signup?email={student2}"
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert student1 in activities["Chess Club"]["participants"]
        assert student2 in activities["Chess Club"]["participants"]
    
    def test_signup_student_multiple_activities(self, client, fresh_activities):
        """Test student can sign up for multiple activities"""
        email = "versatile@mergington.edu"
        
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        response2 = client.post(
            f"/activities/Art Club/signup?email={email}"
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Art Club"]["participants"]
    
    def test_signup_with_special_characters_in_email(self, client, fresh_activities):
        """Test signup with email containing special characters"""
        from urllib.parse import quote
        email = "test+tag@mergington.edu"
        response = client.post(
            f"/activities/Chess Club/signup?email={quote(email)}"
        )
        assert response.status_code == 200
        assert email in activities["Chess Club"]["participants"]
    
    def test_signup_updates_participant_count(self, client, fresh_activities):
        """Test that signup updates the participant count"""
        activity_name = "Drama Club"
        initial_count = len(activities[activity_name]["participants"])
        
        response = client.post(
            f"/activities/{activity_name}/signup?email=newdramastar@mergington.edu"
        )
        
        assert response.status_code == 200
        new_count = len(activities[activity_name]["participants"])
        assert new_count == initial_count + 1


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity}/unregister endpoint"""
    
    def test_unregister_success(self, client, fresh_activities):
        """Test successful unregistration of a student"""
        email = "michael@mergington.edu"
        initial_count = len(activities["Chess Club"]["participants"])
        
        response = client.post(
            f"/activities/Chess Club/unregister?email={email}"
        )
        
        assert response.status_code == 200
        assert email not in activities["Chess Club"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == initial_count - 1
    
    def test_unregister_returns_success_message(self, client, fresh_activities):
        """Test that unregister returns a success message"""
        email = "daniel@mergington.edu"
        response = client.post(
            f"/activities/Chess Club/unregister?email={email}"
        )
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_email_not_registered(self, client, fresh_activities):
        """Test unregister fails if student not registered"""
        email = "notregistered@mergington.edu"
        response = client.post(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_then_signup_again(self, client, fresh_activities):
        """Test student can unregister and sign up again"""
        email = "michael@mergington.edu"
        
        # Unregister
        response1 = client.post(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response1.status_code == 200
        assert email not in activities["Chess Club"]["participants"]
        
        # Sign up again
        response2 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response2.status_code == 200
        assert email in activities["Chess Club"]["participants"]
    
    def test_unregister_multiple_students(self, client, fresh_activities):
        """Test unregistering multiple students"""
        activity = "Chess Club"
        emails = list(activities[activity]["participants"])
        
        for email in emails:
            response = client.post(
                f"/activities/{activity}/unregister?email={email}"
            )
            assert response.status_code == 200
        
        assert len(activities[activity]["participants"]) == 0
    
    def test_unregister_with_special_characters_in_email(self, client, fresh_activities):
        """Test unregister with special characters in email"""
        email = "test+tag@mergington.edu"
        
        # First sign up
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Then unregister
        response = client.post(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200
        assert email not in activities["Chess Club"]["participants"]


class TestEdgeCases:
    """Tests for edge cases and complex scenarios"""
    
    def test_activity_at_capacity(self, client, fresh_activities):
        """Test that we can sign up students even if near capacity"""
        # This tests the current behavior - the API doesn't enforce capacity limits yet
        activity_name = "Chess Club"
        activities[activity_name]["max_participants"] = 2
        
        # Should still allow signup even with 2 participants
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
    
    def test_signup_unregister_signup_cycle(self, client, fresh_activities):
        """Test signup -> unregister -> signup cycle"""
        email = "cycletest@mergington.edu"
        activity = "Art Club"
        
        # Signup
        r1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert r1.status_code == 200
        assert email in activities[activity]["participants"]
        
        # Unregister
        r2 = client.post(f"/activities/{activity}/unregister?email={email}")
        assert r2.status_code == 200
        assert email not in activities[activity]["participants"]
        
        # Signup again
        r3 = client.post(f"/activities/{activity}/signup?email={email}")
        assert r3.status_code == 200
        assert email in activities[activity]["participants"]
    
    def test_concurrent_operations_on_different_activities(self, client, fresh_activities):
        """Test operations on different activities don't interfere"""
        email1 = "user1@mergington.edu"
        email2 = "user2@mergington.edu"
        
        # User1 signs up for Chess Club
        r1 = client.post(f"/activities/Chess Club/signup?email={email1}")
        assert r1.status_code == 200
        
        # User2 signs up for Art Club
        r2 = client.post(f"/activities/Art Club/signup?email={email2}")
        assert r2.status_code == 200
        
        # Verify they're in their respective activities
        assert email1 in activities["Chess Club"]["participants"]
        assert email2 in activities["Art Club"]["participants"]
        assert email1 not in activities["Art Club"]["participants"]
        assert email2 not in activities["Chess Club"]["participants"]
    
    def test_root_endpoint_redirect(self, client):
        """Test that root endpoint redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
    
    def test_activities_initial_state_preserved(self, client, fresh_activities):
        """Test that initial participant data is preserved"""
        response = client.get("/activities")
        data = response.json()
        
        # Check that initial participants are present
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]
