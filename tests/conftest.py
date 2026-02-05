"""
Global test configuration and fixtures for Duobingo API tests.

This module provides:
- TestClient for FastAPI app
- Authentication tokens for different user roles
- Test data fixtures (classrooms, modules, quizzes, questions)
- Mock services for testing different scenarios
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from jose import jwt

# Note: These imports will need to be adjusted once the actual app is implemented
# from app.main import app
# from app.core.config import settings
# from app.db.session import get_db
# from app.services.auth import auth_service


# =============================================================================
# TEST CONSTANTS
# =============================================================================

# Test user credentials (as specified in the problem statement)
TEST_USERS = {
    "admin": {
        "email": "admin@univ-rennes.fr",
        "password": "admin123",
        "role": "ADMIN",
        "name": "Admin User"
    },
    "prof_responsible": {
        "email": "house@univ-rennes.fr",
        "password": "prof123",
        "role": "TEACHER",
        "name": "Dr. House",
        "department": "Anatomie"
    },
    "prof_secondary": {
        "email": "wilson@univ-rennes.fr",
        "password": "prof123",
        "role": "TEACHER",
        "name": "Dr. Wilson",
        "department": "Anatomie"
    },
    "student1": {
        "email": "marie.martin@univ-rennes.fr",
        "password": "student123",
        "role": "STUDENT",
        "name": "Marie Martin",
        "level": "L1"
    },
    "student2": {
        "email": "jean.dupont@univ-rennes.fr",
        "password": "student123",
        "role": "STUDENT",
        "name": "Jean Dupont",
        "level": "L1"
    }
}

TEST_CLASSROOM_CODE = "ANAT26"

# JWT secret for test tokens (this should match the app config)
TEST_JWT_SECRET = "test_secret_key_for_testing_only"
TEST_JWT_ALGORITHM = "HS256"


# =============================================================================
# BASIC FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def test_db():
    """
    Create a test database for the entire test session.
    Uses SQLite in-memory database for speed.
    """
    # TODO: Implement once the app is available
    # from app.db.session import engine, Base
    # Base.metadata.create_all(bind=engine)
    # yield
    # Base.metadata.drop_all(bind=engine)
    pass


@pytest.fixture
def client(test_db):
    """
    FastAPI TestClient for making HTTP requests.
    
    Returns:
        TestClient: Configured test client
    """
    # TODO: Implement once the app is available
    # from fastapi.testclient import TestClient
    # from app.main import app
    # return TestClient(app)
    
    # Mock client for now - will be replaced with actual implementation
    class MockClient:
        def __init__(self):
            self.base_url = "http://testserver/api"
            
        def get(self, url, **kwargs):
            pass
        
        def post(self, url, **kwargs):
            pass
        
        def patch(self, url, **kwargs):
            pass
        
        def delete(self, url, **kwargs):
            pass
    
    return MockClient()


# =============================================================================
# AUTHENTICATION TOKEN FIXTURES
# =============================================================================

def create_test_token(user_data: Dict[str, Any], expired: bool = False) -> str:
    """
    Helper function to create a JWT token for testing.
    
    Args:
        user_data: User information to encode in token
        expired: Whether to create an expired token
        
    Returns:
        str: JWT token
    """
    payload = {
        "sub": user_data.get("id", "test-user-id"),
        "email": user_data["email"],
        "role": user_data["role"],
        "exp": datetime.utcnow() + timedelta(hours=-1 if expired else 24)
    }
    
    token = jwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)
    return token


@pytest.fixture
def admin_token() -> str:
    """
    JWT token for Admin user.
    
    Login with: admin@univ-rennes.fr / admin123
    
    Returns:
        str: Bearer token for admin
    """
    return create_test_token(TEST_USERS["admin"])


@pytest.fixture
def prof_responsible_token() -> str:
    """
    JWT token for Professor Responsible (main teacher of a classroom).
    
    Login with: house@univ-rennes.fr / prof123
    
    Returns:
        str: Bearer token for responsible professor
    """
    return create_test_token(TEST_USERS["prof_responsible"])


@pytest.fixture
def prof_secondary_token() -> str:
    """
    JWT token for Secondary Professor (additional teacher in a classroom).
    
    Login with: wilson@univ-rennes.fr / prof123
    
    Returns:
        str: Bearer token for secondary professor
    """
    return create_test_token(TEST_USERS["prof_secondary"])


@pytest.fixture
def student_token() -> str:
    """
    JWT token for Student 1.
    
    Login with: marie.martin@univ-rennes.fr / student123
    
    Returns:
        str: Bearer token for student
    """
    return create_test_token(TEST_USERS["student1"])


@pytest.fixture
def student2_token() -> str:
    """
    JWT token for Student 2.
    
    Login with: jean.dupont@univ-rennes.fr / student123
    
    Returns:
        str: Bearer token for second student
    """
    return create_test_token(TEST_USERS["student2"])


@pytest.fixture
def invalid_token() -> str:
    """
    Invalid/malformed JWT token for testing authentication failures.
    
    Returns:
        str: Invalid bearer token
    """
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbnZhbGlkIn0.invalid_signature"


@pytest.fixture
def expired_token() -> str:
    """
    Expired JWT token for testing token expiration.
    
    Returns:
        str: Expired bearer token
    """
    return create_test_token(TEST_USERS["student1"], expired=True)


# =============================================================================
# TEST DATA FIXTURES
# =============================================================================

@pytest.fixture
def classroom_id(client, prof_responsible_token) -> str:
    """
    UUID of a classroom created for tests.
    
    Creates a classroom with the responsible professor and returns its ID.
    
    Returns:
        str: UUID of the test classroom
    """
    # TODO: Implement once the app is available
    # response = client.post(
    #     "/api/classrooms",
    #     headers={"Authorization": f"Bearer {prof_responsible_token}"},
    #     json={"name": "Test Anatomie L1", "level": "L1"}
    # )
    # return response.json()["id"]
    return "test-classroom-id"


@pytest.fixture
def module_id(client, prof_responsible_token, classroom_id) -> str:
    """
    UUID of a module created for tests.
    
    Args:
        classroom_id: Parent classroom ID
        
    Returns:
        str: UUID of the test module
    """
    # TODO: Implement once the app is available
    # response = client.post(
    #     f"/api/classrooms/{classroom_id}/modules",
    #     headers={"Authorization": f"Bearer {prof_responsible_token}"},
    #     json={"name": "Test Module", "category": "Ostéologie"}
    # )
    # return response.json()["id"]
    return "test-module-id"


@pytest.fixture
def quiz_id(client, prof_responsible_token, module_id) -> str:
    """
    UUID of a quiz created for tests.
    
    Args:
        module_id: Parent module ID
        
    Returns:
        str: UUID of the test quiz
    """
    # TODO: Implement once the app is available
    # response = client.post(
    #     f"/api/modules/{module_id}/quizzes",
    #     headers={"Authorization": f"Bearer {prof_responsible_token}"},
    #     json={
    #         "title": "Test Quiz",
    #         "minScoreToUnlockNext": 15,
    #         "isActive": True
    #     }
    # )
    # return response.json()["id"]
    return "test-quiz-id"


@pytest.fixture
def question_id(client, prof_responsible_token, quiz_id) -> str:
    """
    UUID of a question created for tests.
    
    Args:
        quiz_id: Parent quiz ID
        
    Returns:
        str: UUID of the test question
    """
    # TODO: Implement once the app is available
    # response = client.post(
    #     f"/api/quizzes/{quiz_id}/questions",
    #     headers={"Authorization": f"Bearer {prof_responsible_token}"},
    #     json={
    #         "type": "QCM",
    #         "contentText": "Test question?",
    #         "options": [
    #             {"textChoice": "Answer A", "isCorrect": True},
    #             {"textChoice": "Answer B", "isCorrect": False}
    #         ]
    #     }
    # )
    # return response.json()["id"]
    return "test-question-id"


@pytest.fixture
def session_id(client, student_token, quiz_id) -> str:
    """
    UUID of a quiz session created for tests.
    
    Args:
        quiz_id: Quiz to start a session for
        
    Returns:
        str: UUID of the test session
    """
    # TODO: Implement once the app is available
    # response = client.post(
    #     "/api/sessions/start",
    #     headers={"Authorization": f"Bearer {student_token}"},
    #     json={"quizId": quiz_id}
    # )
    # return response.json()["sessionId"]
    return "test-session-id"


@pytest.fixture
def leitner_session_id(client, student_token, classroom_id) -> str:
    """
    UUID of a Leitner session created for tests.
    
    Args:
        classroom_id: Classroom for Leitner review
        
    Returns:
        str: UUID of the test Leitner session
    """
    # TODO: Implement once the app is available
    # response = client.post(
    #     f"/api/classrooms/{classroom_id}/leitner/start",
    #     headers={"Authorization": f"Bearer {student_token}"},
    #     json={"questionCount": 10}
    # )
    # return response.json()["sessionId"]
    return "test-leitner-session-id"


@pytest.fixture
def media_id(client, prof_responsible_token) -> str:
    """
    UUID of a media file uploaded for tests.
    
    Returns:
        str: UUID of the test media
    """
    # TODO: Implement once the app is available
    # with open("test_image.jpg", "rb") as f:
    #     response = client.post(
    #         "/api/media",
    #         headers={"Authorization": f"Bearer {prof_responsible_token}"},
    #         files={"file": ("test.jpg", f, "image/jpeg")}
    #     )
    # return response.json()["mediaId"]
    return "test-media-id"


# =============================================================================
# HELPER FIXTURES
# =============================================================================

@pytest.fixture
def auth_headers():
    """
    Helper fixture to create authorization headers.
    
    Returns:
        Function that takes a token and returns headers dict
    """
    def _auth_headers(token: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}"}
    
    return _auth_headers


@pytest.fixture
def create_user(client):
    """
    Helper fixture to create a user for testing.
    
    Returns:
        Function that creates a user and returns user data
    """
    def _create_user(email: str, password: str, role: str, **kwargs) -> Dict[str, Any]:
        # TODO: Implement once the app is available
        return {
            "id": "test-user-id",
            "email": email,
            "role": role
        }
    
    return _create_user


@pytest.fixture
def create_classroom(client, prof_responsible_token):
    """
    Helper fixture to create a classroom for testing.
    
    Returns:
        Function that creates a classroom and returns classroom data
    """
    def _create_classroom(name: str, level: str) -> Dict[str, Any]:
        # TODO: Implement once the app is available
        return {
            "id": "test-classroom-id",
            "name": name,
            "level": level,
            "code": TEST_CLASSROOM_CODE
        }
    
    return _create_classroom


# =============================================================================
# MOCK SERVICES (for testing different scenarios)
# =============================================================================

@pytest.fixture
def mock_auth_service(monkeypatch):
    """
    Mock the authentication service for testing different scenarios.
    
    This allows testing various authentication flows without a real database.
    """
    class MockAuthService:
        def verify_token(self, token: str):
            """Mock token verification"""
            if token == "invalid":
                raise Exception("Invalid token")
            return {"sub": "test-user-id", "role": "STUDENT"}
        
        def create_token(self, user_id: str, role: str):
            """Mock token creation"""
            return create_test_token({"id": user_id, "role": role, "email": "test@test.com"})
    
    # TODO: Use monkeypatch to replace the actual auth service
    # monkeypatch.setattr("app.services.auth.auth_service", MockAuthService())
    
    return MockAuthService()


# =============================================================================
# AUTO-USE FIXTURES (cleanup, setup)
# =============================================================================

@pytest.fixture(autouse=True)
def reset_database():
    """
    Automatically reset the database before each test.
    
    This ensures test isolation.
    """
    # TODO: Implement database reset logic
    yield
    # Cleanup after test


@pytest.fixture(autouse=True)
def clear_cache():
    """
    Clear any caches before each test.
    """
    # TODO: Implement cache clearing if needed
    yield
