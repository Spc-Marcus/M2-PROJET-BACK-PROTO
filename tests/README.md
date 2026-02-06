# Duobingo API Test Suite

Comprehensive test suite for the Duobingo API backend, covering all 35+ endpoints with complete HTTP status code coverage and authentication scenarios.

## 📋 Test Coverage

### Test Files

1. **`test_auth.py`** - Authentication & User Management (20+ tests)
   - Login (valid, invalid, missing credentials)
   - Registration (success, duplicates, validation)
   - User profile (get, update, permissions)
   - Admin user creation

2. **`test_classrooms.py`** - Classroom Management (40+ tests)
   - CRUD operations
   - Member management (add/remove teachers, students)
   - Join with code
   - Code regeneration
   - Cascade deletion

3. **`test_modules.py`** - Module Management (20+ tests)
   - CRUD operations
   - Prerequisites and locking
   - Circular dependency detection
   - Cascade deletion

4. **`test_quizzes.py`** - Quiz Management (25+ tests)
   - CRUD operations
   - Prerequisites and locking
   - Active/inactive state
   - Circular dependency detection

5. **`test_questions.py`** - Question Bank (40+ tests)
   - 5 polymorphic question types:
     - QCM (Multiple Choice)
     - VRAI_FAUX (True/False)
     - MATCHING (Pairing)
     - TEXT (Text Input with fuzzy matching)
     - IMAGE (Clickable zones)
   - Validation for each type
   - Leitner integration

6. **`test_sessions.py`** - Quiz Gameplay (45+ tests)
   - Starting sessions
   - Submitting answers (all question types)
   - Session completion
   - Score calculation
   - Unlocking logic
   - Review/correction

7. **`test_leitner.py`** - Leitner Spaced Repetition (30+ tests)
   - Box status and distribution
   - Session creation (5, 10, 15, 20 questions)
   - Answer submission
   - Promotion/demotion rules
   - Session completion and review

8. **`test_stats.py`** - Statistics & Progression (35+ tests)
   - Student personal stats
   - Leaderboard rankings
   - Professor dashboard
   - Module/quiz/classroom progress
   - Role-based access

9. **`test_media.py`** - Media Upload (30+ tests)
   - Image upload (JPG, PNG)
   - File validation
   - Size limits
   - Orphaned media detection
   - Deletion with usage check

### HTTP Status Codes Tested

- ✅ **200 OK** - Successful GET, successful operations
- ✅ **201 Created** - Successful POST (creation)
- ✅ **204 No Content** - Successful DELETE
- ✅ **400 Bad Request** - Validation errors, invalid data
- ✅ **401 Unauthorized** - Missing or invalid authentication
- ✅ **403 Forbidden** - Insufficient permissions
- ✅ **404 Not Found** - Resource not found
- ✅ **409 Conflict** - Duplicate resources, constraint violations
- ✅ **422 Unprocessable Entity** - Circular dependencies
- ✅ **413 Payload Too Large** - File size limits (media upload)

### Authentication Scenarios Tested

- ✅ **Admin** - Full access
- ✅ **Professor Responsible** - Classroom owner permissions
- ✅ **Professor Secondary** - Limited classroom permissions
- ✅ **Student** - Student-specific permissions
- ✅ **No Authentication** - Public endpoints and 401 errors
- ✅ **Invalid Token** - Malformed or expired tokens
- ✅ **Insufficient Permissions** - 403 Forbidden scenarios

## 🚀 Running the Tests

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt
```

### Run All Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_auth.py::test_login_valid_credentials -v
```

### Run Tests by Category

```bash
# Authentication tests
pytest tests/test_auth.py -v

# Classroom tests
pytest tests/test_classrooms.py -v

# Gameplay tests (sessions + leitner)
pytest tests/test_sessions.py tests/test_leitner.py -v

# Statistics tests
pytest tests/test_stats.py -v
```

### Advanced Options

```bash
# Stop at first failure
pytest tests/ -x

# Show print statements
pytest tests/ -s

# Run in parallel (requires pytest-xdist)
pytest tests/ -n auto

# Generate JUnit XML report
pytest tests/ --junitxml=test-results.xml

# Run only failed tests from last run
pytest tests/ --lf

# Run with detailed failure messages
pytest tests/ -vv
```

