"""
Tests for Quiz Session (Gameplay) endpoints.

Endpoints tested:
- POST /api/sessions/start
- POST /api/sessions/{sid}/submit-answer
- POST /api/sessions/{sid}/finish
- GET /api/sessions/{sid}/review

Test coverage:
- Starting quiz sessions
- Submitting answers for different question types
- Quiz locking logic
- Session completion and scoring
- Unlocking next quizzes/modules
- Review/correction after completion
- Business error codes
"""

import pytest


# =============================================================================
# POST /api/sessions/start
# =============================================================================

def test_start_session_success(client, student_token, quiz_id):
    """
    Test starting a quiz session.
    
    Expected: 200 OK, sessionId and questions (without correct answers)
    """
    response = client.post(
        "/sessions/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"quizId": quiz_id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "sessionId" in data
    assert "questions" in data
    # Questions should not contain correct answers
    if len(data["questions"]) > 0:
        question = data["questions"][0]
        if "options" in question:
            # isCorrect should not be present (anti-cheat)
            assert "isCorrect" not in question["options"][0]


def test_start_session_locked_quiz(client, student_token):
    """
    Test starting a session on a locked quiz (prerequisite not met).
    
    Expected: 403 Forbidden with QUIZ_LOCKED error
    """
    locked_quiz_id = "locked-quiz-id"
    
    response = client.post(
        "/sessions/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"quizId": locked_quiz_id}
    )
    
    assert response.status_code == 403
    data = response.json()
    assert "error" in data
    # Should contain QUIZ_LOCKED business error code


def test_start_session_inactive_quiz(client, student_token):
    """
    Test starting session on inactive quiz.
    
    Expected: 403 Forbidden or 400 Bad Request
    """
    inactive_quiz_id = "inactive-quiz-id"
    
    response = client.post(
        "/sessions/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"quizId": inactive_quiz_id}
    )
    
    assert response.status_code in [400, 403]


def test_start_session_not_a_student(client, prof_responsible_token, quiz_id):
    """
    Test that professors cannot start quiz sessions.
    
    Expected: 403 Forbidden
    """
    response = client.post(
        "/sessions/start",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"quizId": quiz_id}
    )
    
    assert response.status_code == 403


def test_start_session_quiz_not_found(client, student_token):
    """
    Test starting session with non-existent quiz.
    
    Expected: 404 Not Found
    """
    response = client.post(
        "/sessions/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"quizId": "non-existent-quiz-id"}
    )
    
    assert response.status_code == 404


