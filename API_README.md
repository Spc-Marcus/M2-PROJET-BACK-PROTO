# Duobingo FastAPI Backend

Complete FastAPI backend implementation for the Duobingo anatomy learning platform.

## Features

- ✅ 22 SQLAlchemy models (async, SQLite)
- ✅ 50+ Pydantic v2 schemas with camelCase JSON serialization
- ✅ JWT authentication with role-based permissions (ADMIN, TEACHER, STUDENT)
- ✅ Leitner 5-box spaced-repetition system with probability-based selection
- ✅ 35+ API endpoints matching documentation exactly
- ✅ Circular dependency detection for prerequisites
- ✅ Auto-completion tracking with cache tables
- ✅ Dynamic statistics calculation (no stored points)
- ✅ Session management with timeout
- ✅ Comprehensive business logic

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Seed Database

```bash
export PYTHONPATH=.
python app/utils/seed.py
```

This creates 5 test users:
- **admin@univ-rennes.fr** / admin123 (ADMIN)
- **house@univ-rennes.fr** / prof123 (TEACHER - Prof Responsible)
- **wilson@univ-rennes.fr** / prof123 (TEACHER - Secondary Prof)
- **marie.martin@univ-rennes.fr** / student123 (STUDENT L1)
- **jean.dupont@univ-rennes.fr** / student123 (STUDENT L1)

### 3. Start Server

```bash
./start.sh
```

Or manually:
```bash
uvicorn app.main:app --reload
```

### 4. Access API

- **API Base**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

All endpoints are prefixed with `/api`:

### Authentication
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/register` - Student self-registration
- `GET /api/users/me` - Get current user profile
- `PATCH /api/users/me` - Update profile
- `POST /api/admin/users` - Create users (admin only)

### Classrooms
- `GET /api/classrooms` - List classrooms
- `POST /api/classrooms` - Create classroom
- `GET /api/classrooms/{id}` - Get classroom details
- `PATCH /api/classrooms/{id}` - Update classroom
- `DELETE /api/classrooms/{id}` - Delete classroom
- `POST /api/classrooms/{id}/join` - Join with code
- `POST /api/classrooms/{id}/enroll` - Enroll student
- `GET /api/classrooms/{id}/members` - List members
- `POST /api/classrooms/{id}/teachers` - Add teacher
- `DELETE /api/classrooms/{id}/teachers/{tid}` - Remove teacher
- `DELETE /api/classrooms/{id}/students/{sid}` - Remove student
- `POST /api/classrooms/{id}/regenerate-code` - Regenerate code

### Modules
- `GET /api/classrooms/{cid}/modules` - List modules
- `POST /api/classrooms/{cid}/modules` - Create module
- `PUT /api/modules/{id}` - Update module
- `DELETE /api/modules/{id}` - Delete module

### Quizzes
- `GET /api/modules/{mid}/quizzes` - List quizzes
- `POST /api/modules/{mid}/quizzes` - Create quiz
- `PUT /api/quizzes/{id}` - Update quiz
- `DELETE /api/quizzes/{id}` - Delete quiz

### Questions
- `GET /api/quizzes/{qid}/questions` - List questions
- `POST /api/quizzes/{qid}/questions` - Create question
- `PUT /api/questions/{id}` - Update question
- `DELETE /api/questions/{id}` - Delete question

### Quiz Sessions
- `POST /api/sessions/start` - Start quiz session
- `POST /api/sessions/{sid}/submit-answer` - Submit answer
- `POST /api/sessions/{sid}/finish` - Finish session
- `GET /api/sessions/{sid}/review` - Review session

### Leitner System
- `GET /api/classrooms/{cid}/leitner/status` - View box distribution
- `POST /api/classrooms/{cid}/leitner/start` - Start revision session
- `POST /api/leitner/sessions/{sid}/submit-answer` - Submit answer
- `POST /api/leitner/sessions/{sid}/finish` - Finish session
- `GET /api/leitner/sessions/{sid}/review` - Review session

### Statistics & Progress
- `GET /api/stats/student` - Student statistics
- `GET /api/stats/leaderboard/{cid}` - Classroom leaderboard
- `GET /api/stats/dashboard/{cid}` - Professor dashboard
- `GET /api/progress/modules/{mid}` - Module progress
- `GET /api/progress/quizzes/{qid}` - Quiz progress
- `GET /api/progress/classroom/{cid}` - Classroom progress
- `GET /api/progress/classroom/{cid}/student/{sid}` - Student progress (prof view)

### Media
- `POST /api/media` - Upload media file
- `GET /api/media` - List media files
- `DELETE /api/media/{id}` - Delete media file
- `GET /api/media/orphaned` - List orphaned media (admin)

## Architecture

### Database Models (app/models/)

- **Users**: User, StudentProfile, TeacherProfile
- **Classrooms**: Classroom, ClassroomTeacher, ClassroomStudent
- **Content**: Module, Quiz, Question (polymorphic)
- **Questions**: QuestionOption, MatchingPair, ImageZone, TextConfig
- **Sessions**: QuizSession, SessionAnswer
- **Leitner**: LeitnerBox, LeitnerSession, LeitnerSessionAnswer
- **Cache**: CompletedQuiz, CompletedModule
- **Media**: Media

### Business Logic

#### Leitner Spaced Repetition
- 5 boxes per student per classroom
- Probability-based selection: Box1=50%, Box2=25%, Box3=15%, Box4=7%, Box5=3%
- Correct answer: +1 box (max 5)
- Incorrect answer: back to box 1
- Questions added to Box 1 on first quiz completion

#### Prerequisite System
- Modules can require other modules
- Quizzes can require other quizzes
- Circular dependency detection (max 50 depth)
- Auto-unlock when prerequisites met

#### Completion Tracking
- `CompletedQuiz` table: Quiz passed (score >= minScoreToUnlockNext)
- `CompletedModule` table: All required quizzes passed
- Auto-created on quiz finish
- Used for fast unlock checks

#### Session Management
- States: IN_PROGRESS, COMPLETED, ABANDONED
- 2-hour timeout for abandoned sessions
- Answers stored for review
- Score calculated on finish

#### Dynamic Statistics
- All stats calculated on-demand (no stored aggregates)
- Student stats: completed quizzes, average score, Leitner mastery
- Leaderboard: sorted by completion then score
- Professor dashboard: module stats, difficult questions

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_auth.py -v
```