## 📊 Test Statistics

- **Total Tests**: 280+ tests
- **Test Files**: 9 files
- **Endpoints Covered**: 35+ endpoints
- **HTTP Codes**: 10 different status codes
- **Auth Scenarios**: 7 different auth scenarios

## 🔧 Test Infrastructure

### Fixtures (`conftest.py`)

- **`client`** - FastAPI TestClient
- **`admin_token`** - Admin JWT token
- **`prof_responsible_token`** - Professor (responsible) JWT token
- **`prof_secondary_token`** - Professor (secondary) JWT token
- **`student_token`** - Student JWT token
- **`student2_token`** - Second student JWT token
- **`invalid_token`** - Invalid JWT token
- **`expired_token`** - Expired JWT token
- **`classroom_id`** - Test classroom UUID
- **`module_id`** - Test module UUID
- **`quiz_id`** - Test quiz UUID
- **`question_id`** - Test question UUID
- **`session_id`** - Test quiz session UUID
- **`leitner_session_id`** - Test Leitner session UUID
- **`media_id`** - Test media UUID

### Test Users

Predefined test accounts (from problem statement):

- **Admin**: `admin@univ-rennes.fr` / `admin123`
- **Prof Responsible**: `house@univ-rennes.fr` / `prof123`
- **Prof Secondary**: `wilson@univ-rennes.fr` / `prof123`
- **Student 1**: `marie.martin@univ-rennes.fr` / `student123`
- **Student 2**: `jean.dupont@univ-rennes.fr` / `student123`

### Test Classroom Code

- **Code**: `ANAT26`

## 📝 Writing New Tests

### Test Naming Convention

```python
def test_<action>_<scenario>(client, <fixtures>):
    """
    Brief description of what is being tested.
    
    Expected: <HTTP status code>, <expected behavior>
    """
    # Arrange
    # Act
    # Assert
```

### Example Test

```python
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
    assert data["questionCount"] == 0
```

## 🎯 Business Error Codes Tested

- `QUIZ_LOCKED` - Quiz prerequisite not met
- `MODULE_PREREQUISITE_NOT_MET` - Module locked
- `CIRCULAR_PREREQUISITE` - Circular dependency detected
- `LEITNER_NO_QUESTIONS` - No questions available for Leitner
- `ALREADY_ENROLLED` - Student already enrolled
- `CLASSROOM_CODE_INVALID` - Invalid classroom code
- `SESSION_ALREADY_FINISHED` - Session already completed
- `INVALID_QUESTION_COUNT` - Invalid Leitner question count

## 📚 Documentation References

- **[Endpoints](../doc/endpoints.md)** - Complete API endpoints documentation
- **[DTOs](../doc/dto.md)** - Data Transfer Objects with examples
- **[Class Diagram](../doc/class-diagram.md)** - Database architecture
- **[README](../README.md)** - Architectural principles

## 🔍 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 🛠️ Troubleshooting

### Common Issues

1. **Import errors**: Make sure the app module is available
2. **Database errors**: Check database connection and migrations
3. **Token errors**: Verify JWT secret configuration
4. **Fixture errors**: Ensure test data is properly seeded

### Debug Mode

```bash
# Run with full traceback
pytest tests/ --tb=long

# Run with pdb debugger on failure
pytest tests/ --pdb

# Verbose assertions
pytest tests/ -vv
```

## 📈 Coverage Goals

- **Line Coverage**: > 80%
- **Branch Coverage**: > 75%
- **Endpoint Coverage**: 100%
- **Status Code Coverage**: 100%

## ✨ Best Practices

1. **Test Isolation**: Each test is independent
2. **Clear Assertions**: Explicit status codes and data validation
3. **Descriptive Names**: Test names clearly indicate what is tested
4. **Documentation**: Each test has a docstring explaining expected behavior
5. **Fixtures**: Reusable test data and setup
6. **Cleanup**: Automatic cleanup after each test

---

**Last Updated**: February 2026
