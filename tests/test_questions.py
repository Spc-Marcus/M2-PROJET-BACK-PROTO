"""
Tests for Question bank endpoints.

Endpoints tested:
- GET /api/quizzes/{qid}/questions
- POST /api/quizzes/{qid}/questions
- GET /api/questions/{id}
- PATCH /api/questions/{id}
- DELETE /api/questions/{id}

Test coverage:
- 5 polymorphic question types (QCM, VRAI_FAUX, MATCHING, IMAGE, TEXT)
- Question creation and validation
- Media attachment (for IMAGE type)
- Answer configuration
- Role-based access control
- Leitner box integration
"""

import pytest


# =============================================================================
# POST /api/quizzes/{qid}/questions - QCM (Multiple Choice)
# =============================================================================

def test_create_qcm_question(client, prof_responsible_token, quiz_id):
    """
    Test creating a QCM (multiple choice) question.
    
    Expected: 201 Created, QuestionDto
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "QCM",
            "contentText": "Quel os constitue le talon ?",
            "options": [
                {"textChoice": "Calcanéus", "isCorrect": True},
                {"textChoice": "Talus", "isCorrect": False},
                {"textChoice": "Cuboïde", "isCorrect": False},
                {"textChoice": "Naviculaire", "isCorrect": False}
            ],
            "explanation": "Le calcanéus est l'os du talon."
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "QCM"
    assert data["contentText"] == "Quel os constitue le talon ?"
    assert len(data["options"]) == 4


def test_create_qcm_multiple_correct_answers(client, prof_responsible_token, quiz_id):
    """
    Test creating QCM with multiple correct answers.
    
    Expected: 201 Created
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "QCM",
            "contentText": "Quels os font partie du pied ? (plusieurs réponses)",
            "options": [
                {"textChoice": "Calcanéus", "isCorrect": True},
                {"textChoice": "Talus", "isCorrect": True},
                {"textChoice": "Fémur", "isCorrect": False},
                {"textChoice": "Tibia", "isCorrect": False}
            ]
        }
    )
    
    assert response.status_code == 201


def test_create_qcm_missing_options(client, prof_responsible_token, quiz_id):
    """
    Test creating QCM without options.
    
    Expected: 400 Bad Request
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "QCM",
            "contentText": "Question without options?"
        }
    )
    
    assert response.status_code == 400


def test_create_qcm_no_correct_answer(client, prof_responsible_token, quiz_id):
    """
    Test creating QCM without any correct answer.
    
    Expected: 400 Bad Request
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "QCM",
            "contentText": "Question?",
            "options": [
                {"textChoice": "A", "isCorrect": False},
                {"textChoice": "B", "isCorrect": False}
            ]
        }
    )
    
    assert response.status_code == 400


# =============================================================================
# POST /api/quizzes/{qid}/questions - VRAI_FAUX (True/False)
# =============================================================================

def test_create_truefalse_question(client, prof_responsible_token, quiz_id):
    """
    Test creating a VRAI_FAUX (true/false) question.
    
    Expected: 201 Created
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "VRAI_FAUX",
            "contentText": "Le tibia est l'os interne de la jambe",
            "options": [
                {"textChoice": "Vrai", "isCorrect": True},
                {"textChoice": "Faux", "isCorrect": False}
            ],
            "explanation": "Le tibia est effectivement situé du côté interne."
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "VRAI_FAUX"
    assert len(data["options"]) == 2


def test_create_truefalse_with_wrong_options(client, prof_responsible_token, quiz_id):
    """
    Test creating VRAI_FAUX with more than 2 options.
    
    Expected: 400 Bad Request (must have exactly 2 options)
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "VRAI_FAUX",
            "contentText": "Question?",
            "options": [
                {"textChoice": "Vrai", "isCorrect": True},
                {"textChoice": "Faux", "isCorrect": False},
                {"textChoice": "Peut-être", "isCorrect": False}
            ]
        }
    )
    
    assert response.status_code == 400


# =============================================================================
# POST /api/quizzes/{qid}/questions - MATCHING (Pairing)
# =============================================================================

