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
    },
    "extra_student": {
        "email": "student@univ-rennes.fr",
        "password": "student123",
        "role": "STUDENT",
        "name": "Extra Student",
        "level": "L1"
    },
    "duplicate_student": {
        "email": "duplicate.student@univ-rennes.fr",
        "password": "student123",
        "role": "STUDENT",
        "name": "Duplicate Student",
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
def test_engine():
    """
    Create a test database engine for the entire test session.
    Uses SQLite in-memory database with async support.
    """
    import asyncio
    
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    async def create_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    asyncio.get_event_loop().run_until_complete(create_tables())
    
    yield test_engine
    
    async def drop_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await test_engine.dispose()
    
    asyncio.get_event_loop().run_until_complete(drop_tables())


@pytest.fixture(scope="session")
def test_session_maker(test_engine):
    """Create a session maker for the test database."""
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def seed_test_users(test_session_maker):
    """
    Seed the test database with users and hardcoded test data once for the entire session.
    This runs automatically before any tests.
    Stores generated user IDs back into TEST_USERS for token creation.
    """
    import asyncio
    
    async def _seed():
        async with test_session_maker() as session:
            for key, user_data in TEST_USERS.items():
                user = User(
                    email=user_data["email"],
                    password=get_password_hash(user_data["password"]),
                    name=user_data["name"],
                    role=Role[user_data["role"]]
                )
                session.add(user)
                await session.flush()
                
                # Store the generated ID back into TEST_USERS so tokens use real IDs
                user_data["id"] = user.id
                
                if user_data["role"] == "STUDENT":
                    from app.models.user import Level
                    profile = StudentProfile(
                        user_id=user.id,
                        level=Level[user_data.get("level", "L1")]
                    )
                    session.add(profile)
                elif user_data["role"] == "TEACHER":
                    profile = TeacherProfile(
                        user_id=user.id,
                        faculty_department=user_data.get("department")
                    )
                    session.add(profile)
            
            # Create a classroom with the known TEST_CLASSROOM_CODE
            from app.models.classroom import Classroom
            prof_id = TEST_USERS["prof_responsible"]["id"]
            test_classroom = Classroom(
                name="Test Classroom ANAT26",
                level=Level.L1,
                code=TEST_CLASSROOM_CODE,
                responsible_professor_id=prof_id
            )
            session.add(test_classroom)
            
            # =============================================
            # Seed users with hardcoded IDs used by tests
            # =============================================

            # teacher-to-remove-id: used by test_remove_teacher_success
            teacher_to_remove = User(
                id="teacher-to-remove-id",
                email="teacher.remove@univ-rennes.fr",
                password=get_password_hash("prof123"),
                name="Teacher To Remove",
                role=Role.TEACHER
            )
            session.add(teacher_to_remove)
            await session.flush()
            tp_remove = TeacherProfile(
                user_id="teacher-to-remove-id",
                faculty_department="Anatomie"
            )
            session.add(tp_remove)

            # student-to-remove-id: used by test_remove_student_success
            student_to_remove = User(
                id="student-to-remove-id",
                email="student.remove@univ-rennes.fr",
                password=get_password_hash("student123"),
                name="Student To Remove",
                role=Role.STUDENT
            )
            session.add(student_to_remove)
            await session.flush()
            sp_remove = StudentProfile(
                user_id="student-to-remove-id",
                level=Level.L1
            )
            session.add(sp_remove)

            # student-id: used by test_student_progress_view_professor/secondary_prof
            student_progress = User(
                id="student-id",
                email="student.progress@univ-rennes.fr",
                password=get_password_hash("student123"),
                name="Progress Student",
                role=Role.STUDENT
            )
            session.add(student_progress)
            await session.flush()
            sp_progress = StudentProfile(
                user_id="student-id",
                level=Level.L1
            )
            session.add(sp_progress)

            # new.teacher@univ-rennes.fr: used by test_add_teacher_success
            new_teacher = User(
                email="add.teacher@univ-rennes.fr",
                password=get_password_hash("prof123"),
                name="Add Teacher",
                role=Role.TEACHER
            )
            session.add(new_teacher)
            await session.flush()
            tp_new = TeacherProfile(
                user_id=new_teacher.id,
                faculty_department="Anatomie"
            )
            session.add(tp_new)

            # =============================================
            # Seed hardcoded classrooms
            # =============================================

            # empty-classroom-id: used by test_start_leitner_no_questions_available
            empty_classroom = Classroom(
                id="empty-classroom-id",
                name="Empty Classroom",
                level=Level.L1,
                code="EMPTY1",
                responsible_professor_id=prof_id
            )
            session.add(empty_classroom)

            # sparse-classroom-id: used by test_start_leitner_insufficient_questions
            sparse_classroom = Classroom(
                id="sparse-classroom-id",
                name="Sparse Classroom",
                level=Level.L1,
                code="SPARS1",
                responsible_professor_id=prof_id
            )
            session.add(sparse_classroom)

            # other-classroom for the "other-classroom-quiz-id" quiz
            # student1 is NOT enrolled here -> used for test_leaderboard_not_member (403)
            other_classroom = Classroom(
                id="other-classroom-id",
                name="Other Classroom",
                level=Level.L1,
                code="OTHER1",
                responsible_professor_id=prof_id
            )
            session.add(other_classroom)

            await session.flush()

            # Enroll student1 in empty + sparse + other classrooms for membership checks
            from app.models.classroom import ClassroomStudent
            student1_id = TEST_USERS["student1"]["id"]

            # Enroll student1 in empty classroom (so membership passes but no leitner boxes)
            session.add(ClassroomStudent(classroom_id="empty-classroom-id", student_id=student1_id))
            # Enroll student1 in sparse classroom
            session.add(ClassroomStudent(classroom_id="sparse-classroom-id", student_id=student1_id))

            # =============================================
            # Seed modules/quizzes/questions with hardcoded IDs
            # =============================================
            from app.models.module import Module
            from app.models.quiz import Quiz
            from app.models.question import Question, QuestionOption, MatchingPair, ImageZone, TextConfig, QuestionType
            from app.models.session import QuizSession, SessionAnswer, SessionStatus
            from app.models.leitner import LeitnerBox, LeitnerSession, LeitnerSessionAnswer
            from app.models.media import Media

            # Module in the other classroom
            other_module = Module(
                id="other-module-id",
                classroom_id="other-classroom-id",
                name="Other Module"
            )
            session.add(other_module)

            # other-classroom-quiz-id: quiz in another classroom (student not enrolled)
            other_quiz = Quiz(
                id="other-classroom-quiz-id",
                module_id="other-module-id",
                title="Other Classroom Quiz",
                is_active=True,
                min_score_to_unlock_next=0,
                created_by_id=prof_id
            )
            session.add(other_quiz)

            # Module in empty classroom for locked/inactive quiz tests
            empty_module = Module(
                id="empty-module-id",
                classroom_id="empty-classroom-id",
                name="Empty Module"
            )
            session.add(empty_module)
            await session.flush()

            # prerequisite-quiz-id: a quiz that student1 has NOT completed (used as prerequisite)
            prereq_quiz = Quiz(
                id="prerequisite-quiz-id",
                module_id="empty-module-id",
                title="Prerequisite Quiz",
                is_active=True,
                min_score_to_unlock_next=0,
                created_by_id=prof_id
            )
            session.add(prereq_quiz)

            # locked-quiz-id: has prerequisite that student1 hasn't completed
            locked_quiz = Quiz(
                id="locked-quiz-id",
                module_id="empty-module-id",
                title="Locked Quiz",
                is_active=True,
                min_score_to_unlock_next=0,
                created_by_id=prof_id,
                prerequisite_quiz_id="prerequisite-quiz-id"
            )
            session.add(locked_quiz)

            # inactive-quiz-id: quiz with is_active=False
            inactive_quiz = Quiz(
                id="inactive-quiz-id",
                module_id="empty-module-id",
                title="Inactive Quiz",
                is_active=False,
                min_score_to_unlock_next=0,
                created_by_id=prof_id
            )
            session.add(inactive_quiz)

            # Module in sparse classroom for sparse leitner
            sparse_module = Module(
                id="sparse-module-id",
                classroom_id="sparse-classroom-id",
                name="Sparse Module"
            )
            session.add(sparse_module)

            # Quiz in sparse classroom with a few questions
            sparse_quiz = Quiz(
                id="sparse-quiz-id",
                module_id="sparse-module-id",
                title="Sparse Quiz",
                is_active=True,
                min_score_to_unlock_next=0,
                created_by_id=prof_id
            )
            session.add(sparse_quiz)
            await session.flush()

            # Create 3 questions in sparse quiz and put them in leitner boxes
            for i in range(3):
                sq = Question(
                    id=f"sparse-q-{i}",
                    quiz_id="sparse-quiz-id",
                    type=QuestionType.QCM,
                    content_text=f"Sparse Question {i}?"
                )
                session.add(sq)
                await session.flush()
                session.add(QuestionOption(question_id=f"sparse-q-{i}", text_choice="Yes", is_correct=True, display_order=0))
                session.add(QuestionOption(question_id=f"sparse-q-{i}", text_choice="No", is_correct=False, display_order=1))
                session.add(LeitnerBox(
                    classroom_id="sparse-classroom-id",
                    student_id=student1_id,
                    question_id=f"sparse-q-{i}",
                    box_level=1
                ))

            await session.flush()

            # =============================================
            # Seed media with hardcoded IDs
            # =============================================

            # unused-media-id: owned by prof_responsible, not used in any question
            session.add(Media(
                id="unused-media-id",
                url="/uploads/unused.jpg",
                filename="unused.jpg",
                mime_type="image/jpeg",
                uploaded_by_id=prof_id
            ))

            # other-user-media-id: owned by prof_responsible (so prof_secondary gets 403)
            session.add(Media(
                id="other-user-media-id",
                url="/uploads/other.jpg",
                filename="other.jpg",
                mime_type="image/jpeg",
                uploaded_by_id=prof_id
            ))

            # used-media-id: owned by prof_responsible, used by a question
            session.add(Media(
                id="used-media-id",
                url="/uploads/used.jpg",
                filename="used.jpg",
                mime_type="image/jpeg",
                uploaded_by_id=prof_id
            ))

            await session.flush()

            # Create a question that references used-media-id
            media_question = Question(
                id="media-using-question",
                quiz_id="sparse-quiz-id",
                type=QuestionType.QCM,
                content_text="Question with media?",
                media_id="used-media-id"
            )
            session.add(media_question)

            await session.commit()
    
    asyncio.get_event_loop().run_until_complete(_seed())


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
def classroom_id(client, prof_responsible_token, prof_secondary_token, student_token, student2_token) -> str:
    """
    UUID of a classroom created for tests.
    
    Creates a classroom with the responsible professor, adds secondary professor
    as teacher, enrolls student1 and student2, and returns its ID.
    Also adds teacher-to-remove-id, student-to-remove-id, and student-id users.
    
    Returns:
        str: UUID of the test classroom
    """
    response = client.post(
        "/classrooms",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"name": "Test Anatomie L1", "level": "L1"}
    )
    assert response.status_code in [200, 201], f"Failed to create classroom: {response.text}"
    classroom_data = response.json()
    classroom_id = classroom_data["id"]
    
    # Add secondary professor as teacher
    me_secondary = client.get("/users/me", headers={"Authorization": f"Bearer {prof_secondary_token}"})
    secondary_email = me_secondary.json()["email"]
    add_teacher_resp = client.post(
        f"/classrooms/{classroom_id}/teachers",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"email": secondary_email}
    )
    # Accept 200, 201, 409 (already added)
    assert add_teacher_resp.status_code in [200, 201, 409], f"Failed to add secondary teacher: {add_teacher_resp.text}"
    
    # Add teacher-to-remove
    client.post(
        f"/classrooms/{classroom_id}/teachers",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"email": "teacher.remove@univ-rennes.fr"}
    )
    
    # Lookup student1's current email (may have been updated by earlier tests)
    me_resp = client.get("/users/me", headers={"Authorization": f"Bearer {student_token}"})
    student_email = me_resp.json()["email"]
    
    enroll_response = client.post(
        f"/classrooms/{classroom_id}/enroll",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"email": student_email}
    )
    assert enroll_response.status_code in [200, 201, 409], f"Failed to enroll student: {enroll_response.text}"
    
    # Lookup student2's current email
    me_resp2 = client.get("/users/me", headers={"Authorization": f"Bearer {student2_token}"})
    student2_email = me_resp2.json()["email"]
    
    enroll_response2 = client.post(
        f"/classrooms/{classroom_id}/enroll",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"email": student2_email}
    )
    # student2 enrollment is optional, don't assert
    
    # Enroll student-to-remove
    client.post(
        f"/classrooms/{classroom_id}/enroll",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"email": "student.remove@univ-rennes.fr"}
    )
    
    # Enroll student-id (progress student)
    client.post(
        f"/classrooms/{classroom_id}/enroll",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"email": "student.progress@univ-rennes.fr"}
    )
    
    # =============================================
    # Populate Leitner boxes for this classroom
    # Create a module + quiz + 25 questions, complete it as student1
    # so leitner start tests (5/10/15/20) have enough questions
    # =============================================
    mod_resp = client.post(
        f"/classrooms/{classroom_id}/modules",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        json={"name": "Leitner Seed Module", "category": "Seed"}
    )
    if mod_resp.status_code in [200, 201]:
        seed_module_id = mod_resp.json()["id"]
        
        q_resp = client.post(
            f"/modules/{seed_module_id}/quizzes",
            headers={"Authorization": f"Bearer {prof_responsible_token}"},
            json={"title": "Leitner Seed Quiz", "minScoreToUnlockNext": 0, "isActive": True}
        )
        if q_resp.status_code in [200, 201]:
            seed_quiz_id = q_resp.json()["id"]
            
            # Create 25 QCM questions (enough for 20-question leitner tests)
            for i in range(25):
                client.post(
                    f"/quizzes/{seed_quiz_id}/questions",
                    headers={"Authorization": f"Bearer {prof_responsible_token}"},
                    json={
                        "type": "QCM",
                        "contentText": f"Seed Q{i+1}?",
                        "options": [
                            {"textChoice": f"Right {i+1}", "isCorrect": True},
                            {"textChoice": f"Wrong {i+1}", "isCorrect": False}
                        ]
                    }
                )
            
            # Start quiz session as student1
            start_resp = client.post(
                "/sessions/start",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"quizId": seed_quiz_id}
            )
            if start_resp.status_code == 200:
                seed_sid = start_resp.json()["sessionId"]
                questions = start_resp.json().get("questions", [])
                
                # Submit answers for all questions
                for q in questions:
                    if q.get("options"):
                        opt_id = q["options"][0]["id"]
                        client.post(
                            f"/sessions/{seed_sid}/submit-answer",
                            headers={"Authorization": f"Bearer {student_token}"},
                            json={"questionId": q["id"], "selectedOptionId": opt_id}
                        )
                
                # Finish the session -> populates Leitner boxes
                client.post(
                    f"/sessions/{seed_sid}/finish",
                    headers={"Authorization": f"Bearer {student_token}"}
                )
    
    return classroom_id


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
        f"/classrooms/{classroom_id}/modules",
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
        f"/modules/{module_id}/quizzes",
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
def question_id(client, prof_responsible_token, quiz_id, test_session_maker) -> str:
    """
    UUID of a question created for tests.
    Also creates additional questions (TEXT, IMAGE, MATCHING) with hardcoded IDs
    in the same quiz so session tests can reference them.
    
    Args:
        quiz_id: Parent quiz ID
        
    Returns:
        str: UUID of the test QCM question (with hardcoded option IDs)
    """
    import asyncio
    from app.models.question import Question, QuestionOption, MatchingPair, ImageZone, TextConfig, QuestionType
    
    # First, create the QCM question via API to get it registered properly
    response = client.post(
        f"/quizzes/{quiz_id}/questions",
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
    qcm_question_id = response.json()["id"]
    
    # Now seed additional questions with hardcoded IDs directly in DB
    async def _seed_questions():
        async with test_session_maker() as session:
            from sqlalchemy import select, update
            from app.models.quiz import Quiz
            from app.models.module import Module
            from app.models.leitner import LeitnerBox
            
            # Get classroom_id from quiz -> module -> classroom
            qresult = await session.execute(select(Quiz).where(Quiz.id == quiz_id))
            quiz_obj = qresult.scalar_one()
            mresult = await session.execute(select(Module).where(Module.id == quiz_obj.module_id))
            mod_obj = mresult.scalar_one()
            current_classroom_id = mod_obj.classroom_id
            student1_id = TEST_USERS["student1"]["id"]
            
            # Check if hardcoded options already exist (from a previous fixture call)
            existing = await session.execute(
                select(QuestionOption).where(QuestionOption.id == "correct-option-id")
            )
            existing_opt = existing.scalar_one_or_none()
            
            # Also check if hardcoded questions exist (options may have been cascade-deleted)
            existing_q = await session.execute(
                select(Question).where(Question.id == "text-question-id")
            )
            existing_question = existing_q.scalar_one_or_none()
            
            if existing_opt is not None or existing_question is not None:
                # Already seeded — move hardcoded questions to current quiz
                await session.execute(
                    update(Question)
                    .where(Question.id.in_([
                        "text-question-id",
                        "text-question-case-insensitive-id",
                        "image-question-id",
                        "matching-question-id"
                    ]))
                    .values(quiz_id=quiz_id)
                )
                
                if existing_opt is not None:
                    # Options still exist — move them to current QCM question
                    await session.execute(
                        update(QuestionOption)
                        .where(QuestionOption.id.in_(["correct-option-id", "incorrect-option-id"]))
                        .values(question_id=qcm_question_id)
                    )
                    # Delete the auto-generated options for the new QCM question
                    result = await session.execute(
                        select(QuestionOption)
                        .where(QuestionOption.question_id == qcm_question_id)
                        .where(QuestionOption.id.notin_(["correct-option-id", "incorrect-option-id"]))
                    )
                    for opt in result.scalars().all():
                        await session.delete(opt)
                else:
                    # Options were cascade-deleted — recreate them for current QCM question
                    # First, delete auto-generated options
                    result = await session.execute(
                        select(QuestionOption).where(QuestionOption.question_id == qcm_question_id)
                    )
                    for opt in result.scalars().all():
                        await session.delete(opt)
                    await session.flush()
                    # Re-create hardcoded options
                    session.add(QuestionOption(
                        id="correct-option-id",
                        question_id=qcm_question_id,
                        text_choice="Answer A",
                        is_correct=True,
                        display_order=10
                    ))
                    session.add(QuestionOption(
                        id="incorrect-option-id",
                        question_id=qcm_question_id,
                        text_choice="Answer B",
                        is_correct=False,
                        display_order=11
                    ))
                
                # Update leitner box for QCM question to current classroom
                existing_lb = await session.execute(
                    select(LeitnerBox).where(LeitnerBox.question_id == qcm_question_id)
                )
                if existing_lb.scalar_one_or_none() is None:
                    session.add(LeitnerBox(
                        classroom_id=current_classroom_id,
                        student_id=student1_id,
                        question_id=qcm_question_id,
                        box_level=1
                    ))
                else:
                    await session.execute(
                        update(LeitnerBox)
                        .where(LeitnerBox.question_id == qcm_question_id)
                        .values(classroom_id=current_classroom_id)
                    )
                
                await session.commit()
                return
            
            # Get the actual option IDs for the QCM question and update them
            result = await session.execute(
                select(QuestionOption)
                .where(QuestionOption.question_id == qcm_question_id)
            )
            options = list(result.scalars().all())
            
            # Create options with hardcoded IDs: correct-option-id and incorrect-option-id
            for opt in options:
                if opt.is_correct:
                    new_opt = QuestionOption(
                        id="correct-option-id",
                        question_id=qcm_question_id,
                        text_choice=opt.text_choice,
                        is_correct=True,
                        display_order=10
                    )
                    session.add(new_opt)
                    await session.delete(opt)
                else:
                    new_opt = QuestionOption(
                        id="incorrect-option-id",
                        question_id=qcm_question_id,
                        text_choice=opt.text_choice,
                        is_correct=False,
                        display_order=11
                    )
                    session.add(new_opt)
                    await session.delete(opt)
            
            # TEXT question: text-question-id (exact match, Calcanéus)
            session.add(Question(
                id="text-question-id",
                quiz_id=quiz_id,
                type=QuestionType.TEXT,
                content_text="Quel est le nom de cet os du talon?"
            ))
            await session.flush()
            session.add(TextConfig(
                question_id="text-question-id",
                accepted_answer="Calcanéus",
                is_case_sensitive=True,
                ignore_spelling_errors=False
            ))
            
            # TEXT question: text-question-case-insensitive-id
            session.add(Question(
                id="text-question-case-insensitive-id",
                quiz_id=quiz_id,
                type=QuestionType.TEXT,
                content_text="Quel os du talon? (insensible à la casse)"
            ))
            await session.flush()
            session.add(TextConfig(
                question_id="text-question-case-insensitive-id",
                accepted_answer="Calcanéus",
                is_case_sensitive=False,
                ignore_spelling_errors=False
            ))
            
            # IMAGE question: image-question-id with zone at (50, 60) radius 20
            session.add(Question(
                id="image-question-id",
                quiz_id=quiz_id,
                type=QuestionType.IMAGE,
                content_text="Click on the correct zone"
            ))
            await session.flush()
            session.add(ImageZone(
                question_id="image-question-id",
                label_name="Correct Zone",
                x=50.0,
                y=60.0,
                radius=20.0
            ))
            
            # MATCHING question: matching-question-id
            session.add(Question(
                id="matching-question-id",
                quiz_id=quiz_id,
                type=QuestionType.MATCHING,
                content_text="Match the bones"
            ))
            await session.flush()
            session.add(MatchingPair(
                id="tibia-id",
                question_id="matching-question-id",
                item_left="tibia-id",
                item_right="interne-id"
            ))
            session.add(MatchingPair(
                id="fibula-id",
                question_id="matching-question-id",
                item_left="fibula-id",
                item_right="externe-id"
            ))
            
            # Add QCM question to leitner boxes so leitner submit tests work
            session.add(LeitnerBox(
                classroom_id=current_classroom_id,
                student_id=student1_id,
                question_id=qcm_question_id,
                box_level=1
            ))
            
            await session.commit()
    
    asyncio.get_event_loop().run_until_complete(_seed_questions())
    
    return qcm_question_id


@pytest.fixture
def session_id(client, student_token, quiz_id, question_id, test_session_maker) -> str:
    """
    UUID of a quiz session created for tests.
    Also seeds finished-session-id and other-student-session-id in the DB.
    Depends on question_id to ensure all hardcoded questions exist in the quiz.
    
    Args:
        quiz_id: Quiz to start a session for
        question_id: Ensures questions are seeded before session
        
    Returns:
        str: UUID of the test session
    """
    import asyncio
    from app.models.session import QuizSession, SessionAnswer, SessionStatus
    from app.models.quiz import Quiz
    from app.models.module import Module
    
    response = client.post(
        "/sessions/start",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"quizId": quiz_id}
    )
    assert response.status_code in [200, 201], f"Failed to create session: {response.text}"
    sid = response.json()["sessionId"]
    
    # Seed hardcoded sessions in DB
    async def _seed_sessions():
        async with test_session_maker() as session:
            from sqlalchemy import select, update
            
            # Check if already seeded
            existing = await session.execute(
                select(QuizSession).where(QuizSession.id == "finished-session-id")
            )
            if existing.scalar_one_or_none() is not None:
                # Already seeded — update quiz_id and classroom_id to current ones
                result = await session.execute(select(Quiz).where(Quiz.id == quiz_id))
                quiz = result.scalar_one()
                result = await session.execute(select(Module).where(Module.id == quiz.module_id))
                module = result.scalar_one()
                classroom_id = module.classroom_id
                
                await session.execute(
                    update(QuizSession)
                    .where(QuizSession.id.in_([
                        "finished-session-id",
                        "other-student-session-id",
                        "in-progress-session-id"
                    ]))
                    .values(quiz_id=quiz_id, classroom_id=classroom_id)
                )
                await session.commit()
                return
            
            # Get the quiz to find its classroom_id
            result = await session.execute(select(Quiz).where(Quiz.id == quiz_id))
            quiz = result.scalar_one()
            result = await session.execute(select(Module).where(Module.id == quiz.module_id))
            module = result.scalar_one()
            classroom_id = module.classroom_id
            
            student1_id = TEST_USERS["student1"]["id"]
            student2_id = TEST_USERS["student2"]["id"]
            
            # finished-session-id: completed session owned by student1
            finished_session = QuizSession(
                id="finished-session-id",
                quiz_id=quiz_id,
                student_id=student1_id,
                classroom_id=classroom_id,
                status=SessionStatus.COMPLETED,
                total_score=1,
                max_score=1,
                passed=True,
                completed_at=datetime.utcnow()
            )
            session.add(finished_session)
            
            # other-student-session-id: completed session owned by student1 (student2 tries to review)
            other_session = QuizSession(
                id="other-student-session-id",
                quiz_id=quiz_id,
                student_id=student1_id,
                classroom_id=classroom_id,
                status=SessionStatus.COMPLETED,
                total_score=1,
                max_score=1,
                passed=True,
                completed_at=datetime.utcnow()
            )
            session.add(other_session)
            
            # in-progress-session-id: in-progress session owned by student1 (review before finish)
            in_progress_session = QuizSession(
                id="in-progress-session-id",
                quiz_id=quiz_id,
                student_id=student1_id,
                classroom_id=classroom_id,
                status=SessionStatus.IN_PROGRESS,
                total_score=0,
                max_score=1
            )
            session.add(in_progress_session)
            
            await session.commit()
    
    asyncio.get_event_loop().run_until_complete(_seed_sessions())
    
    return sid


