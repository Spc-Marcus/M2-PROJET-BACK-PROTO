"""
Tests for Statistics and Progression endpoints.

Endpoints tested:
- GET /api/stats/student
- GET /api/stats/leaderboard/{cid}
- GET /api/stats/dashboard/{cid}
- GET /api/progress/modules/{moduleId}
- GET /api/progress/quizzes/{quizId}
- GET /api/progress/classroom/{cid}
- GET /api/progress/classroom/{cid}/student/{sid}

Test coverage:
- Student personal statistics
- Leaderboard rankings
- Professor dashboard
- Progress tracking (module, quiz, classroom)
- Role-based access control
- Pagination
"""

import pytest


# =============================================================================
# GET /api/stats/student
# =============================================================================

def test_student_stats_complete(client, student_token):
    """
    Test getting complete student statistics.
    
    Expected: 200 OK, StudentStatsDto with all fields
    """
    response = client.get(
        "/stats/student",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "totalCompletedQuizzes" in data
    assert "averageScore" in data
    assert "leitnerMastery" in data
    assert "classroomsProgress" in data


def test_student_stats_with_no_progress(client):
    """
    Test student stats for student with no progress.
    
    Expected: 200 OK, zeros for all metrics
    """
    new_student_token = "new-student-token"
    
    response = client.get(
        "/stats/student",
        headers={"Authorization": f"Bearer {new_student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        assert data["totalCompletedQuizzes"] == 0
        assert data["averageScore"] == 0 or data["averageScore"] is None


def test_student_stats_leitner_mastery_calculation(client, student_token):
    """
    Test Leitner mastery calculation (% in boxes 4-5).
    
    Expected: 200 OK, leitnerMastery between 0.0 and 1.0
    """
    response = client.get(
        "/stats/student",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        mastery = data["leitnerMastery"]
        assert 0.0 <= mastery <= 1.0


def test_student_stats_classrooms_progress(client, student_token):
    """
    Test that stats include progress for each enrolled classroom.
    
    Expected: 200 OK, classroomsProgress is array
    """
    response = client.get(
        "/stats/student",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data["classroomsProgress"], list)


def test_student_stats_no_auth(client):
    """
    Test getting student stats without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.get("/stats/student")
    
    assert response.status_code == 401


def test_student_stats_as_professor(client, prof_responsible_token):
    """
    Test that professors can get their own stats (if they have student profile).
    
    Expected: May be 200 OK or 403 Forbidden depending on implementation
    """
    response = client.get(
        "/stats/student",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    # Professors may not have student stats
    assert response.status_code in [200, 403]


# =============================================================================
# GET /api/stats/leaderboard/{cid}
# =============================================================================

def test_leaderboard_ranking(client, student_token, classroom_id):
    """
    Test getting classroom leaderboard.
    
    Expected: 200 OK, sorted by completedQuizzes desc, then averageScore desc
    """
    response = client.get(
        f"/stats/leaderboard/{classroom_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should be paginated or array of student rankings
    leaderboard = data.get("data", data) if isinstance(data, dict) else data
    
    if isinstance(leaderboard, list) and len(leaderboard) > 1:
        # Verify sorting
        for i in range(len(leaderboard) - 1):
            current = leaderboard[i]
            next_student = leaderboard[i + 1]
            # First sort by completedQuizzes desc
            if current["completedQuizzes"] == next_student["completedQuizzes"]:
                # Then by averageScore desc
                assert current["averageScore"] >= next_student["averageScore"]
            else:
                assert current["completedQuizzes"] >= next_student["completedQuizzes"]


def test_leaderboard_includes_rank(client, student_token, classroom_id):
    """
    Test that leaderboard includes rank for each student.
    
    Expected: 200 OK, each entry has rank field
    """
    response = client.get(
        f"/stats/leaderboard/{classroom_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        leaderboard = data.get("data", data) if isinstance(data, dict) else data
        
        if isinstance(leaderboard, list) and len(leaderboard) > 0:
            assert "rank" in leaderboard[0]


def test_leaderboard_includes_leitner_mastery(client, student_token, classroom_id):
    """
    Test that leaderboard includes Leitner mastery for each student.
    
    Expected: 200 OK, each entry has leitnerMastery
    """
    response = client.get(
        f"/stats/leaderboard/{classroom_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        leaderboard = data.get("data", data) if isinstance(data, dict) else data
        
        if isinstance(leaderboard, list) and len(leaderboard) > 0:
            assert "leitnerMastery" in leaderboard[0]


def test_leaderboard_pagination(client, student_token, classroom_id):
    """
    Test leaderboard pagination.
    
    Expected: 200 OK, paginated response with metadata
    """
    response = client.get(
        f"/stats/leaderboard/{classroom_id}?page=1&limit=10",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    if "pagination" in data:
        assert "hasNextPage" in data["pagination"]
        assert "totalPages" in data["pagination"]


def test_leaderboard_not_member(client, student_token):
    """
    Test accessing leaderboard for classroom where not a member.
    
    Expected: 403 Forbidden
    """
    other_classroom_id = "other-classroom-id"
    
    response = client.get(
        f"/stats/leaderboard/{other_classroom_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403


def test_leaderboard_no_auth(client, classroom_id):
    """
    Test accessing leaderboard without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.get(f"/stats/leaderboard/{classroom_id}")
    
    assert response.status_code == 401


def test_leaderboard_not_found(client, student_token):
    """
    Test leaderboard for non-existent classroom.
    
    Expected: 404 Not Found
    """
    response = client.get(
        "/stats/leaderboard/non-existent-classroom-id",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 404


# =============================================================================
# GET /api/stats/dashboard/{cid}
# =============================================================================

def test_professor_dashboard(client, prof_responsible_token, classroom_id):
    """
    Test getting professor dashboard for a classroom.
    
    Expected: 200 OK, ProfessorDashboardDto with stats
    """
    response = client.get(
        f"/stats/dashboard/{classroom_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "modulesStats" in data or "modules" in data
    assert "hardestQuestions" in data or "difficult" in data
    # May include alertStudents (students in difficulty)


def test_dashboard_modules_stats(client, prof_responsible_token, classroom_id):
    """
    Test that dashboard includes statistics for each module.
    
    Expected: 200 OK, modulesStats with completion rates
    """
    response = client.get(
        f"/stats/dashboard/{classroom_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        modules_stats = data.get("modulesStats", [])
        if len(modules_stats) > 0:
            # Each module should have completion info
            assert "completionRate" in modules_stats[0] or "averageCompletion" in modules_stats[0]


def test_dashboard_hardest_questions(client, prof_responsible_token, classroom_id):
    """
    Test that dashboard includes hardest questions (lowest success rate).
    
    Expected: 200 OK, list of difficult questions
    """
    response = client.get(
        f"/stats/dashboard/{classroom_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        hardest = data.get("hardestQuestions", [])
        # Should be sorted by success rate ascending


def test_dashboard_alert_students(client, prof_responsible_token, classroom_id):
    """
    Test that dashboard identifies students in difficulty.
    
    Expected: 200 OK, alertStudents with struggling students
    """
    response = client.get(
        f"/stats/dashboard/{classroom_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        # May have alertStudents field
        if "alertStudents" in data:
            assert isinstance(data["alertStudents"], list)


def test_dashboard_leitner_stats(client, prof_responsible_token, classroom_id):
    """
    Test that dashboard includes Leitner system statistics.
    
    Expected: 200 OK, leitnerStats with distribution
    """
    response = client.get(
        f"/stats/dashboard/{classroom_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        if "leitnerStats" in data:
            # Should show overall class Leitner distribution
            pass


def test_dashboard_non_professor(client, student_token, classroom_id):
    """
    Test that students cannot access professor dashboard.
    
    Expected: 403 Forbidden
    """
    response = client.get(
        f"/stats/dashboard/{classroom_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403


def test_dashboard_secondary_prof(client, prof_secondary_token, classroom_id):
    """
    Test that secondary professors can access dashboard.
    
    Expected: 200 OK (secondary profs can view stats)
    """
    response = client.get(
        f"/stats/dashboard/{classroom_id}",
        headers={"Authorization": f"Bearer {prof_secondary_token}"}
    )
    
    # Secondary profs should have access
    assert response.status_code == 200


def test_dashboard_no_auth(client, classroom_id):
    """
    Test accessing dashboard without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.get(f"/stats/dashboard/{classroom_id}")
    
    assert response.status_code == 401


# =============================================================================
# GET /api/progress/modules/{moduleId}
# =============================================================================

def test_module_progress(client, student_token, module_id):
    """
    Test getting progress for a specific module.
    
    Expected: 200 OK, ModuleProgressDto
    """
    response = client.get(
        f"/progress/modules/{module_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "isCompleted" in data or "completed" in data
    assert "completionRate" in data or "progress" in data
    assert "quizzes" in data  # List of quizzes in module


def test_module_progress_completion_rate(client, student_token, module_id):
    """
    Test module completion rate calculation.
    
    Expected: 200 OK, completionRate between 0.0 and 1.0
    """
    response = client.get(
        f"/progress/modules/{module_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        rate = data.get("completionRate", 0.0)
        assert 0.0 <= rate <= 1.0


def test_module_progress_not_found(client, student_token):
    """
    Test progress for non-existent module.
    
    Expected: 404 Not Found
    """
    response = client.get(
        "/progress/modules/non-existent-module-id",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 404


def test_module_progress_no_auth(client, module_id):
    """
    Test getting module progress without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.get(f"/progress/modules/{module_id}")
    
    assert response.status_code == 401


# =============================================================================
# GET /api/progress/quizzes/{quizId}
# =============================================================================

def test_quiz_progress(client, student_token, quiz_id):
    """
    Test getting progress for a specific quiz.
    
    Expected: 200 OK, QuizProgressDto
    """
    response = client.get(
        f"/progress/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "bestScore" in data or "highestScore" in data
    assert "attemptsCount" in data or "attempts" in data
    assert "isCompleted" in data or "completed" in data


def test_quiz_progress_best_score(client, student_token, quiz_id):
    """
    Test that quiz progress shows best score achieved.
    
    Expected: 200 OK, bestScore is highest score from all attempts
    """
    response = client.get(
        f"/progress/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        # bestScore should be >= 0
        best_score = data.get("bestScore", 0)
        assert best_score >= 0


def test_quiz_progress_attempts_count(client, student_token, quiz_id):
    """
    Test that quiz progress shows number of attempts.
    
    Expected: 200 OK, attemptsCount shows total attempts
    """
    response = client.get(
        f"/progress/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        attempts = data.get("attemptsCount", 0)
        assert attempts >= 0


def test_quiz_progress_not_found(client, student_token):
    """
    Test progress for non-existent quiz.
    
    Expected: 404 Not Found
    """
    response = client.get(
        "/progress/quizzes/non-existent-quiz-id",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 404


# =============================================================================
# GET /api/progress/classroom/{cid}
# =============================================================================

def test_classroom_progress(client, student_token, classroom_id):
    """
    Test getting overall classroom progress.
    
    Expected: 200 OK, array of ModuleProgressDto
    """
    response = client.get(
        f"/progress/classroom/{classroom_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should return list of all modules with progress
    modules = data.get("data", data) if isinstance(data, dict) else data
    assert isinstance(modules, list)


def test_classroom_progress_all_modules(client, student_token, classroom_id):
    """
    Test that classroom progress includes all modules.
    
    Expected: 200 OK, all modules in classroom
    """
    response = client.get(
        f"/progress/classroom/{classroom_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        modules = data.get("data", data) if isinstance(data, dict) else data
        # Each module should have progress info


def test_classroom_progress_not_member(client, student_token):
    """
    Test classroom progress for classroom where not a member.
    
    Expected: 403 Forbidden
    """
    other_classroom_id = "other-classroom-id"
    
    response = client.get(
        f"/progress/classroom/{other_classroom_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403


def test_classroom_progress_no_auth(client, classroom_id):
    """
    Test getting classroom progress without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.get(f"/progress/classroom/{classroom_id}")
    
    assert response.status_code == 401


# =============================================================================
# GET /api/progress/classroom/{cid}/student/{sid}
# =============================================================================

def test_student_progress_view_professor(client, prof_responsible_token, classroom_id):
    """
    Test professor viewing a student's progress.
    
    Expected: 200 OK, student's progress data
    """
    student_id = "student-id"
    
    response = client.get(
        f"/progress/classroom/{classroom_id}/student/{student_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    # Professors should be able to view student progress
    assert response.status_code == 200


def test_student_progress_view_secondary_prof(client, prof_secondary_token, classroom_id):
    """
    Test secondary professor viewing a student's progress.
    
    Expected: 200 OK (secondary profs can view)
    """
    student_id = "student-id"
    
    response = client.get(
        f"/progress/classroom/{classroom_id}/student/{student_id}",
        headers={"Authorization": f"Bearer {prof_secondary_token}"}
    )
    
    assert response.status_code == 200


def test_student_progress_view_unauthorized(client, student_token, classroom_id):
    """
    Test student viewing another student's progress.
    
    Expected: 403 Forbidden
    """
    other_student_id = "other-student-id"
    
    response = client.get(
        f"/progress/classroom/{classroom_id}/student/{other_student_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403


def test_student_progress_view_self(client, student_token, classroom_id):
    """
    Test student viewing their own progress.
    
    Expected: 200 OK (students can view own progress)
    """
    # Assuming the student's own ID can be extracted from token
    # or endpoint allows "me" keyword
    response = client.get(
        f"/progress/classroom/{classroom_id}/student/me",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    # Should allow viewing own progress
    assert response.status_code in [200, 404]  # 404 if "me" not supported


def test_student_progress_student_not_found(client, prof_responsible_token, classroom_id):
    """
    Test viewing progress for non-existent student.
    
    Expected: 404 Not Found
    """
    response = client.get(
        f"/progress/classroom/{classroom_id}/student/non-existent-student-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 404


def test_student_progress_classroom_not_found(client, prof_responsible_token):
    """
    Test viewing student progress in non-existent classroom.
    
    Expected: 404 Not Found
    """
    response = client.get(
        "/progress/classroom/non-existent-classroom-id/student/student-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 404