Run with coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```

**Note**: Tests use in-memory SQLite database. Test fixtures are in `tests/conftest.py`.

## Project Structure

```
.
├── app/
│   ├── api/
│   │   ├── deps.py              # Authentication dependencies
│   │   └── routes/              # API endpoints
│   ├── core/
│   │   ├── config.py            # Settings
│   │   └── security.py          # JWT & password hashing
│   ├── db/
│   │   └── session.py           # Database session
│   ├── models/                  # SQLAlchemy models
│   ├── schemas/                 # Pydantic DTOs
│   ├── services/                # Business logic
│   ├── utils/
│   │   └── seed.py              # Database seeding
│   └── main.py                  # FastAPI app
├── tests/                       # Test suite
├── doc/                         # API documentation
├── requirements.txt
├── pytest.ini
└── start.sh                     # Startup script
```

## Configuration

Set via environment variables or `.env` file:

- `DATABASE_URL`: Database connection (default: `sqlite+aiosqlite:///./duobingo.db`)
- `JWT_SECRET_KEY`: **REQUIRED IN PRODUCTION** (default for dev/test only)
- `JWT_ALGORITHM`: JWT algorithm (default: `HS256`)
- `JWT_EXPIRATION_HOURS`: Token expiration (default: `24`)
- `CORS_ORIGINS`: Allowed origins (default: `["*"]`)
- `DEBUG`: Debug mode (default: `True`)

⚠️ **Security Warning**: The default `JWT_SECRET_KEY` is for development/testing only. 
Set a secure random value in production via environment variable.

## Key Features

### Permissions

- **Admin**: Full access to all resources
- **Teacher**: Manage quizzes/questions in their classrooms
- **Responsible Professor**: Full classroom management (only creator)
- **Other Teachers**: Can manage quizzes but not classroom/modules
- **Student**: Join classrooms, take quizzes, review with Leitner

### Question Types

1. **QCM**: Multiple choice with multiple correct answers
2. **VRAI_FAUX**: True/False questions
3. **MATCHING**: Match pairs of items
4. **IMAGE**: Click zones on images
5. **TEXT**: Text input with spelling tolerance

### Error Codes

- `QUIZ_LOCKED`: Prerequisite quiz not completed
- `MODULE_PREREQUISITE_NOT_MET`: Prerequisite module not completed  
- `CIRCULAR_PREREQUISITE`: Circular dependency detected
- `LEITNER_NO_QUESTIONS`: No questions in Leitner boxes
- `ALREADY_ENROLLED`: Student already enrolled
- `CLASSROOM_CODE_INVALID`: Invalid classroom code
- `INSUFFICIENT_PERMISSIONS`: User lacks required permissions
- `SESSION_ALREADY_FINISHED`: Session already completed

## Documentation

See `/doc` folder for detailed API documentation:
- `endpoints.md` - All endpoints with examples
- `dto.md` - All DTOs with field specifications
- `class-diagram.md` - Database model diagrams
- `naming-conventions.md` - Code style guide

## License

University project - Université de Rennes

## Support

For issues or questions, see the API documentation at `/docs` when the server is running.
