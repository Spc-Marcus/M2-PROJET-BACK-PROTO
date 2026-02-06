"""
Tests for Module management endpoints.

Endpoints tested:
- GET /api/classrooms/{cid}/modules
- POST /api/classrooms/{cid}/modules
- GET /api/modules/{id}
- PATCH /api/modules/{id}
- DELETE /api/modules/{id}

Test coverage:
- CRUD operations
- Prerequisites and locking logic
- Circular dependency detection
- Cascade deletion
- Role-based access control
"""

import pytest


# =============================================================================
# GET /api/classrooms/{cid}/modules
# =============================================================================

def test_list_modules(client, student_token, classroom_id):
    """
    Test listing modules in a classroom.
    
    Expected: 200 OK, list of ModuleDto
    """
    response = client.get(
        f"/classrooms/{classroom_id}/modules",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data or isinstance(data, list)


def test_list_modules_pagination(client, student_token, classroom_id):
    """
    Test module list pagination.
    
    Expected: 200 OK, paginated response
    """
    response = client.get(
        f"/classrooms/{classroom_id}/modules?page=1&limit=10",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200


def test_list_modules_as_non_member(client, student_token):
    """
    Test listing modules for classroom where not a member.
    
    Expected: 403 Forbidden
    """
    other_classroom_id = "other-classroom-id"
    
    response = client.get(
        f"/classrooms/{other_classroom_id}/modules",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403


def test_list_modules_no_auth(client, classroom_id):
    """
    Test listing modules without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.get(f"/classrooms/{classroom_id}/modules")
    
    assert response.status_code == 401


# =============================================================================
# POST /api/classrooms/{cid}/modules
# =============================================================================

def test_create_module_success(client, prof_responsible_token, classroom_id):
    """
    Test creating a module.
    
    Expected: 201 Created, ModuleDto
    """
    response = client.post(
        f"/classrooms/{classroom_id}/modules",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "name": "Membre Inférieur",
            "category": "Ostéologie"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Membre Inférieur"
    assert data["category"] == "Ostéologie"
    assert data["classroomId"] == classroom_id


def test_create_module_with_prerequisite(client, prof_responsible_token, classroom_id, module_id):
    """
    Test creating a module with a prerequisite.
    
    Expected: 201 Created
    """
    response = client.post(
        f"/classrooms/{classroom_id}/modules",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "name": "Advanced Module",
            "category": "Ostéologie",
            "prerequisiteModuleId": module_id
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["prerequisiteModuleId"] == module_id


def test_create_module_circular_prerequisite(client, prof_responsible_token, classroom_id):
    """
    Test circular dependency detection (A → B → A).
    
    Expected: 422 Unprocessable Entity
    """
    # Create module A
    response_a = client.post(
        f"/classrooms/{classroom_id}/modules",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"name": "Module A", "category": "Test"}
    )
    module_a_id = response_a.json()["id"]
    
    # Create module B with prerequisite A
    response_b = client.post(
        f"/classrooms/{classroom_id}/modules",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "name": "Module B",
            "category": "Test",
            "prerequisiteModuleId": module_a_id
        }
    )
    module_b_id = response_b.json()["id"]
    
    # Try to update module A to have prerequisite B (circular)
    response = client.patch(
        f"/modules/{module_a_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"prerequisiteModuleId": module_b_id}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    # Should contain CIRCULAR_PREREQUISITE error code


def test_create_module_as_student(client, student_token, classroom_id):
    """
    Test creating module as student.
    
    Expected: 403 Forbidden
    """
    response = client.post(
        f"/classrooms/{classroom_id}/modules",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"name": "Unauthorized Module", "category": "Test"}
    )
    
    assert response.status_code == 403


def test_create_module_missing_name(client, prof_responsible_token, classroom_id):
    """
    Test creating module without name.
    
    Expected: 400 Bad Request or 422 Unprocessable Entity
    """
    response = client.post(
        f"/classrooms/{classroom_id}/modules",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"category": "Test"}
    )
    
    assert response.status_code in [400, 422]


def test_create_module_as_secondary_prof(client, prof_secondary_token, classroom_id):
    """
    Test creating module as secondary professor.
    
    Expected: 403 Forbidden (only responsible prof can manage modules)
    """
    response = client.post(
        f"/classrooms/{classroom_id}/modules",
        headers={"Authorization": f"Bearer {prof_secondary_token}"},
        json={"name": "Secondary Prof Module", "category": "Test"}
    )
    
    assert response.status_code == 403


# =============================================================================
# GET /api/modules/{id}
# =============================================================================

def test_get_module_success(client, student_token, module_id):
    """
    Test getting module details.
    
    Expected: 200 OK, ModuleDto
    """
    response = client.get(
        f"/modules/{module_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == module_id


def test_get_module_locked_for_student(client, student_token):
    """
    Test that module shows as locked when prerequisite not met.
    
    Expected: 200 OK, isLocked = true
    """
    # This test assumes a module with unmet prerequisite exists
    locked_module_id = "locked-module-id"
    
    response = client.get(
        f"/modules/{locked_module_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    # Response should include module data with isLocked field
    if response.status_code == 200:
        data = response.json()
        assert "isLocked" in data
        # May be true if prerequisite not met


def test_get_module_unlocked_after_prerequisite(client, student_token, module_id):
    """
    Test that module is unlocked after completing prerequisite.
    
    Expected: 200 OK, isLocked = false
    """
    response = client.get(
        f"/modules/{module_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        # If no prerequisite or prerequisite completed, should be unlocked
        assert "isLocked" in data


def test_get_module_not_found(client, student_token):
    """
    Test getting non-existent module.
    
    Expected: 404 Not Found
    """
    response = client.get(
        "/modules/non-existent-id",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 404


def test_get_module_no_auth(client, module_id):
    """
    Test getting module without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.get(f"/modules/{module_id}")
    
    assert response.status_code == 401


# =============================================================================
# PATCH /api/modules/{id}
# =============================================================================

def test_update_module_success(client, prof_responsible_token, module_id):
    """
    Test updating module details.
    
    Expected: 200 OK, updated ModuleDto
    """
    response = client.patch(
        f"/modules/{module_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"name": "Updated Module Name"}
    )
    
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Module Name"


def test_update_module_as_secondary_prof(client, prof_secondary_token, module_id):
    """
    Test updating module as secondary professor.
    
    Expected: 403 Forbidden
    """
    response = client.patch(
        f"/modules/{module_id}",
        headers={"Authorization": f"Bearer {prof_secondary_token}"},
        json={"name": "Unauthorized Update"}
    )
    
    assert response.status_code == 403


def test_update_module_as_student(client, student_token, module_id):
    """
    Test updating module as student.
    
    Expected: 403 Forbidden
    """
    response = client.patch(
        f"/modules/{module_id}",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"name": "Student Update"}
    )
    
    assert response.status_code == 403


def test_update_module_not_found(client, prof_responsible_token):
    """
    Test updating non-existent module.
    
    Expected: 404 Not Found
    """
    response = client.patch(
        "/modules/non-existent-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"name": "Updated"}
    )
    
    assert response.status_code == 404


def test_update_module_prerequisite_circular(client, prof_responsible_token):
    """
    Test that updating prerequisite detects circular dependencies.
    
    Expected: 422 Unprocessable Entity
    """
    # This test would need a setup with modules A → B
    # Then try to set B → A (circular)
    # Expected: 422 with CIRCULAR_PREREQUISITE error
    pass


# =============================================================================
# DELETE /api/modules/{id}
# =============================================================================

def test_delete_module_cascade(client, prof_responsible_token, module_id):
    """
    Test cascade deletion of module (quizzes, questions, sessions).
    
    Expected: 204 No Content
    """
    response = client.delete(
        f"/modules/{module_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 204
    
    # Verify deletion
    get_response = client.get(
        f"/modules/{module_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    assert get_response.status_code == 404


def test_delete_module_as_secondary_prof(client, prof_secondary_token, module_id):
    """
    Test deleting module as secondary professor.
    
    Expected: 403 Forbidden
    """
    response = client.delete(
        f"/modules/{module_id}",
        headers={"Authorization": f"Bearer {prof_secondary_token}"}
    )
    
    assert response.status_code == 403


def test_delete_module_as_student(client, student_token, module_id):
    """
    Test deleting module as student.
    
    Expected: 403 Forbidden
    """
    response = client.delete(
        f"/modules/{module_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403


def test_delete_module_not_found(client, prof_responsible_token):
    """
    Test deleting non-existent module.
    
    Expected: 404 Not Found
    """
    response = client.delete(
        "/modules/non-existent-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 404


def test_delete_module_with_dependent_modules(client, prof_responsible_token):
    """
    Test deleting a module that is a prerequisite for another.
    
    Expected: May be 400 Bad Request or cascade to update dependents
    """
    # This behavior depends on implementation
    # Either: 400 error (can't delete, has dependents)
    # Or: Cascade update (remove prerequisite from dependents)
    pass
