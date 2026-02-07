"""
Global test configuration and fixtures for Duobingo API tests.

This module provides:
- TestClient for FastAPI app
- Authentication tokens for different user roles
- Test data fixtures (classrooms, modules, quizzes, questions)
- Mock services for testing different scenarios
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, AsyncGenerator
from jose import jwt
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import settings
from app.db.session import get_db, Base
from app.models.user import User, Role, Level, StudentProfile, TeacherProfile
from app.core.security import get_password_hash
from app.models import *  # noqa - Import all models to ensure they're registered with Base


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
async def test_engine():
    """
    Create a test database engine for the entire test session.
    Uses SQLite in-memory database with async support.
    """
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await test_engine.dispose()


@pytest.fixture(scope="session")
def test_session_maker(test_engine):
    """Create a session maker for the test database."""
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def test_db(test_session_maker):
    """
    Create a test database session for each test.
    Automatically rolls back after each test for isolation.
    """
    async with test_session_maker() as session:
        yield session
        await session.rollback()


async def override_get_db(test_session_maker):
    """Override the database dependency with test database."""
    async with test_session_maker() as session:
        yield session


@pytest.fixture
def client(test_session_maker):
    """
    FastAPI TestClient for making HTTP requests.
    Uses dependency override to inject test database.
    
    Returns:
        TestClient: Configured test client
    """
    from app.db.session import get_db
    
    async def override_get_db():
        async with test_session_maker() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


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
# SEED DATA FIXTURES
# =============================================================================

@pytest.fixture
async def seed_users(test_db: AsyncSession):
    """
    Seed the test database with the 5 test users.
    Creates users with proper password hashing and profiles.
    
    Returns:
        Dict mapping user keys to user IDs
    """
    user_ids = {}
    
    for key, user_data in TEST_USERS.items():
        # Create user
        user = User(
            email=user_data["email"],
            password=get_password_hash(user_data["password"]),
            name=user_data["name"],
            role=Role[user_data["role"]]
        )
        test_db.add(user)
        await test_db.flush()
        
        # Create profile based on role
        if user_data["role"] == "STUDENT":
            profile = StudentProfile(
                user_id=user.id,
                level=Level[user_data["level"]]
            )
            test_db.add(profile)
        elif user_data["role"] == "TEACHER":
            profile = TeacherProfile(
                user_id=user.id,
                faculty_department=user_data.get("department")
            )
            test_db.add(profile)
        
        user_ids[key] = user.id
    
    await test_db.commit()
    return user_ids


# =============================================================================
# TEST DATA FIXTURES
# =============================================================================

@pytest.fixture
def classroom_id(client, prof_responsible_token, seed_users) -> str:
    """
    UUID of a classroom created for tests.
    
    Creates a classroom with the responsible professor and returns its ID.
    
    Returns:
        str: UUID of the test classroom
    """
    response = client.post(
        "/api/classrooms",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"name": "Test Anatomie L1", "level": "L1", "code": TEST_CLASSROOM_CODE}
    )
    assert response.status_code in [200, 201], f"Failed to create classroom: {response.text}"
    return response.json()["id"]


@pytest.fixture
def module_id(client, prof_responsible_token, classroom_id) -> str:
    """
    UUID of a module created for tests.
    
    Args:
        classroom_id: Parent classroom ID
        
    Returns:
        str: UUID of the test module
    """
    response = client.post(
        f"/api/classrooms/{classroom_id}/modules",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"name": "Test Module", "category": "Ostéologie"}
    )
    assert response.status_code in [200, 201], f"Failed to create module: {response.text}"
    return response.json()["id"]


@pytest.fixture
def quiz_id(client, prof_responsible_token, module_id) -> str:
    """
    UUID of a quiz created for tests.
    
    Args:
        module_id: Parent module ID
        
    Returns:
        str: UUID of the test quiz
    """
    response = client.post(
        f"/api/modules/{module_id}/quizzes",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "title": "Test Quiz",
            "minScoreToUnlockNext": 15,
            "isActive": True
        }
    )
    assert response.status_code in [200, 201], f"Failed to create quiz: {response.text}"
    return response.json()["id"]


@pytest.fixture
def question_id(client, prof_responsible_token, quiz_id) -> str:
    """
    UUID of a question created for tests.
    
    Args:
        quiz_id: Parent quiz ID
        
    Returns:
        str: UUID of the test question
    """
    response = client.post(
        f"/api/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "QCM",
            "contentText": "Test question?",
            "options": [
                {"textChoice": "Answer A", "isCorrect": True},
                {"textChoice": "Answer B", "isCorrect": False}
            ]
        }
    )
    assert response.status_code in [200, 201], f"Failed to create question: {response.text}"
    return response.json()["id"]


@pytest.fixture
def session_id(client, student_token, quiz_id, seed_users) -> str:
    """
    UUID of a quiz session created for tests.
    
    Args:
        quiz_id: Quiz to start a session for
        
    Returns:
        str: UUID of the test session
    """
    response = client.post(
        "/api/sessions/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"quizId": quiz_id}
    )
    assert response.status_code in [200, 201], f"Failed to create session: {response.text}"
    return response.json()["sessionId"]


@pytest.fixture
def leitner_session_id(client, student_token, classroom_id, seed_users) -> str:
    """
    UUID of a Leitner session created for tests.
    
    Args:
        classroom_id: Classroom for Leitner review
        
    Returns:
        str: UUID of the test Leitner session
    """
    response = client.post(
        f"/api/classrooms/{classroom_id}/leitner/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"questionCount": 10}
    )
    assert response.status_code in [200, 201], f"Failed to create Leitner session: {response.text}"
    return response.json()["sessionId"]


@pytest.fixture
def media_id(client, prof_responsible_token, seed_users) -> str:
    """
    UUID of a media file uploaded for tests.
    
    Returns:
        str: UUID of the test media
    """
    import io
    from PIL import Image
    
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    response = client.post(
        "/api/media",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code in [200, 201], f"Failed to upload media: {response.text}"
    return response.json()["mediaId"]


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
def create_user(test_db: AsyncSession):
    """
    Helper fixture to create a user for testing.
    
    Returns:
        Function that creates a user and returns user data
    """
    async def _create_user(email: str, password: str, role: str, **kwargs) -> Dict[str, Any]:
        user = User(
            email=email,
            password=get_password_hash(password),
            name=kwargs.get("name", "Test User"),
            role=Role[role]
        )
        test_db.add(user)
        await test_db.flush()
        
        if role == "STUDENT":
            profile = StudentProfile(
                user_id=user.id,
                level=Level[kwargs.get("level", "L1")]
            )
            test_db.add(profile)
        elif role == "TEACHER":
            profile = TeacherProfile(
                user_id=user.id,
                faculty_department=kwargs.get("department")
            )
            test_db.add(profile)
        
        await test_db.commit()
        return {
            "id": user.id,
            "email": user.email,
            "role": user.role.value
        }
    
    return _create_user


@pytest.fixture
def create_classroom(client, prof_responsible_token, seed_users):
    """
    Helper fixture to create a classroom for testing.
    
    Returns:
        Function that creates a classroom and returns classroom data
    """
    def _create_classroom(name: str, level: str, code: str = None) -> Dict[str, Any]:
        response = client.post(
            "/api/classrooms",
            headers={"Authorization": f"Bearer {prof_responsible_token}"},
            json={"name": name, "level": level, "code": code or TEST_CLASSROOM_CODE}
        )
        assert response.status_code in [200, 201], f"Failed to create classroom: {response.text}"
        return response.json()
    
    return _create_classroom


# =============================================================================
# AUTO-USE FIXTURES (cleanup, setup)
# =============================================================================

@pytest.fixture(autouse=True)
async def reset_database(test_db: AsyncSession):
    """
    Automatically reset the database before each test.
    
    This ensures test isolation by rolling back any changes.
    """
    yield
    await test_db.rollback()