@pytest.fixture
def leitner_session_id(client, student_token, prof_responsible_token, classroom_id, module_id, test_session_maker) -> str:
    """
    UUID of a Leitner session created for tests.
    
    Creates multiple questions, completes a quiz to populate Leitner boxes,
    then starts a Leitner revision session.
    Also seeds finished-leitner-session-id and other-student-leitner-session-id.
    
    Args:
        classroom_id: Classroom for Leitner review
        module_id: Module to create quiz in
        
    Returns:
        str: UUID of the test Leitner session
    """
    import asyncio
    from app.models.leitner import LeitnerSession, LeitnerSessionAnswer
    
    headers = {"Authorization": f"Bearer {prof_responsible_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}
    
    # Step 1: Create a quiz with low min_score so it always passes
    quiz_resp = client.post(
        f"/modules/{module_id}/quizzes",
        headers=headers,
        json={"title": "Leitner Quiz", "minScoreToUnlockNext": 0, "isActive": True}
    )
    assert quiz_resp.status_code in [200, 201], f"Failed to create quiz: {quiz_resp.text}"
    leitner_quiz_id = quiz_resp.json()["id"]
    
    # Step 2: Create multiple QCM questions (need at least 5 for Leitner)
    question_ids = []
    for i in range(6):
        q_resp = client.post(
            f"/quizzes/{leitner_quiz_id}/questions",
            headers=headers,
            json={
                "type": "QCM",
                "contentText": f"Leitner Q{i+1}?",
                "options": [
                    {"textChoice": f"Correct {i+1}", "isCorrect": True},
                    {"textChoice": f"Wrong {i+1}", "isCorrect": False}
                ]
            }
        )
        assert q_resp.status_code in [200, 201], f"Failed to create question: {q_resp.text}"
        question_ids.append(q_resp.json()["id"])
    
    # Step 3: Start a quiz session as the student
    start_resp = client.post(
        "/sessions/start",
        headers=student_headers,
        json={"quizId": leitner_quiz_id}
    )
    assert start_resp.status_code == 200, f"Failed to start session: {start_resp.text}"
    session_data = start_resp.json()
    sid = session_data["sessionId"]
    
    # Step 4: Submit answers for each question
    questions = session_data.get("questions", [])
    for q in questions:
        if q.get("options"):
            opt_id = q["options"][0]["id"]
            client.post(
                f"/sessions/{sid}/submit-answer",
                headers=student_headers,
                json={"questionId": q["id"], "selectedOptionId": opt_id}
            )
    
    # Step 5: Finish the session (min_score=0, so always passes -> adds to Leitner Box 1)
    finish_resp = client.post(
        f"/sessions/{sid}/finish",
        headers=student_headers
    )
    assert finish_resp.status_code == 200, f"Failed to finish session: {finish_resp.text}"
    
    # Step 6: Start a Leitner session (boxes should now be populated with 6 questions)
    response = client.post(
        f"/classrooms/{classroom_id}/leitner/start",
        headers=student_headers,
        json={"questionCount": 5}
    )
    assert response.status_code in [200, 201], f"Failed to create Leitner session: {response.text}"
    leitner_sid = response.json()["sessionId"]
    
    # Step 7: Seed hardcoded Leitner sessions in DB
    async def _seed_leitner():
        async with test_session_maker() as session:
            from sqlalchemy import select, update
            
            # Check if already seeded
            existing = await session.execute(
                select(LeitnerSession).where(LeitnerSession.id == "finished-leitner-session-id")
            )
            if existing.scalar_one_or_none() is not None:
                # Already seeded — update classroom_id to current one
                await session.execute(
                    update(LeitnerSession)
                    .where(LeitnerSession.id.in_([
                        "finished-leitner-session-id",
                        "other-student-leitner-session-id"
                    ]))
                    .values(classroom_id=classroom_id)
                )
                await session.commit()
                return
            
            student1_id = TEST_USERS["student1"]["id"]
            
            # finished-leitner-session-id: completed Leitner session owned by student1
            finished_ls = LeitnerSession(
                id="finished-leitner-session-id",
                classroom_id=classroom_id,
                student_id=student1_id,
                question_count=5,
                correct_answers=3,
                wrong_answers=2,
                promoted=3,
                demoted=2,
                completed_at=datetime.utcnow()
            )
            session.add(finished_ls)
            
            # Add some answers to the finished session so review has data
            for i, qid in enumerate(question_ids[:5]):
                is_correct = i < 3  # first 3 correct, last 2 incorrect
                session.add(LeitnerSessionAnswer(
                    session_id="finished-leitner-session-id",
                    question_id=qid,
                    is_correct=is_correct,
                    previous_box=1,
                    new_box=2 if is_correct else 1,
                    answer_data="{}"
                ))
            
            # other-student-leitner-session-id: completed session owned by student1 (student2 tries to review)
            other_ls = LeitnerSession(
                id="other-student-leitner-session-id",
                classroom_id=classroom_id,
                student_id=student1_id,
                question_count=5,
                correct_answers=5,
                wrong_answers=0,
                promoted=5,
                demoted=0,
                completed_at=datetime.utcnow()
            )
            session.add(other_ls)
            
            await session.commit()
    
    asyncio.get_event_loop().run_until_complete(_seed_leitner())
    
    return leitner_sid


@pytest.fixture
def media_id(client, prof_responsible_token) -> str:
    """
    UUID of a media file uploaded for tests.
    
    Returns:
        str: UUID of the test media
    """
    import io
    
    # Create a minimal valid JPEG (just the header bytes)
    img_bytes = io.BytesIO(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')
    
    response = client.post(
        "/media",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code in [200, 201], f"Failed to upload media: {response.text}"
    data = response.json()
    return data.get("mediaId") or data.get("id")


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
def create_classroom(client, prof_responsible_token):
    """
    Helper fixture to create a classroom for testing.
    
    Returns:
        Function that creates a classroom and returns classroom data
    """
    def _create_classroom(name: str, level: str, code: str = None) -> Dict[str, Any]:
        response = client.post(
            "/classrooms",
            headers={"Authorization": f"Bearer {prof_responsible_token}"},
            json={"name": name, "level": level}
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