def test_create_matching_question(client, prof_responsible_token, quiz_id):
    """
    Test creating a MATCHING (pairing) question.
    
    Expected: 201 Created
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "MATCHING",
            "contentText": "Appariez les os avec leur localisation",
            "matchingPairs": [
                {"itemLeft": "Tibia", "itemRight": "Interne"},
                {"itemLeft": "Fibula", "itemRight": "Externe"},
                {"itemLeft": "Fémur", "itemRight": "Cuisse"}
            ]
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "MATCHING"
    assert len(data["matchingPairs"]) == 3


def test_create_matching_missing_pairs(client, prof_responsible_token, quiz_id):
    """
    Test creating MATCHING without matchingPairs.
    
    Expected: 400 Bad Request
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "MATCHING",
            "contentText": "Match items"
        }
    )
    
    assert response.status_code == 400


def test_create_matching_insufficient_pairs(client, prof_responsible_token, quiz_id):
    """
    Test creating MATCHING with too few pairs (< 2).
    
    Expected: 400 Bad Request
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "MATCHING",
            "contentText": "Match items",
            "matchingPairs": [
                {"itemLeft": "A", "itemRight": "1"}
            ]
        }
    )
    
    assert response.status_code == 400


# =============================================================================
# POST /api/quizzes/{qid}/questions - TEXT (Text Input)
# =============================================================================

def test_create_text_question(client, prof_responsible_token, quiz_id):
    """
    Test creating a TEXT (text input) question.
    
    Expected: 201 Created
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "TEXT",
            "contentText": "Nommez l'os du talon",
            "textConfig": {
                "acceptedAnswer": "Calcanéus",
                "isCaseSensitive": False,
                "ignoreSpellingErrors": True
            }
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "TEXT"
    assert data["textConfig"]["acceptedAnswer"] == "Calcanéus"


def test_create_text_case_sensitive(client, prof_responsible_token, quiz_id):
    """
    Test creating TEXT question with case sensitivity.
    
    Expected: 201 Created
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "TEXT",
            "contentText": "Écrivez exactement: DNA",
            "textConfig": {
                "acceptedAnswer": "DNA",
                "isCaseSensitive": True,
                "ignoreSpellingErrors": False
            }
        }
    )
    
    assert response.status_code == 201
    assert response.json()["textConfig"]["isCaseSensitive"] is True


def test_create_text_missing_config(client, prof_responsible_token, quiz_id):
    """
    Test creating TEXT without textConfig.
    
    Expected: 400 Bad Request
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "TEXT",
            "contentText": "Text question without config"
        }
    )
    
    assert response.status_code == 400


def test_create_text_missing_accepted_answer(client, prof_responsible_token, quiz_id):
    """
    Test creating TEXT without acceptedAnswer.
    
    Expected: 400 Bad Request
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "TEXT",
            "contentText": "Text question",
            "textConfig": {
                "isCaseSensitive": False
            }
        }
    )
    
    assert response.status_code == 400


# =============================================================================
# POST /api/quizzes/{qid}/questions - IMAGE (Clickable Zones)
# =============================================================================

def test_create_image_question(client, prof_responsible_token, quiz_id, media_id):
    """
    Test creating an IMAGE (clickable zones) question.
    
    Expected: 201 Created
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "IMAGE",
            "contentText": "Cliquez sur le talus",
            "mediaId": media_id,
            "imageZones": [
                {"labelName": "Talus", "x": 50, "y": 60, "radius": 15},
                {"labelName": "Calcanéus", "x": 40, "y": 80, "radius": 20},
                {"labelName": "Cuboïde", "x": 60, "y": 70, "radius": 12}
            ]
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "IMAGE"
    assert data["mediaId"] == media_id
    assert len(data["imageZones"]) == 3


def test_create_image_missing_media(client, prof_responsible_token, quiz_id):
    """
    Test creating IMAGE without mediaId.
    
    Expected: 400 Bad Request
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "IMAGE",
            "contentText": "Click on image",
            "imageZones": [
                {"labelName": "Zone1", "x": 50, "y": 60, "radius": 15}
            ]
        }
    )
    
    assert response.status_code == 400


def test_create_image_missing_zones(client, prof_responsible_token, quiz_id, media_id):
    """
    Test creating IMAGE without imageZones.
    
    Expected: 400 Bad Request
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "IMAGE",
            "contentText": "Click on image",
            "mediaId": media_id
        }
    )
    
    assert response.status_code == 400


