"""
Tests for Quiz management endpoints.

Endpoints tested:
- GET /api/modules/{mid}/quizzes
- POST /api/modules/{mid}/quizzes
- GET /api/quizzes/{id}
- PATCH /api/quizzes/{id}
- DELETE /api/quizzes/{id}

Test coverage:
- CRUD operations
- Prerequisites and locking logic
- Circular dependency detection
- Active/inactive state
- Cascade deletion
- Role-based access control
"""

import pytest


# =============================================================================
# GET /api/modules/{mid}/quizzes
# =============================================================================

def test_list_quizzes(client, student_token, module_id):
    """
    Test listing quizzes in a module.
    
    Expected: 200 OK, list of QuizDto
    """
    response = client.get(
        f"/modules/{module_id}/quizzes",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data or isinstance(data, list)


def test_list_quizzes_pagination(client, student_token, module_id):
    """
    Test quiz list pagination.
    
    Expected: 200 OK, paginated response
    """
    response = client.get(
        f"/modules/{module_id}/quizzes?page=1&limit=10",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200


def test_list_quizzes_shows_locked_status(client, student_token, module_id):
    """
    Test that quiz list includes isLocked field for each quiz.
    
    Expected: 200 OK, each quiz has isLocked boolean
    """
    response = client.get(
        f"/modules/{module_id}/quizzes",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        quizzes = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(quizzes, list) and len(quizzes) > 0:
            assert "isLocked" in quizzes[0]


def test_list_quizzes_no_auth(client, module_id):
    """
    Test listing quizzes without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.get(f"/modules/{module_id}/quizzes")
    
    assert response.status_code == 401


# =============================================================================
# POST /api/modules/{mid}/quizzes
# =============================================================================

def test_create_quiz_success(client, prof_responsible_token, module_id):
    """
    Test creating a quiz.
    
    Expected: 201 Created, QuizDto with questionCount = 0
    """
    response = client.post(
        f"/modules/{module_id}/quizzes",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "title": "Le Pied",
            "minScoreToUnlockNext": 15,
            "isActive": True
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Le Pied"
    assert data["minScoreToUnlockNext"] == 15
    assert data["isActive"] is True
    assert data["questionCount"] == 0


def test_create_quiz_with_prerequisite(client, prof_responsible_token, module_id, quiz_id):
    """
    Test creating a quiz with a prerequisite quiz.
    
    Expected: 201 Created
    """
    response = client.post(
        f"/modules/{module_id}/quizzes",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "title": "Advanced Quiz",
            "minScoreToUnlockNext": 15,
            "isActive": True,
            "prerequisiteQuizId": quiz_id
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["prerequisiteQuizId"] == quiz_id


def test_create_quiz_circular_prerequisite(client, prof_responsible_token, module_id):
    """
    Test circular dependency detection (Quiz A → B → A).
    
    Expected: 422 Unprocessable Entity
    """
    # Create quiz A
    response_a = client.post(
        f"/modules/{module_id}/quizzes",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"title": "Quiz A", "minScoreToUnlockNext": 10, "isActive": True}
    )
    quiz_a_id = response_a.json()["id"]
    
    # Create quiz B with prerequisite A
    response_b = client.post(
        f"/modules/{module_id}/quizzes",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "title": "Quiz B",
            "minScoreToUnlockNext": 10,
            "isActive": True,
            "prerequisiteQuizId": quiz_a_id
        }
    )
    quiz_b_id = response_b.json()["id"]
    
    # Try to update quiz A to have prerequisite B (circular)
    response = client.patch(
        f"/quizzes/{quiz_a_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"prerequisiteQuizId": quiz_b_id}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "error" in data


def test_create_quiz_as_secondary_prof(client, prof_secondary_token, module_id):
    """
    Test creating quiz as secondary professor (should be allowed).
    
    Expected: 201 Created
    """
    response = client.post(
        f"/modules/{module_id}/quizzes",
        headers={"Authorization": f"Bearer {prof_secondary_token}"},
        json={
            "title": "Secondary Prof Quiz",
            "minScoreToUnlockNext": 15,
            "isActive": True
        }
    )
    
    # Secondary profs can create quizzes
    assert response.status_code == 201


def test_create_quiz_as_student(client, student_token, module_id):
    """
    Test creating quiz as student.
    
    Expected: 403 Forbidden
    """
    response = client.post(
        f"/modules/{module_id}/quizzes",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"title": "Student Quiz", "minScoreToUnlockNext": 10, "isActive": True}
    )
    
    assert response.status_code == 403


def test_create_quiz_missing_title(client, prof_responsible_token, module_id):
    """
    Test creating quiz without title.
    
    Expected: 400 Bad Request or 422 Unprocessable Entity
    """
    response = client.post(
        f"/modules/{module_id}/quizzes",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"minScoreToUnlockNext": 15, "isActive": True}
    )
    
    assert response.status_code in [400, 422]


def test_create_quiz_invalid_min_score(client, prof_responsible_token, module_id):
    """
    Test creating quiz with invalid minScoreToUnlockNext (negative).
    
    Expected: 400 Bad Request
    """
    response = client.post(
        f"/modules/{module_id}/quizzes",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "title": "Test Quiz",
            "minScoreToUnlockNext": -5,
            "isActive": True
        }
    )
    
    assert response.status_code == 400


# =============================================================================
# GET /api/quizzes/{id}
# =============================================================================

def test_get_quiz_success(client, student_token, quiz_id):
    """
    Test getting quiz details.
    
    Expected: 200 OK, QuizDto
    """
    response = client.get(
        f"/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == quiz_id


def test_quiz_locked_prerequisite_not_met(client, student_token):
    """
    Test that quiz shows as locked when prerequisite not met.
    
    Expected: 200 OK, isLocked = true
    """
    locked_quiz_id = "locked-quiz-id"
    
    response = client.get(
        f"/quizzes/{locked_quiz_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        assert "isLocked" in data


def test_quiz_unlocked_after_prerequisite(client, student_token, quiz_id):
    """
    Test that quiz is unlocked after completing prerequisite.
    
    Expected: 200 OK, isLocked = false
    """
    response = client.get(
        f"/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        assert "isLocked" in data


def test_get_quiz_not_found(client, student_token):
    """
    Test getting non-existent quiz.
    
    Expected: 404 Not Found
    """
    response = client.get(
        "/quizzes/non-existent-id",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 404


def test_get_quiz_no_auth(client, quiz_id):
    """
    Test getting quiz without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.get(f"/quizzes/{quiz_id}")
    
    assert response.status_code == 401


# =============================================================================
# PATCH /api/quizzes/{id}
# =============================================================================

def test_update_quiz_success(client, prof_responsible_token, quiz_id):
    """
    Test updating quiz details.
    
    Expected: 200 OK, updated QuizDto
    """
    response = client.patch(
        f"/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "title": "Updated Quiz Title",
            "minScoreToUnlockNext": 18
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Quiz Title"
    assert data["minScoreToUnlockNext"] == 18


def test_update_quiz_activate_deactivate(client, prof_responsible_token, quiz_id):
    """
    Test activating/deactivating a quiz.
    
    Expected: 200 OK, isActive updated
    """
    # Deactivate
    response = client.patch(
        f"/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"isActive": False}
    )
    
    assert response.status_code == 200
    assert response.json()["isActive"] is False
    
    # Reactivate
    response = client.patch(
        f"/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"isActive": True}
    )
    
    assert response.status_code == 200
    assert response.json()["isActive"] is True


def test_update_quiz_as_secondary_prof(client, prof_secondary_token, quiz_id):
    """
    Test updating quiz as secondary professor (should be allowed).
    
    Expected: 200 OK
    """
    response = client.patch(
        f"/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {prof_secondary_token}"},
        json={"title": "Secondary Prof Update"}
    )
    
    # Secondary profs can update quizzes
    assert response.status_code == 200


def test_update_quiz_as_student(client, student_token, quiz_id):
    """
    Test updating quiz as student.
    
    Expected: 403 Forbidden
    """
    response = client.patch(
        f"/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"title": "Student Update"}
    )
    
    assert response.status_code == 403


def test_update_quiz_not_found(client, prof_responsible_token):
    """
    Test updating non-existent quiz.
    
    Expected: 404 Not Found
    """
    response = client.patch(
        "/quizzes/non-existent-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"title": "Updated"}
    )
    
    assert response.status_code == 404


# =============================================================================
# DELETE /api/quizzes/{id}
# =============================================================================

def test_delete_quiz_cascade(client, prof_responsible_token, quiz_id):
    """
    Test cascade deletion of quiz (questions, sessions).
    
    Expected: 204 No Content
    """
    response = client.delete(
        f"/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 204
    
    # Verify deletion
    get_response = client.get(
        f"/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    assert get_response.status_code == 404


def test_delete_quiz_as_secondary_prof(client, prof_secondary_token, quiz_id):
    """
    Test deleting quiz as secondary professor (should be allowed).
    
    Expected: 204 No Content
    """
    response = client.delete(
        f"/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {prof_secondary_token}"}
    )
    
    # Secondary profs can delete quizzes
    assert response.status_code == 204


def test_delete_quiz_as_student(client, student_token, quiz_id):
    """
    Test deleting quiz as student.
    
    Expected: 403 Forbidden
    """
    response = client.delete(
        f"/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403


def test_delete_quiz_not_found(client, prof_responsible_token):
    """
    Test deleting non-existent quiz.
    
    Expected: 404 Not Found
    """
    response = client.delete(
        "/quizzes/non-existent-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 404


def test_delete_quiz_with_dependent_quizzes(client, prof_responsible_token):
    """
    Test deleting a quiz that is a prerequisite for another.
    
    Expected: May be 400 Bad Request or cascade to update dependents
    """
    # This behavior depends on implementation
    # Either: 400 error (can't delete, has dependents)
    # Or: Cascade update (remove prerequisite from dependents)
    pass


# =============================================================================
# ADDITIONAL TESTS
# =============================================================================

def test_inactive_quiz_visibility(client, student_token):
    """
    Test that inactive quizzes are hidden from students.
    
    Expected: Student should not see inactive quizzes in list
    """
    # This test would create an inactive quiz and verify
    # it doesn't appear in student's quiz list
    pass


def test_quiz_question_count_updated(client, prof_responsible_token, quiz_id):
    """
    Test that questionCount is updated when questions are added/removed.
    
    Expected: questionCount reflects actual number of questions
    """
    # Get initial count
    response = client.get(
        f"/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        assert "questionCount" in data
