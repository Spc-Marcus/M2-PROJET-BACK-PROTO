"""
Tests for Authentication & User endpoints.

Endpoints tested:
- POST /api/auth/login
- POST /api/auth/register
- GET /api/users/me
- PATCH /api/users/me
- POST /api/admin/users

Test coverage:
- Valid and invalid credentials
- Token authentication (valid, invalid, expired, missing)
- Email validation
- Password validation
- Role-based access control (Admin, Prof, Student)
- Duplicate email detection
- Profile management
"""

import pytest
from tests.conftest import TEST_USERS


# =============================================================================
# POST /api/auth/login
# =============================================================================

def test_login_valid_credentials(client):
    """
    Test successful login with valid credentials.
    
    Expected: 200 OK, JWT token returned
    """
    response = client.post(
        "/auth/login",
        json={
            "email": TEST_USERS["student1"]["email"],
            "password": TEST_USERS["student1"]["password"]
        }
    )
    
    assert response.status_code == 200
    assert "token" in response.json() or "access_token" in response.json()
    # JWT token format validation
    token = response.json().get("token") or response.json().get("access_token")
    assert token is not None
    assert len(token) > 50  # JWT tokens are long


def test_login_invalid_password(client):
    """
    Test login failure with incorrect password.
    
    Expected: 401 Unauthorized
    """
    response = client.post(
        "/auth/login",
        json={
            "email": TEST_USERS["student1"]["email"],
            "password": "wrong_password"
        }
    )
    
    assert response.status_code == 401
    assert "error" in response.json()


def test_login_user_not_found(client):
    """
    Test login failure with non-existent user.
    
    Expected: 401 Unauthorized
    """
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@univ-rennes.fr",
            "password": "password123"
        }
    )
    
    assert response.status_code == 401


def test_login_missing_email(client):
    """
    Test validation error when email is missing.
    
    Expected: 400 Bad Request or 422 Unprocessable Entity
    """
    response = client.post(
        "/auth/login",
        json={
            "password": "password123"
        }
    )
    
    assert response.status_code in [400, 422]


def test_login_missing_password(client):
    """
    Test validation error when password is missing.
    
    Expected: 400 Bad Request or 422 Unprocessable Entity
    """
    response = client.post(
        "/auth/login",
        json={
            "email": TEST_USERS["student1"]["email"]
        }
    )
    
    assert response.status_code in [400, 422]


def test_login_invalid_email_format(client):
    """
    Test validation error with invalid email format.
    
    Expected: 400 Bad Request or 422 Unprocessable Entity
    """
    response = client.post(
        "/auth/login",
        json={
            "email": "not-an-email",
            "password": "password123"
        }
    )
    
    assert response.status_code in [400, 422]


def test_login_empty_credentials(client):
    """
    Test validation error with empty credentials.
    
    Expected: 400 Bad Request or 422 Unprocessable Entity
    """
    response = client.post(
        "/auth/login",
        json={
            "email": "",
            "password": ""
        }
    )
    
    assert response.status_code in [400, 422]


# =============================================================================
# POST /api/auth/register
# =============================================================================

