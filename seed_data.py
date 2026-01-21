"""
Script to seed the database with demo data.
Run with: python seed_data.py
"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, Role, Level, StudentProfile, TeacherProfile
from app.models.classroom import Classroom, ClassroomStudent, ClassroomTeacher
from app.models.module import Module
from app.models.quiz import Quiz
from app.models.question import Question, QuestionType, QuestionOption, MatchingPair, TextConfig

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Check if data exists
    if db.query(User).first():
        print("Database already has data. Skipping seed.")
        sys.exit(0)
    
    print("Seeding database with demo data...")
    
    # ============== Create Users ==============
    
    # Admin
    admin = User(
        email="admin@univ-rennes.fr",
        password=get_password_hash("admin123"),
        name="Administrateur",
        role=Role.ADMIN
    )
    db.add(admin)
    
    # Teachers
    prof1 = User(
        email="house@univ-rennes.fr",
        password=get_password_hash("prof123"),
        name="Dr. Gregory House",
        role=Role.TEACHER
    )
    db.add(prof1)
    db.flush()
    
    prof1_profile = TeacherProfile(
        user_id=prof1.id,
        faculty_department="Anatomie"
    )
    db.add(prof1_profile)
    
    prof2 = User(
        email="wilson@univ-rennes.fr",
        password=get_password_hash("prof123"),
        name="Dr. James Wilson",
        role=Role.TEACHER
    )
    db.add(prof2)
    db.flush()
    
    prof2_profile = TeacherProfile(
        user_id=prof2.id,
        faculty_department="Anatomie"
    )
    db.add(prof2_profile)
    
    # Students
    students = []
    student_data = [
        ("marie.martin@univ-rennes.fr", "Marie Martin", Level.L1),
        ("jean.dupont@univ-rennes.fr", "Jean Dupont", Level.L1),
        ("pierre.durand@univ-rennes.fr", "Pierre Durand", Level.L2),
        ("sophie.bernard@univ-rennes.fr", "Sophie Bernard", Level.L1),
    ]
    
    for email, name, level in student_data:
        student = User(
            email=email,
            password=get_password_hash("student123"),
            name=name,
            role=Role.STUDENT
        )
        db.add(student)
        db.flush()
        
        profile = StudentProfile(
            user_id=student.id,
            level=level
        )
        db.add(profile)
        students.append(student)
    
    db.commit()
    print(f"Created {len(students) + 3} users (1 admin, 2 teachers, {len(students)} students)")
    
    # ============== Create Classroom ==============
    
    classroom = Classroom(
        name="Anatomie L1 - 2026",
        level=Level.L1,
        code="ANAT26",
        responsible_professor_id=prof1.id
    )
    db.add(classroom)
    db.flush()
    
    # Add second teacher
    teacher_link = ClassroomTeacher(
        classroom_id=classroom.id,
        teacher_id=prof2.id
    )
    db.add(teacher_link)
    
    # Enroll students
    for student in students:
        link = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=student.id
        )
        db.add(link)
    
    db.commit()
    print(f"Created classroom: {classroom.name} (Code: {classroom.code})")
    
    # ============== Create Modules ==============
    
    module1 = Module(
        classroom_id=classroom.id,
        name="Membre Inférieur",
        category="Ostéologie"
    )
    db.add(module1)
    db.flush()
    
    module2 = Module(
        classroom_id=classroom.id,
        name="Membre Supérieur",
        category="Ostéologie",
        prerequisite_module_id=module1.id
    )
    db.add(module2)
    db.flush()
    
    db.commit()
    print(f"Created 2 modules")
    
    # ============== Create Quizzes ==============
    
    quiz1 = Quiz(
        module_id=module1.id,
        title="Le Pied - Introduction",
        min_score_to_unlock_next=2,
        is_active=True,
        created_by_id=prof1.id
    )
    db.add(quiz1)
    db.flush()
    
    quiz2 = Quiz(
        module_id=module1.id,
        title="Le Pied - Avancé",
        prerequisite_quiz_id=quiz1.id,
        min_score_to_unlock_next=3,
        is_active=True,
        created_by_id=prof1.id
    )
    db.add(quiz2)
    db.flush()
    
    db.commit()
    print(f"Created 2 quizzes")
    
    # ============== Create Questions ==============
    
    # QCM Question
    q1 = Question(
        quiz_id=quiz1.id,
        type=QuestionType.QCM,
        content_text="Quel est l'os le plus volumineux du pied ?",
        explanation="Le calcanéus (os du talon) est le plus gros os du pied."
    )
    db.add(q1)
    db.flush()
    
    options1 = [
        QuestionOption(question_id=q1.id, text_choice="Talus", is_correct=False, display_order=1),
        QuestionOption(question_id=q1.id, text_choice="Calcanéus", is_correct=True, display_order=2),
        QuestionOption(question_id=q1.id, text_choice="Cuboïde", is_correct=False, display_order=3),
        QuestionOption(question_id=q1.id, text_choice="Naviculaire", is_correct=False, display_order=4),
    ]
    for opt in options1:
        db.add(opt)
    
    # Vrai/Faux Question
    q2 = Question(
        quiz_id=quiz1.id,
        type=QuestionType.VRAI_FAUX,
        content_text="Le pied contient 26 os.",
        explanation="Correct ! Le pied humain contient 26 os."
    )
    db.add(q2)
    db.flush()
    
    options2 = [
        QuestionOption(question_id=q2.id, text_choice="Vrai", is_correct=True, display_order=1),
        QuestionOption(question_id=q2.id, text_choice="Faux", is_correct=False, display_order=2),
    ]
    for opt in options2:
        db.add(opt)
    
    # TEXT Question
    q3 = Question(
        quiz_id=quiz1.id,
        type=QuestionType.TEXT,
        content_text="Comment s'appelle l'os du talon ?",
        explanation="Le calcanéus est l'os qui forme le talon."
    )
    db.add(q3)
    db.flush()
    
    text_config = TextConfig(
        question_id=q3.id,
        accepted_answer="calcanéus",
        is_case_sensitive=False,
        ignore_spelling_errors=True
    )
    db.add(text_config)
    
    # MATCHING Question
    q4 = Question(
        quiz_id=quiz1.id,
        type=QuestionType.MATCHING,
        content_text="Associez chaque os à sa localisation :",
        explanation="Le tarse postérieur contient le talus et le calcanéus."
    )
    db.add(q4)
    db.flush()
    
    pairs = [
        MatchingPair(question_id=q4.id, item_left="Talus", item_right="Tarse postérieur"),
        MatchingPair(question_id=q4.id, item_left="Calcanéus", item_right="Tarse postérieur"),
        MatchingPair(question_id=q4.id, item_left="Cuboïde", item_right="Tarse antérieur"),
    ]
    for pair in pairs:
        db.add(pair)
    
    # Add questions to quiz2
    q5 = Question(
        quiz_id=quiz2.id,
        type=QuestionType.QCM,
        content_text="Combien de métatarsiens compte le pied ?",
        explanation="Le pied possède 5 métatarsiens, un pour chaque orteil."
    )
    db.add(q5)
    db.flush()
    
    options5 = [
        QuestionOption(question_id=q5.id, text_choice="3", is_correct=False, display_order=1),
        QuestionOption(question_id=q5.id, text_choice="4", is_correct=False, display_order=2),
        QuestionOption(question_id=q5.id, text_choice="5", is_correct=True, display_order=3),
        QuestionOption(question_id=q5.id, text_choice="7", is_correct=False, display_order=4),
    ]
    for opt in options5:
        db.add(opt)
    
    db.commit()
    print(f"Created 5 questions")
    
    # ============== Summary ==============
    print("\n" + "="*50)
    print("DEMO DATA CREATED SUCCESSFULLY!")
    print("="*50)
    print("\nTest Accounts:")
    print("-" * 40)
    print("Admin:    admin@univ-rennes.fr / admin123")
    print("Teacher:  house@univ-rennes.fr / prof123")
    print("Teacher:  wilson@univ-rennes.fr / prof123")
    print("Student:  marie.martin@univ-rennes.fr / student123")
    print("Student:  jean.dupont@univ-rennes.fr / student123")
    print("-" * 40)
    print(f"\nClassroom Code: {classroom.code}")
    print("\nRun the server with: uvicorn main:app --reload")
    print("API Docs: http://localhost:8000/docs")
    
finally:
    db.close()
