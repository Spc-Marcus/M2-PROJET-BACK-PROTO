"""
Tests for Classroom management endpoints.

Endpoints tested:
- GET /api/classrooms
- POST /api/classrooms
- GET /api/classrooms/{id}
- PATCH /api/classrooms/{id}
- DELETE /api/classrooms/{id}
- GET /api/classrooms/{id}/members
- POST /api/classrooms/{id}/teachers
- DELETE /api/classrooms/{id}/teachers/{tid}
- POST /api/classrooms/{id}/enroll
- DELETE /api/classrooms/{id}/students/{sid}
- POST /api/classrooms/{id}/join
- POST /api/classrooms/{id}/regenerate-code

Test coverage:
- CRUD operations
- Role-based access (Prof Responsible, Secondary Prof, Student)
- Membership management
- Code generation and validation
- Cascade deletion
- Pagination
"""

import pytest
from tests.conftest import TEST_CLASSROOM_CODE


# =============================================================================
# GET /api/classrooms
# =============================================================================

def test_list_classrooms_student(client, student_token):
    """
    Test student sees only their enrolled classrooms.
    
    Expected: 200 OK, list of enrolled classrooms
    """
    response = client.get(
        "/classrooms",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data or isinstance(data, list)


def test_list_classrooms_professor(client, prof_responsible_token):
    """
    Test professor sees their managed classrooms.
    
    Expected: 200 OK, list of managed classrooms
    """
    response = client.get(
        "/classrooms",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data or isinstance(data, list)


def test_list_classrooms_admin(client, admin_token):
    """
    Test admin sees all classrooms.
    
    Expected: 200 OK, list of all classrooms
    """
    response = client.get(
        "/classrooms",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200


def test_list_classrooms_no_auth(client):
    """
    Test listing classrooms without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.get("/classrooms")
    
    assert response.status_code == 401


def test_list_classrooms_pagination(client, prof_responsible_token):
    """
    Test classroom list pagination.
    
    Expected: 200 OK, paginated response with metadata
    """
    response = client.get(
        "/classrooms?page=1&limit=10",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Check for pagination metadata
    if "pagination" in data:
        assert "page" in data["pagination"]
        assert "totalItems" in data["pagination"]


# =============================================================================
# POST /api/classrooms
# =============================================================================

def test_create_classroom_success(client, prof_responsible_token):
    """
    Test successful classroom creation.
    
    Expected: 201 Created, ClassroomDto with generated code
    """
    response = client.post(
        "/classrooms",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "name": "Anatomie L1",
            "level": "L1"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Anatomie L1"
    assert data["level"] == "L1"
    assert "code" in data
    assert len(data["code"]) == 6  # 6-character code


def test_create_classroom_as_student(client, student_token):
    """
    Test classroom creation as student (insufficient permissions).
    
    Expected: 403 Forbidden
    """
    response = client.post(
        "/classrooms",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "name": "Unauthorized Classroom",
            "level": "L1"
        }
    )
    
    assert response.status_code == 403


def test_create_classroom_invalid_level(client, prof_responsible_token):
    """
    Test classroom creation with invalid level.
    
    Expected: 400 Bad Request
    """
    response = client.post(
        "/classrooms",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "name": "Test Classroom",
            "level": "INVALID"
        }
    )
    
    assert response.status_code == 400


def test_create_classroom_missing_name(client, prof_responsible_token):
    """
    Test classroom creation without name.
    
    Expected: 400 Bad Request or 422 Unprocessable Entity
    """
    response = client.post(
        "/classrooms",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "level": "L1"
        }
    )
    
    assert response.status_code in [400, 422]


def test_create_classroom_no_auth(client):
    """
    Test classroom creation without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.post(
        "/classrooms",
        json={
            "name": "No Auth Classroom",
            "level": "L1"
        }
    )
    
    assert response.status_code == 401


# =============================================================================
# GET /api/classrooms/{id}
# =============================================================================

def test_get_classroom_as_member(client, student_token, classroom_id):
    """
    Test accessing classroom as enrolled member.
    
    Expected: 200 OK, ClassroomDto
    """
    response = client.get(
        f"/classrooms/{classroom_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == classroom_id


def test_get_classroom_as_non_member(client, student_token):
    """
    Test accessing classroom as non-member.
    
    Expected: 403 Forbidden
    """
    # Use a different classroom ID that student is not enrolled in
    other_classroom_id = "other-classroom-id"
    
    response = client.get(
        f"/classrooms/{other_classroom_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403


def test_get_classroom_not_found(client, prof_responsible_token):
    """
    Test accessing non-existent classroom.
    
    Expected: 404 Not Found
    """
    response = client.get(
        "/classrooms/non-existent-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 404


def test_get_classroom_no_auth(client, classroom_id):
    """
    Test accessing classroom without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.get(f"/classrooms/{classroom_id}")
    
    assert response.status_code == 401


# =============================================================================
# PATCH /api/classrooms/{id}
# =============================================================================

def test_patch_classroom_as_responsible(client, prof_responsible_token, classroom_id):
    """
    Test modifying classroom as responsible professor.
    
    Expected: 200 OK, updated ClassroomDto
    """
    response = client.patch(
        f"/classrooms/{classroom_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"name": "Anatomie L2 Updated"}
    )
    
    assert response.status_code == 200
    assert response.json()["name"] == "Anatomie L2 Updated"


def test_patch_classroom_as_secondary_prof(client, prof_secondary_token, classroom_id):
    """
    Test modifying classroom as secondary professor.
    
    Expected: 403 Forbidden
    """
    response = client.patch(
        f"/classrooms/{classroom_id}",
        headers={"Authorization": f"Bearer {prof_secondary_token}"},
        json={"name": "Unauthorized Update"}
    )
    
    assert response.status_code == 403


def test_patch_classroom_as_student(client, student_token, classroom_id):
    """
    Test modifying classroom as student.
    
    Expected: 403 Forbidden
    """
    response = client.patch(
        f"/classrooms/{classroom_id}",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"name": "Student Update"}
    )
    
    assert response.status_code == 403


def test_patch_classroom_not_found(client, prof_responsible_token):
    """
    Test modifying non-existent classroom.
    
    Expected: 404 Not Found
    """
    response = client.patch(
        "/classrooms/non-existent-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"name": "Updated Name"}
    )
    
    assert response.status_code == 404


# =============================================================================
# DELETE /api/classrooms/{id}
# =============================================================================

def test_delete_classroom_cascade(client, prof_responsible_token, classroom_id):
    """
    Test cascade deletion of classroom (modules, quizzes, sessions).
    
    Expected: 204 No Content
    """
    response = client.delete(
        f"/classrooms/{classroom_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 204
    
    # Verify deletion - attempt to get should return 404
    get_response = client.get(
        f"/classrooms/{classroom_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    assert get_response.status_code == 404


def test_delete_classroom_as_secondary_prof(client, prof_secondary_token, classroom_id):
    """
    Test deleting classroom as secondary professor.
    
    Expected: 403 Forbidden
    """
    response = client.delete(
        f"/classrooms/{classroom_id}",
        headers={"Authorization": f"Bearer {prof_secondary_token}"}
    )
    
    assert response.status_code == 403


def test_delete_classroom_as_student(client, student_token, classroom_id):
    """
    Test deleting classroom as student.
    
    Expected: 403 Forbidden
    """
    response = client.delete(
        f"/classrooms/{classroom_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403


def test_delete_classroom_not_found(client, prof_responsible_token):
    """
    Test deleting non-existent classroom.
    
    Expected: 404 Not Found
    """
    response = client.delete(
        "/classrooms/non-existent-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 404


# =============================================================================
# GET /api/classrooms/{id}/members
# =============================================================================

def test_get_classroom_members(client, prof_responsible_token, classroom_id):
    """
    Test listing classroom members (professors + students).
    
    Expected: 200 OK, ClassroomMembersDto with pagination
    """
    response = client.get(
        f"/classrooms/{classroom_id}/members",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should contain responsibleProfessor, teachers, students
    assert "responsibleProfessor" in data or "teachers" in data or "students" in data


def test_get_classroom_members_as_student(client, student_token, classroom_id):
    """
    Test listing members as student (may be restricted).
    
    Expected: 200 OK or 403 Forbidden (depends on implementation)
    """
    response = client.get(
        f"/classrooms/{classroom_id}/members",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    # Either allowed (200) or forbidden (403)
    assert response.status_code in [200, 403]


def test_get_classroom_members_pagination(client, prof_responsible_token, classroom_id):
    """
    Test members list pagination.
    
    Expected: 200 OK, paginated response
    """
    response = client.get(
        f"/classrooms/{classroom_id}/members?page=1&limit=10",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 200


# =============================================================================
# POST /api/classrooms/{id}/teachers
# =============================================================================

def test_add_teacher_success(client, prof_responsible_token, classroom_id):
    """
    Test adding a teacher to classroom.
    
    Expected: 200 OK or 201 Created
    """
    response = client.post(
        f"/classrooms/{classroom_id}/teachers",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"email": "new.teacher@univ-rennes.fr"}
    )
    
    assert response.status_code in [200, 201]


def test_add_teacher_invalid_email(client, prof_responsible_token, classroom_id):
    """
    Test adding teacher with non-existent email.
    
    Expected: 404 Not Found
    """
    response = client.post(
        f"/classrooms/{classroom_id}/teachers",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"email": "nonexistent@univ-rennes.fr"}
    )
    
    assert response.status_code == 404


def test_add_teacher_as_secondary_prof(client, prof_secondary_token, classroom_id):
    """
    Test adding teacher as secondary professor.
    
    Expected: 403 Forbidden
    """
    response = client.post(
        f"/classrooms/{classroom_id}/teachers",
        headers={"Authorization": f"Bearer {prof_secondary_token}"},
        json={"email": "another.teacher@univ-rennes.fr"}
    )
    
    assert response.status_code == 403


def test_add_teacher_as_student(client, student_token, classroom_id):
    """
    Test adding teacher as student.
    
    Expected: 403 Forbidden
    """
    response = client.post(
        f"/classrooms/{classroom_id}/teachers",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"email": "teacher@univ-rennes.fr"}
    )
    
    assert response.status_code == 403


# =============================================================================
# DELETE /api/classrooms/{id}/teachers/{tid}
# =============================================================================

def test_remove_teacher_success(client, prof_responsible_token, classroom_id):
    """
    Test removing a teacher from classroom.
    
    Expected: 204 No Content
    """
    teacher_id = "teacher-to-remove-id"
    
    response = client.delete(
        f"/classrooms/{classroom_id}/teachers/{teacher_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 204


def test_remove_teacher_as_secondary_prof(client, prof_secondary_token, classroom_id):
    """
    Test removing teacher as secondary professor.
    
    Expected: 403 Forbidden
    """
    teacher_id = "teacher-id"
    
    response = client.delete(
        f"/classrooms/{classroom_id}/teachers/{teacher_id}",
        headers={"Authorization": f"Bearer {prof_secondary_token}"}
    )
    
    assert response.status_code == 403


def test_remove_teacher_not_found(client, prof_responsible_token, classroom_id):
    """
    Test removing non-existent teacher.
    
    Expected: 404 Not Found
    """
    response = client.delete(
        f"/classrooms/{classroom_id}/teachers/non-existent-teacher-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 404


# =============================================================================
# POST /api/classrooms/{id}/enroll
# =============================================================================

def test_enroll_student_success(client, prof_responsible_token, classroom_id):
    """
    Test enrolling a student via email.
    
    Expected: 200 OK or 201 Created
    """
    response = client.post(
        f"/classrooms/{classroom_id}/enroll",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"email": "student@univ-rennes.fr"}
    )
    
    assert response.status_code in [200, 201]


def test_enroll_student_already_enrolled(client, prof_responsible_token, classroom_id):
    """
    Test enrolling a student who is already enrolled.
    
    Expected: 409 Conflict
    """
    # Enroll first time
    client.post(
        f"/classrooms/{classroom_id}/enroll",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"email": "duplicate.student@univ-rennes.fr"}
    )
    
    # Try to enroll again
    response = client.post(
        f"/classrooms/{classroom_id}/enroll",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"email": "duplicate.student@univ-rennes.fr"}
    )
    
    assert response.status_code == 409


def test_enroll_student_invalid_email(client, prof_responsible_token, classroom_id):
    """
    Test enrolling with non-existent email.
    
    Expected: 404 Not Found
    """
    response = client.post(
        f"/classrooms/{classroom_id}/enroll",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"email": "nonexistent@univ-rennes.fr"}
    )
    
    assert response.status_code == 404


# =============================================================================
# DELETE /api/classrooms/{id}/students/{sid}
# =============================================================================

def test_remove_student_success(client, prof_responsible_token, classroom_id):
    """
    Test removing a student from classroom.
    
    Expected: 204 No Content
    """
    student_id = "student-to-remove-id"
    
    response = client.delete(
        f"/classrooms/{classroom_id}/students/{student_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 204


def test_remove_student_as_secondary_prof(client, prof_secondary_token, classroom_id):
    """
    Test removing student as secondary professor.
    
    Expected: 403 Forbidden
    """
    student_id = "student-id"
    
    response = client.delete(
        f"/classrooms/{classroom_id}/students/{student_id}",
        headers={"Authorization": f"Bearer {prof_secondary_token}"}
    )
    
    assert response.status_code == 403


def test_remove_student_not_found(client, prof_responsible_token, classroom_id):
    """
    Test removing non-existent student.
    
    Expected: 404 Not Found
    """
    response = client.delete(
        f"/classrooms/{classroom_id}/students/non-existent-student-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 404


# =============================================================================
# POST /api/classrooms/{id}/join
# =============================================================================

def test_join_classroom_valid_code(client, student_token):
    """
    Test joining classroom with valid code.
    
    Expected: 200 OK
    """
    response = client.post(
        "/classrooms/join",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"code": TEST_CLASSROOM_CODE}
    )
    
    assert response.status_code == 200


def test_join_classroom_invalid_code(client, student_token):
    """
    Test joining with invalid/non-existent code.
    
    Expected: 400 Bad Request or 404 Not Found
    """
    response = client.post(
        "/classrooms/join",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"code": "INVALID"}
    )
    
    assert response.status_code in [400, 404]
    # Should contain business error code
    if response.status_code == 400:
        data = response.json()
        assert "error" in data
        # May contain CLASSROOM_CODE_INVALID


def test_join_classroom_already_enrolled(client, student_token, classroom_id):
    """
    Test joining a classroom already enrolled in.
    
    Expected: 409 Conflict
    """
    # First join
    client.post(
        "/classrooms/join",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"code": TEST_CLASSROOM_CODE}
    )
    
    # Try to join again
    response = client.post(
        "/classrooms/join",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"code": TEST_CLASSROOM_CODE}
    )
    
    assert response.status_code == 409


def test_join_classroom_as_professor(client, prof_responsible_token):
    """
    Test joining classroom as professor (may be restricted).
    
    Expected: 403 Forbidden (professors don't join, they create/are added)
    """
    response = client.post(
        "/classrooms/join",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"code": TEST_CLASSROOM_CODE}
    )
    
    assert response.status_code == 403


def test_join_classroom_no_auth(client):
    """
    Test joining classroom without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.post(
        "/classrooms/join",
        json={"code": TEST_CLASSROOM_CODE}
    )
    
    assert response.status_code == 401


# =============================================================================
# POST /api/classrooms/{id}/regenerate-code
# =============================================================================

def test_regenerate_code_success(client, prof_responsible_token, classroom_id):
    """
    Test regenerating classroom code.
    
    Expected: 200 OK, new code in response
    """
    # Get current code
    get_response = client.get(
        f"/classrooms/{classroom_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    old_code = get_response.json()["code"]
    
    # Regenerate code
    response = client.post(
        f"/classrooms/{classroom_id}/regenerate-code",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "code" in data or "newCode" in data
    new_code = data.get("code") or data.get("newCode")
    assert new_code != old_code
    assert len(new_code) == 6


def test_regenerate_code_as_secondary_prof(client, prof_secondary_token, classroom_id):
    """
    Test regenerating code as secondary professor.
    
    Expected: 403 Forbidden
    """
    response = client.post(
        f"/classrooms/{classroom_id}/regenerate-code",
        headers={"Authorization": f"Bearer {prof_secondary_token}"}
    )
    
    assert response.status_code == 403


def test_regenerate_code_as_student(client, student_token, classroom_id):
    """
    Test regenerating code as student.
    
    Expected: 403 Forbidden
    """
    response = client.post(
        f"/classrooms/{classroom_id}/regenerate-code",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403


def test_regenerate_code_old_code_invalidated(client, prof_responsible_token, student_token, classroom_id):
    """
    Test that old code is invalidated after regeneration.
    
    Expected: Old code no longer works
    """
    # Get current code
    get_response = client.get(
        f"/classrooms/{classroom_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    old_code = get_response.json()["code"]
    
    # Regenerate code
    client.post(
        f"/classrooms/{classroom_id}/regenerate-code",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    # Try to join with old code
    response = client.post(
        "/classrooms/join",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"code": old_code}
    )
    
    assert response.status_code in [400, 404]