def test_register_student_success(client):
    """
    Test successful student registration.
    
    Expected: 201 Created, UserResponseDto returned
    """
    response = client.post(
        "/auth/register",
        json={
            "email": "new.student@univ-rennes.fr",
            "password": "password123",
            "name": "New Student",
            "level": "L1"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new.student@univ-rennes.fr"
    assert data["role"] == "STUDENT"
    assert "studentProfile" in data
    assert data["studentProfile"]["level"] == "L1"


def test_register_duplicate_email(client):
    """
    Test registration failure with duplicate email.
    
    Expected: 409 Conflict
    """
    # First registration
    client.post(
        "/auth/register",
        json={
            "email": "duplicate@univ-rennes.fr",
            "password": "password123",
            "name": "First User",
            "level": "L1"
        }
    )
    
    # Second registration with same email
    response = client.post(
        "/auth/register",
        json={
            "email": "duplicate@univ-rennes.fr",
            "password": "password123",
            "name": "Second User",
            "level": "L2"
        }
    )
    
    assert response.status_code == 409


def test_register_invalid_password_too_short(client):
    """
    Test registration failure with password less than 8 characters.
    
    Expected: 400 Bad Request
    """
    response = client.post(
        "/auth/register",
        json={
            "email": "short.password@univ-rennes.fr",
            "password": "pass",  # Only 4 characters
            "name": "Test User",
            "level": "L1"
        }
    )
    
    assert response.status_code == 400


def test_register_invalid_level(client):
    """
    Test registration failure with invalid academic level.
    
    Expected: 400 Bad Request
    """
    response = client.post(
        "/auth/register",
        json={
            "email": "invalid.level@univ-rennes.fr",
            "password": "password123",
            "name": "Test User",
            "level": "INVALID"  # Should be L1, L2, L3, M1, or M2
        }
    )
    
    assert response.status_code == 400


def test_register_missing_required_fields(client):
    """
    Test registration failure with missing required fields.
    
    Expected: 400 Bad Request or 422 Unprocessable Entity
    """
    response = client.post(
        "/auth/register",
        json={
            "email": "incomplete@univ-rennes.fr"
            # Missing password, name, level
        }
    )
    
    assert response.status_code in [400, 422]


def test_register_valid_levels(client):
    """
    Test registration with all valid academic levels.
    
    Expected: 201 Created for each level
    """
    levels = ["L1", "L2", "L3", "M1", "M2"]
    
    for level in levels:
        response = client.post(
            "/auth/register",
            json={
                "email": f"student.{level.lower()}@univ-rennes.fr",
                "password": "password123",
                "name": f"Student {level}",
                "level": level
            }
        )
        
        assert response.status_code == 201
        assert response.json()["studentProfile"]["level"] == level


# =============================================================================
# GET /api/users/me
# =============================================================================

def test_get_user_profile_authenticated(client, student_token):
    """
    Test retrieving user profile while authenticated.
    
    Expected: 200 OK, UserResponseDto returned
    """
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "role" in data
    assert data["role"] == "STUDENT"


def test_get_user_profile_no_token(client):
    """
    Test profile retrieval without authentication token.
    
    Expected: 401 Unauthorized
    """
    response = client.get("/users/me")
    
    assert response.status_code == 401


def test_get_user_profile_invalid_token(client, invalid_token):
    """
    Test profile retrieval with invalid token.
    
    Expected: 401 Unauthorized
    """
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {invalid_token}"}
    )
    
    assert response.status_code == 401


def test_get_user_profile_expired_token(client, expired_token):
    """
    Test profile retrieval with expired token.
    
    Expected: 401 Unauthorized
    """
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    
    assert response.status_code == 401


def test_get_user_profile_malformed_auth_header(client):
    """
    Test profile retrieval with malformed authorization header.
    
    Expected: 401 Unauthorized
    """
    # Missing "Bearer" prefix
    response = client.get(
        "/users/me",
        headers={"Authorization": "some-token"}
    )
    
    assert response.status_code == 401


def test_get_professor_profile(client, prof_responsible_token):
    """
    Test retrieving professor profile.
    
    Expected: 200 OK, profile includes teacherProfile
    """
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "TEACHER"
    assert "teacherProfile" in data


def test_get_admin_profile(client, admin_token):
    """
    Test retrieving admin profile.
    
    Expected: 200 OK, role is ADMIN
    """
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "ADMIN"


# =============================================================================
# PATCH /api/users/me
# =============================================================================

def test_update_user_email(client, student_token):
    """
    Test updating user email.
    
    Expected: 200 OK, email updated in response
    """
    response = client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"email": "updated.email@univ-rennes.fr"}
    )
    
    assert response.status_code == 200
    assert response.json()["email"] == "updated.email@univ-rennes.fr"


def test_update_user_invalid_email(client, student_token):
    """
    Test updating user with invalid email format.
    
    Expected: 400 Bad Request
    """
    response = client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"email": "not-an-email"}
    )
    
    assert response.status_code == 400


def test_update_user_profile_unauthorized(client):
    """
    Test updating profile without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.patch(
        "/users/me",
        json={"email": "new@univ-rennes.fr"}
    )
    
    assert response.status_code == 401


def test_update_user_email_already_exists(client, student_token):
    """
    Test updating email to one that already exists.
    
    Expected: 409 Conflict
    """
    response = client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"email": TEST_USERS["student2"]["email"]}  # Email of another user
    )
    
    assert response.status_code == 409


# =============================================================================
# POST /api/admin/users
# =============================================================================

def test_create_teacher_as_admin(client, admin_token):
    """
    Test creating a teacher account as admin.
    
    Expected: 201 Created
    """
    response = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "new.teacher@univ-rennes.fr",
            "password": "password123",
            "role": "TEACHER",
            "name": "New Teacher",
            "department": "Anatomie"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "TEACHER"
    assert "teacherProfile" in data


def test_create_teacher_as_student(client, student_token):
    """
    Test creating a teacher account as student (insufficient permissions).
    
    Expected: 403 Forbidden
    """
    response = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "email": "unauthorized.teacher@univ-rennes.fr",
            "password": "password123",
            "role": "TEACHER",
            "name": "Unauthorized Teacher",
            "department": "Anatomie"
        }
    )
    
    assert response.status_code == 403


def test_create_teacher_as_professor(client, prof_responsible_token):
    """
    Test creating a teacher account as professor (insufficient permissions).
    
    Expected: 403 Forbidden
    """
    response = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "email": "unauthorized.teacher@univ-rennes.fr",
            "password": "password123",
            "role": "TEACHER",
            "name": "Unauthorized Teacher",
            "department": "Anatomie"
        }
    )
    
    assert response.status_code == 403


def test_create_user_invalid_role(client, admin_token):
    """
    Test creating user with invalid role.
    
    Expected: 400 Bad Request
    """
    response = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "invalid.role@univ-rennes.fr",
            "password": "password123",
            "role": "INVALID_ROLE",
            "name": "Test User"
        }
    )
    
    assert response.status_code == 400


def test_create_admin_as_admin(client, admin_token):
    """
    Test creating an admin account as admin.
    
    Expected: 201 Created
    """
    response = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "new.admin@univ-rennes.fr",
            "password": "password123",
            "role": "ADMIN",
            "name": "New Admin"
        }
    )
    
    assert response.status_code == 201
    assert response.json()["role"] == "ADMIN"


def test_create_user_no_auth(client):
    """
    Test creating user without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.post(
        "/admin/users",
        json={
            "email": "no.auth@univ-rennes.fr",
            "password": "password123",
            "role": "TEACHER",
            "name": "No Auth User"
        }
    )
    
    assert response.status_code == 401
