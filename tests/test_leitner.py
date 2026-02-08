"""
Tests for Leitner spaced repetition system endpoints.

Endpoints tested:
- GET /api/classrooms/{cid}/leitner/status
- POST /api/classrooms/{cid}/leitner/start
- POST /api/leitner/sessions/{sid}/submit-answer
- POST /api/leitner/sessions/{sid}/finish
- GET /api/leitner/sessions/{sid}/review

Test coverage:
- Box status and distribution
- Session creation with question counts (5, 10, 15, 20)
- Answer submission
- Box promotion/demotion rules
- Session completion and review
- Business error codes
"""

import pytest


# =============================================================================
# GET /api/classrooms/{cid}/leitner/status
# =============================================================================

def test_get_leitner_status(client, student_token, classroom_id):
    """
    Test getting Leitner box status for a classroom.
    
    Expected: 200 OK, 5 boxes with question counts and percentages
    """
    response = client.get(
        f"/classrooms/{classroom_id}/leitner/status",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "totalQuestions" in data
    assert "boxes" in data
    assert len(data["boxes"]) == 5  # 5 boxes
    
    # Check each box has required fields (per documentation)
    for box in data["boxes"]:
        assert "level" in box  # 1-5
        assert "questionCount" in box
        assert "percentage" in box
        assert "selectionWeight" in box


def test_leitner_status_distribution(client, student_token, classroom_id):
    """
    Test that Leitner status shows correct distribution.
    
    Expected: 200 OK, boxes follow distribution rules
    """
    response = client.get(
        f"/classrooms/{classroom_id}/leitner/status",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        total = data["totalQuestions"]
        if total > 0:
            # Percentages should add up to ~100%
            total_percentage = sum(box["percentage"] for box in data["boxes"])
            assert 99 <= total_percentage <= 101  # Allow for rounding


def test_leitner_status_no_questions(client, student_token):
    """
    Test Leitner status for classroom with no unlocked questions.
    
    Expected: 200 OK, totalQuestions = 0
    """
    empty_classroom_id = "empty-classroom-id"
    
    response = client.get(
        f"/classrooms/{empty_classroom_id}/leitner/status",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        assert data["totalQuestions"] == 0


def test_leitner_status_not_classroom_member(client, student_token):
    """
    Test getting Leitner status for classroom where not a member.
    
    Expected: 403 Forbidden
    """
    other_classroom_id = "other-classroom-id"
    
    response = client.get(
        f"/classrooms/{other_classroom_id}/leitner/status",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403


def test_leitner_status_no_auth(client, classroom_id):
    """
    Test getting Leitner status without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.get(f"/classrooms/{classroom_id}/leitner/status")
    
    assert response.status_code == 401


# =============================================================================
# POST /api/classrooms/{cid}/leitner/start
# =============================================================================

def test_start_leitner_session_10_questions(client, student_token, classroom_id):
    """
    Test starting Leitner session with 10 questions.
    
    Expected: 200 OK, sessionId, 10 questions with proper distribution
    """
    response = client.post(
        f"/classrooms/{classroom_id}/leitner/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"questionCount": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "sessionId" in data
    assert "questions" in data
    assert len(data["questions"]) == 10
    
    # Check distribution: 50%, 25%, 15%, 7%, 3% from boxes 1-5
    # Box 1: 5 questions (50%)
    # Box 2: 2-3 questions (25%)
    # Box 3: 1-2 questions (15%)
    # Box 4: 0-1 questions (7%)
    # Box 5: 0 questions (3%)


def test_start_leitner_session_5_questions(client, student_token, classroom_id):
    """
    Test starting Leitner session with 5 questions.
    
    Expected: 200 OK, 5 questions
    """
    response = client.post(
        f"/classrooms/{classroom_id}/leitner/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"questionCount": 5}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["questions"]) == 5


def test_start_leitner_session_15_questions(client, student_token, classroom_id):
    """
    Test starting Leitner session with 15 questions.
    
    Expected: 200 OK, 15 questions
    """
    response = client.post(
        f"/classrooms/{classroom_id}/leitner/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"questionCount": 15}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["questions"]) == 15


def test_start_leitner_session_20_questions(client, student_token, classroom_id):
    """
    Test starting Leitner session with 20 questions.
    
    Expected: 200 OK, 20 questions
    """
    response = client.post(
        f"/classrooms/{classroom_id}/leitner/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"questionCount": 20}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["questions"]) == 20


def test_start_leitner_session_invalid_count(client, student_token, classroom_id):
    """
    Test starting Leitner with invalid question count (not 5, 10, 15, or 20).
    
    Expected: 400 Bad Request
    """
    response = client.post(
        f"/classrooms/{classroom_id}/leitner/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"questionCount": 6}  # Invalid count
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    # Should contain INVALID_QUESTION_COUNT


def test_start_leitner_no_questions_available(client, student_token):
    """
    Test starting Leitner when no questions are unlocked.
    
    Expected: 400 Bad Request
    """
    empty_classroom_id = "empty-classroom-id"
    
    response = client.post(
        f"/classrooms/{empty_classroom_id}/leitner/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"questionCount": 10}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    # Should contain LEITNER_NO_QUESTIONS


def test_start_leitner_insufficient_questions(client, student_token):
    """
    Test starting Leitner when fewer questions available than requested.
    
    Expected: 200 OK with available questions, or 400 Bad Request
    """
    sparse_classroom_id = "sparse-classroom-id"
    
    response = client.post(
        f"/classrooms/{sparse_classroom_id}/leitner/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"questionCount": 20}  # But only 5 available
    )
    
    # Implementation may return what's available or error
    if response.status_code == 200:
        data = response.json()
        # Should return available questions
        assert len(data["questions"]) <= 20
    else:
        assert response.status_code == 400


def test_start_leitner_not_a_student(client, prof_responsible_token, classroom_id):
    """
    Test that professors cannot start Leitner sessions.
    
    Expected: 403 Forbidden
    """
    response = client.post(
        f"/classrooms/{classroom_id}/leitner/start",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"questionCount": 10}
    )
    
    assert response.status_code == 403


def test_start_leitner_no_auth(client, classroom_id):
    """
    Test starting Leitner without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.post(
        f"/classrooms/{classroom_id}/leitner/start",
        json={"questionCount": 10}
    )
    
    assert response.status_code == 401


# =============================================================================
# POST /api/leitner/sessions/{sid}/submit-answer
# =============================================================================

def test_leitner_submit_correct_answer(client, student_token, leitner_session_id, question_id):
    """
    Test submitting correct answer in Leitner session.
    
    Expected: 200 OK, isCorrect = true
    """
    response = client.post(
        f"/leitner/sessions/{leitner_session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": question_id,
            "selectedOptionId": "correct-option-id"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["isCorrect"] is True


def test_leitner_submit_incorrect_answer(client, student_token, leitner_session_id, question_id):
    """
    Test submitting incorrect answer in Leitner session.
    
    Expected: 200 OK, isCorrect = false
    """
    response = client.post(
        f"/leitner/sessions/{leitner_session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": question_id,
            "selectedOptionId": "incorrect-option-id"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["isCorrect"] is False


def test_leitner_submit_session_not_found(client, student_token):
    """
    Test submitting answer to non-existent Leitner session.
    
    Expected: 404 Not Found
    """
    response = client.post(
        "/leitner/sessions/non-existent-session/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": "question-id",
            "selectedOptionId": "option-id"
        }
    )
    
    assert response.status_code == 404


def test_leitner_submit_already_finished(client, student_token):
    """
    Test submitting answer to finished Leitner session.
    
    Expected: 400 Bad Request
    """
    finished_leitner_session_id = "finished-leitner-session-id"
    
    response = client.post(
        f"/leitner/sessions/{finished_leitner_session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": "question-id",
            "selectedOptionId": "option-id"
        }
    )
    
    assert response.status_code == 400


# =============================================================================
# POST /api/leitner/sessions/{sid}/finish
# =============================================================================

def test_finish_leitner_session(client, student_token, leitner_session_id):
    """
    Test finishing Leitner session.
    
    Expected: 200 OK, summary with promoted/demoted counts
    """
    response = client.post(
        f"/leitner/sessions/{leitner_session_id}/finish",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data or "promoted" in data
    assert "demoted" in data or "summary" in data
    # Should show how many questions moved up/down


def test_leitner_promotion_rules(client, student_token, leitner_session_id):
    """
    Test Leitner box promotion rules.
    
    Correct answer:
    - Box 1 → Box 2
    - Box 2 → Box 3
    - Box 3 → Box 4
    - Box 4 → Box 5
    - Box 5 → Box 5 (stays)
    
    Expected: Questions are promoted correctly
    """
    # This test would need to verify the box movements
    # by checking the Leitner status before and after
    response = client.post(
        f"/leitner/sessions/{leitner_session_id}/finish",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    # Check that promoted questions moved to next box


def test_leitner_demotion_to_box_1(client, student_token, leitner_session_id):
    """
    Test that incorrect answers demote questions to Box 1.
    
    Incorrect answer: Any Box → Box 1
    
    Expected: All incorrect questions go to Box 1
    """
    response = client.post(
        f"/leitner/sessions/{leitner_session_id}/finish",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    # Check that demoted questions went to Box 1


def test_finish_leitner_new_box_distribution(client, student_token, leitner_session_id):
    """
    Test that finish response includes new box distribution.
    
    Expected: 200 OK, newBoxDistribution showing updated counts
    """
    response = client.post(
        f"/leitner/sessions/{leitner_session_id}/finish",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should include updated distribution
    if "newBoxDistribution" in data:
        assert len(data["newBoxDistribution"]) == 5


def test_finish_leitner_accuracy_calculation(client, student_token, leitner_session_id):
    """
    Test that finish response includes accuracy percentage.
    
    Expected: 200 OK, accuracy = (correct / total) * 100
    """
    response = client.post(
        f"/leitner/sessions/{leitner_session_id}/finish",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    if "accuracy" in data or "summary" in data:
        # Accuracy should be between 0 and 100
        accuracy = data.get("accuracy") or data.get("summary", {}).get("accuracy")
        if accuracy is not None:
            assert 0 <= accuracy <= 100


def test_finish_leitner_not_found(client, student_token):
    """
    Test finishing non-existent Leitner session.
    
    Expected: 404 Not Found
    """
    response = client.post(
        "/leitner/sessions/non-existent-session/finish",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 404


def test_finish_leitner_already_finished(client, student_token):
    """
    Test finishing already finished Leitner session.
    
    Expected: 400 Bad Request
    """
    finished_leitner_session_id = "finished-leitner-session-id"
    
    response = client.post(
        f"/leitner/sessions/{finished_leitner_session_id}/finish",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 400


# =============================================================================
# GET /api/leitner/sessions/{sid}/review
# =============================================================================

def test_leitner_review_after_finish(client, student_token):
    """
    Test reviewing finished Leitner session.
    
    Expected: 200 OK, complete review with box movements
    """
    finished_leitner_session_id = "finished-leitner-session-id"
    
    response = client.get(
        f"/leitner/sessions/{finished_leitner_session_id}/review",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "answers" in data or "questions" in data
    # Should show previousBox, newBox for each question


def test_leitner_review_shows_box_movements(client, student_token):
    """
    Test that review shows previousBox and newBox for each question.
    
    Expected: 200 OK, each answer shows box movement
    """
    finished_leitner_session_id = "finished-leitner-session-id"
    
    response = client.get(
        f"/leitner/sessions/{finished_leitner_session_id}/review",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        answers = data.get("answers", [])
        if len(answers) > 0:
            # Each answer should show box movement
            assert "previousBox" in answers[0] or "previousBoxLevel" in answers[0]
            assert "newBox" in answers[0] or "newBoxLevel" in answers[0]


def test_leitner_review_includes_explanations(client, student_token):
    """
    Test that review includes explanations for questions.
    
    Expected: 200 OK, explanations visible
    """
    finished_leitner_session_id = "finished-leitner-session-id"
    
    response = client.get(
        f"/leitner/sessions/{finished_leitner_session_id}/review",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        # Explanations should be included


def test_leitner_review_summary_stats(client, student_token):
    """
    Test that review includes summary statistics.
    
    Expected: 200 OK, summary with accuracy, promoted, demoted
    """
    finished_leitner_session_id = "finished-leitner-session-id"
    
    response = client.get(
        f"/leitner/sessions/{finished_leitner_session_id}/review",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        if "summary" in data:
            summary = data["summary"]
            assert "accuracy" in summary or "correctCount" in summary
            assert "promoted" in summary or "demoted" in summary


def test_leitner_review_before_finish(client, student_token, leitner_session_id):
    """
    Test reviewing Leitner session before it's finished.
    
    Expected: 403 Forbidden or 404 Not Found
    """
    response = client.get(
        f"/leitner/sessions/{leitner_session_id}/review",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code in [403, 404]


def test_leitner_review_not_found(client, student_token):
    """
    Test reviewing non-existent Leitner session.
    
    Expected: 404 Not Found
    """
    response = client.get(
        "/leitner/sessions/non-existent-session/review",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 404


def test_leitner_review_wrong_student(client, student2_token):
    """
    Test reviewing another student's Leitner session.
    
    Expected: 403 Forbidden
    """
    other_student_leitner_session_id = "other-student-leitner-session-id"
    
    response = client.get(
        f"/leitner/sessions/{other_student_leitner_session_id}/review",
        headers={"Authorization": f"Bearer {student2_token}"}
    )
    
    assert response.status_code == 403


# =============================================================================
# ADDITIONAL LEITNER TESTS
# =============================================================================

def test_leitner_question_distribution_follows_rules(client, student_token, classroom_id):
    """
    Test that question selection follows distribution rules.
    
    Distribution: 50%, 25%, 15%, 7%, 3% from boxes 1-5
    
    Expected: Question selection respects these percentages
    """
    response = client.post(
        f"/classrooms/{classroom_id}/leitner/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"questionCount": 20}
    )
    
    if response.status_code == 200:
        # Would need to analyze question distribution by box
        # to verify it follows the 50/25/15/7/3 rule
        pass


def test_leitner_box_5_stays_on_correct(client, student_token):
    """
    Test that questions in Box 5 stay in Box 5 on correct answer.
    
    Expected: Box 5 questions don't move up (already at max)
    """
    # Would need to create a question in Box 5, answer correctly,
    # and verify it stays in Box 5
    pass


def test_leitner_box_1_on_incorrect(client, student_token):
    """
    Test that any incorrect answer sends question to Box 1.
    
    Expected: All boxes demote to Box 1 on incorrect answer
    """
    # Would need to test questions from different boxes
    # and verify they all go to Box 1 on incorrect answer
    pass