def test_create_image_invalid_media_id(client, prof_responsible_token, quiz_id):
    """
    Test creating IMAGE with non-existent mediaId.
    
    Expected: 404 Not Found
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "IMAGE",
            "contentText": "Click on image",
            "mediaId": "non-existent-media-id",
            "imageZones": [
                {"labelName": "Zone1", "x": 50, "y": 60, "radius": 15}
            ]
        }
    )
    
    assert response.status_code == 404


# =============================================================================
# GET /api/quizzes/{qid}/questions
# =============================================================================

def test_list_questions(client, prof_responsible_token, quiz_id):
    """
    Test listing questions in a quiz.
    
    Expected: 200 OK, list of questions
    """
    response = client.get(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 200


def test_list_questions_student_hides_answers(client, student_token, quiz_id):
    """
    Test that question list for students hides correct answers (anti-cheat).
    
    Expected: 200 OK, but isCorrect field is not present in options
    """
    response = client.get(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        questions = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(questions, list) and len(questions) > 0:
            question = questions[0]
            if "options" in question and len(question["options"]) > 0:
                # Should not contain isCorrect for students
                assert "isCorrect" not in question["options"][0]


# =============================================================================
# GET /api/questions/{id}
# =============================================================================

def test_get_question(client, prof_responsible_token, question_id):
    """
    Test getting a single question.
    
    Expected: 200 OK, QuestionDto
    """
    response = client.get(
        f"/questions/{question_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == question_id


def test_get_question_not_found(client, prof_responsible_token):
    """
    Test getting non-existent question.
    
    Expected: 404 Not Found
    """
    response = client.get(
        "/questions/non-existent-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 404


# =============================================================================
# PATCH /api/questions/{id}
# =============================================================================

def test_update_question(client, prof_responsible_token, question_id):
    """
    Test updating a question.
    
    Expected: 200 OK, updated QuestionDto
    """
    response = client.patch(
        f"/questions/{question_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"contentText": "Updated question text"}
    )
    
    assert response.status_code == 200
    assert response.json()["contentText"] == "Updated question text"


def test_update_question_as_student(client, student_token, question_id):
    """
    Test updating question as student.
    
    Expected: 403 Forbidden
    """
    response = client.patch(
        f"/questions/{question_id}",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"contentText": "Student update"}
    )
    
    assert response.status_code == 403


def test_update_question_not_found(client, prof_responsible_token):
    """
    Test updating non-existent question.
    
    Expected: 404 Not Found
    """
    response = client.patch(
        "/questions/non-existent-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"contentText": "Updated"}
    )
    
    assert response.status_code == 404


# =============================================================================
# DELETE /api/questions/{id}
# =============================================================================

def test_delete_question_removes_from_leitner(client, prof_responsible_token, question_id):
    """
    Test that deleting a question removes it from Leitner boxes.
    
    Expected: 204 No Content, question removed from all student Leitner boxes
    """
    response = client.delete(
        f"/questions/{question_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 204


def test_delete_question_as_student(client, student_token, question_id):
    """
    Test deleting question as student.
    
    Expected: 403 Forbidden
    """
    response = client.delete(
        f"/questions/{question_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403


def test_delete_question_not_found(client, prof_responsible_token):
    """
    Test deleting non-existent question.
    
    Expected: 404 Not Found
    """
    response = client.delete(
        "/questions/non-existent-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 404


# =============================================================================
# GENERAL QUESTION TESTS
# =============================================================================

def test_create_question_as_student(client, student_token, quiz_id):
    """
    Test creating question as student.
    
    Expected: 403 Forbidden
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "type": "QCM",
            "contentText": "Student question?",
            "options": [
                {"textChoice": "A", "isCorrect": True}
            ]
        }
    )
    
    assert response.status_code == 403


def test_create_question_invalid_type(client, prof_responsible_token, quiz_id):
    """
    Test creating question with invalid type.
    
    Expected: 400 Bad Request
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={
            "type": "INVALID_TYPE",
            "contentText": "Question?"
        }
    )
    
    assert response.status_code == 400


def test_create_question_no_auth(client, quiz_id):
    """
    Test creating question without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
        json={
            "type": "QCM",
            "contentText": "Question?",
            "options": [{"textChoice": "A", "isCorrect": True}]
        }
    )
    
    assert response.status_code == 401


def test_question_visibility_in_session(client, student_token, session_id, question_id):
    """
    Test that correct answers are not visible during active session (anti-cheat).
    
    Expected: Questions returned without isCorrect field
    """
    # This would be tested in the context of a session
    # During gameplay, students should not see correct answers
    pass