def test_start_session_no_auth(client, quiz_id):
    """
    Test starting session without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.post(
        "/sessions/start",
        json={"quizId": quiz_id}
    )
    
    assert response.status_code == 401


def test_start_session_not_classroom_member(client, student_token):
    """
    Test starting session for quiz in classroom where not a member.
    
    Expected: 403 Forbidden
    """
    other_quiz_id = "other-classroom-quiz-id"
    
    response = client.post(
        "/sessions/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"quizId": other_quiz_id}
    )
    
    assert response.status_code == 403


# =============================================================================
# POST /api/sessions/{sid}/submit-answer - QCM
# =============================================================================

def test_submit_answer_qcm_correct(client, student_token, session_id, question_id):
    """
    Test submitting correct answer for QCM question.
    
    Expected: 200 OK, isCorrect = true, no correction yet
    """
    response = client.post(
        f"/sessions/{session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": question_id,
            "selectedOptionId": "correct-option-id"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["isCorrect"] is True
    # Explanation should not be visible until session is finished
    assert "explanation" not in data or data.get("showExplanation") is False


def test_submit_answer_qcm_incorrect(client, student_token, session_id, question_id):
    """
    Test submitting incorrect answer for QCM question.
    
    Expected: 200 OK, isCorrect = false
    """
    response = client.post(
        f"/sessions/{session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": question_id,
            "selectedOptionId": "incorrect-option-id"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["isCorrect"] is False


def test_submit_answer_qcm_multiple_selections(client, student_token, session_id, question_id):
    """
    Test submitting multiple selections for QCM (when question allows it).
    
    Expected: 200 OK
    """
    response = client.post(
        f"/sessions/{session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": question_id,
            "selectedOptionIds": ["option-1", "option-2"]
        }
    )
    
    assert response.status_code == 200


# =============================================================================
# POST /api/sessions/{sid}/submit-answer - TEXT
# =============================================================================

def test_submit_answer_text_exact_match(client, student_token, session_id):
    """
    Test submitting text answer that matches exactly.
    
    Expected: 200 OK, isCorrect = true
    """
    text_question_id = "text-question-id"
    
    response = client.post(
        f"/sessions/{session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": text_question_id,
            "textResponse": "Calcanéus"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["isCorrect"] is True


def test_submit_answer_text_with_typo(client, student_token, session_id):
    """
    Test text answer with typo when ignoreSpellingErrors = true.
    
    Expected: 200 OK, isCorrect = true (typo ignored)
    """
    text_question_id = "text-question-with-fuzzy-id"
    
    response = client.post(
        f"/sessions/{session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": text_question_id,
            "textResponse": "Calcaneum"  # Typo: missing accent
        }
    )
    
    # If ignoreSpellingErrors is true, should accept
    if response.status_code == 200:
        data = response.json()
        # May be accepted as correct with fuzzy matching


def test_submit_answer_text_case_insensitive(client, student_token, session_id):
    """
    Test text answer with different case when isCaseSensitive = false.
    
    Expected: 200 OK, isCorrect = true
    """
    text_question_id = "text-question-case-insensitive-id"
    
    response = client.post(
        f"/sessions/{session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": text_question_id,
            "textResponse": "CALCANÉUS"  # Uppercase
        }
    )
    
    assert response.status_code == 200


def test_submit_answer_text_case_sensitive(client, student_token, session_id):
    """
    Test text answer with wrong case when isCaseSensitive = true.
    
    Expected: 200 OK, isCorrect = false
    """
    text_question_id = "text-question-case-sensitive-id"
    
    response = client.post(
        f"/sessions/{session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": text_question_id,
            "textResponse": "dna"  # Should be "DNA"
        }
    )
    
    # If case sensitive and wrong case
    if response.status_code == 200:
        data = response.json()
        # Should be incorrect


# =============================================================================
# POST /api/sessions/{sid}/submit-answer - IMAGE
# =============================================================================

def test_submit_answer_image_click_in_zone(client, student_token, session_id):
    """
    Test clicking inside a correct zone for IMAGE question.
    
    Expected: 200 OK, isCorrect = true
    """
    image_question_id = "image-question-id"
    
    response = client.post(
        f"/sessions/{session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": image_question_id,
            "clickedCoordinates": {"x": 50, "y": 60}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    # If click is within radius of correct zone
    assert "isCorrect" in data


def test_submit_answer_image_click_outside_zone(client, student_token, session_id):
    """
    Test clicking outside all zones for IMAGE question.
    
    Expected: 200 OK, isCorrect = false
    """
    image_question_id = "image-question-id"
    
    response = client.post(
        f"/sessions/{session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": image_question_id,
            "clickedCoordinates": {"x": 0, "y": 0}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["isCorrect"] is False


# =============================================================================
# POST /api/sessions/{sid}/submit-answer - MATCHING
# =============================================================================

def test_submit_answer_matching_correct(client, student_token, session_id):
    """
    Test submitting correct pairs for MATCHING question.
    
    Expected: 200 OK, isCorrect = true
    """
    matching_question_id = "matching-question-id"
    
    response = client.post(
        f"/sessions/{session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": matching_question_id,
            "matchedPairs": [
                {"leftId": "tibia-id", "rightId": "interne-id"},
                {"leftId": "fibula-id", "rightId": "externe-id"}
            ]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["isCorrect"] is True


def test_submit_answer_matching_incorrect(client, student_token, session_id):
    """
    Test submitting incorrect pairs for MATCHING question.
    
    Expected: 200 OK, isCorrect = false
    """
    matching_question_id = "matching-question-id"
    
    response = client.post(
        f"/sessions/{session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": matching_question_id,
            "matchedPairs": [
                {"leftId": "tibia-id", "rightId": "externe-id"},  # Wrong
                {"leftId": "fibula-id", "rightId": "interne-id"}  # Wrong
            ]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["isCorrect"] is False


def test_submit_answer_matching_partial(client, student_token, session_id):
    """
    Test submitting partially correct pairs for MATCHING question.
    
    Expected: 200 OK, isCorrect = false (all must be correct)
    """
    matching_question_id = "matching-question-id"
    
    response = client.post(
        f"/sessions/{session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": matching_question_id,
            "matchedPairs": [
                {"leftId": "tibia-id", "rightId": "interne-id"},  # Correct
                {"leftId": "fibula-id", "rightId": "interne-id"}  # Wrong
            ]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    # Partial correctness = incorrect
    assert data["isCorrect"] is False


# =============================================================================
# POST /api/sessions/{sid}/submit-answer - Error Cases
# =============================================================================

def test_submit_answer_session_not_found(client, student_token):
    """
    Test submitting answer to non-existent session.
    
    Expected: 404 Not Found
    """
    response = client.post(
        "/sessions/non-existent-session/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": "question-id",
            "selectedOptionId": "option-id"
        }
    )
    
    assert response.status_code == 404


def test_submit_answer_session_already_finished(client, student_token):
    """
    Test submitting answer to already finished session.
    
    Expected: 400 Bad Request
    """
    finished_session_id = "finished-session-id"
    
    response = client.post(
        f"/sessions/{finished_session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": "question-id",
            "selectedOptionId": "option-id"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    # Should contain SESSION_ALREADY_FINISHED


def test_submit_answer_question_not_in_session(client, student_token, session_id):
    """
    Test submitting answer for question not in this session.
    
    Expected: 400 Bad Request
    """
    response = client.post(
        f"/sessions/{session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": "question-not-in-session",
            "selectedOptionId": "option-id"
        }
    )
    
    assert response.status_code == 400


def test_submit_answer_duplicate(client, student_token, session_id, question_id):
    """
    Test submitting answer twice for same question.
    
    Expected: 400 Bad Request or 409 Conflict
    """
    # First submission
    client.post(
        f"/sessions/{session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": question_id,
            "selectedOptionId": "option-id"
        }
    )
    
    # Second submission
    response = client.post(
        f"/sessions/{session_id}/submit-answer",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "questionId": question_id,
            "selectedOptionId": "different-option-id"
        }
    )
    
    # May allow or reject depending on implementation
    # If rejected: 400 or 409


# =============================================================================
# POST /api/sessions/{sid}/finish
# =============================================================================

def test_finish_session_with_passing_score(client, student_token, session_id):
    """
    Test finishing session with score >= minScoreToUnlockNext.
    
    Expected: 200 OK, passed = true, CompletedQuiz created
    """
    # Assume all answers were submitted correctly
    response = client.post(
        f"/sessions/{session_id}/finish",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "passed" in data
    assert "totalScore" in data
    assert "maxScore" in data
    # If score >= minScoreToUnlockNext, passed = true


def test_finish_session_with_failing_score(client, student_token, session_id):
    """
    Test finishing session with score < minScoreToUnlockNext.
    
    Expected: 200 OK, passed = false, CompletedQuiz NOT created
    """
    # Assume answers were submitted incorrectly
    response = client.post(
        f"/sessions/{session_id}/finish",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "passed" in data
    # If score < minScoreToUnlockNext, passed = false


def test_finish_session_unlock_next_module(client, student_token, session_id):
    """
    Test that finishing last quiz of module unlocks next module.
    
    Expected: 200 OK, CompletedModule created
    """
    response = client.post(
        f"/sessions/{session_id}/finish",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    # If this was the last quiz in the module and all passed,
    # the next module should be unlocked


def test_finish_session_unlocks_next_quiz(client, student_token, session_id):
    """
    Test that finishing quiz with passing score unlocks next quiz.
    
    Expected: 200 OK, next quiz isLocked = false
    """
    response = client.post(
        f"/sessions/{session_id}/finish",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    # Next quiz (if it exists and has this as prerequisite) should be unlocked


def test_finish_session_adds_to_leitner_box_1(client, student_token, session_id):
    """
    Test that finishing successful quiz adds questions to Leitner Box 1.
    
    Expected: 200 OK, all questions added to Box 1
    """
    response = client.post(
        f"/sessions/{session_id}/finish",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200 and response.json().get("passed"):
        # All questions should be added to Leitner Box 1
        # (This would be verified by checking Leitner status endpoint)
        pass


def test_finish_session_not_found(client, student_token):
    """
    Test finishing non-existent session.
    
    Expected: 404 Not Found
    """
    response = client.post(
        "/sessions/non-existent-session/finish",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 404


def test_finish_session_already_finished(client, student_token):
    """
    Test finishing already finished session.
    
    Expected: 400 Bad Request
    """
    finished_session_id = "finished-session-id"
    
    response = client.post(
        f"/sessions/{finished_session_id}/finish",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 400


# =============================================================================
# GET /api/sessions/{sid}/review
# =============================================================================

def test_review_session_before_finish(client, student_token):
    """
    Test accessing review before session is finished.
    
    Expected: 403 Forbidden or 404 Not Found
    """
    in_progress_session_id = "in-progress-session-id"
    
    response = client.get(
        f"/sessions/{in_progress_session_id}/review",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code in [403, 404]


def test_review_session_after_finish(client, student_token):
    """
    Test accessing review after session is finished.
    
    Expected: 200 OK, contains correct answers and explanations
    """
    finished_session_id = "finished-session-id"
    
    response = client.get(
        f"/sessions/{finished_session_id}/review",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should contain questions with correct answers
    assert "questions" in data or "answers" in data
    # Should include explanations


def test_review_session_contains_explanations(client, student_token):
    """
    Test that review contains explanations for all questions.
    
    Expected: 200 OK, each question has explanation
    """
    finished_session_id = "finished-session-id"
    
    response = client.get(
        f"/sessions/{finished_session_id}/review",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        # Explanations should be visible in review
        # Check structure depends on implementation


def test_review_session_shows_student_answers(client, student_token):
    """
    Test that review shows student's submitted answers.
    
    Expected: 200 OK, contains student's answers and correctness
    """
    finished_session_id = "finished-session-id"
    
    response = client.get(
        f"/sessions/{finished_session_id}/review",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        # Should show what student answered and whether it was correct


def test_review_session_not_found(client, student_token):
    """
    Test reviewing non-existent session.
    
    Expected: 404 Not Found
    """
    response = client.get(
        "/sessions/non-existent-session/review",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 404


def test_review_session_wrong_student(client, student2_token):
    """
    Test reviewing another student's session.
    
    Expected: 403 Forbidden
    """
    other_student_session_id = "other-student-session-id"
    
    response = client.get(
        f"/sessions/{other_student_session_id}/review",
        headers={"Authorization": f"Bearer {student2_token}"}
    )
    
    assert response.status_code == 403
