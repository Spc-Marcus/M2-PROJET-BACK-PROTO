# Test Coverage Matrix - Duobingo API

## Complete Test Coverage Overview

### 1. Authentication & Users (`test_auth.py`) - 20 Tests

| Test | Endpoint | Method | Auth | HTTP Codes |
|------|----------|--------|------|------------|
| test_login_valid_credentials | /api/auth/login | POST | ❌ | 200 |
| test_login_invalid_password | /api/auth/login | POST | ❌ | 401 |
| test_login_user_not_found | /api/auth/login | POST | ❌ | 401 |
| test_login_missing_email | /api/auth/login | POST | ❌ | 400, 422 |
| test_login_missing_password | /api/auth/login | POST | ❌ | 400, 422 |
| test_login_invalid_email_format | /api/auth/login | POST | ❌ | 400, 422 |
| test_login_empty_credentials | /api/auth/login | POST | ❌ | 400, 422 |
| test_register_student_success | /api/auth/register | POST | ❌ | 201 |
| test_register_duplicate_email | /api/auth/register | POST | ❌ | 409 |
| test_register_invalid_password_too_short | /api/auth/register | POST | ❌ | 400 |
| test_register_invalid_level | /api/auth/register | POST | ❌ | 400 |
| test_register_missing_required_fields | /api/auth/register | POST | ❌ | 400, 422 |
| test_register_valid_levels | /api/auth/register | POST | ❌ | 201 |
| test_get_user_profile_authenticated | /api/users/me | GET | Student | 200 |
| test_get_user_profile_no_token | /api/users/me | GET | ❌ | 401 |
| test_get_user_profile_invalid_token | /api/users/me | GET | Invalid | 401 |
| test_get_user_profile_expired_token | /api/users/me | GET | Expired | 401 |
| test_update_user_email | /api/users/me | PATCH | Student | 200 |
| test_create_teacher_as_admin | /api/admin/users | POST | Admin | 201 |
| test_create_teacher_as_student | /api/admin/users | POST | Student | 403 |

### 2. Classrooms (`test_classrooms.py`) - 40+ Tests

| Category | Tests | HTTP Codes Tested |
|----------|-------|-------------------|
| List Classrooms | 5 | 200, 401 |
| Create Classroom | 5 | 201, 400, 403, 422 |
| Get Classroom | 4 | 200, 403, 404, 401 |
| Update Classroom | 4 | 200, 403, 404 |
| Delete Classroom | 4 | 204, 403, 404 |
| Members Management | 6 | 200, 403 |
| Teacher Management | 6 | 200, 201, 204, 403, 404 |
| Student Management | 6 | 200, 201, 204, 403, 404, 409 |
| Join with Code | 5 | 200, 400, 403, 404, 409 |
| Regenerate Code | 4 | 200, 403 |

**Key Business Rules Tested:**
- ✅ Prof Responsible permissions
- ✅ Secondary Prof limitations
- ✅ Student enrollment
- ✅ Code validation (CLASSROOM_CODE_INVALID)
- ✅ Duplicate enrollment (ALREADY_ENROLLED)
- ✅ Cascade deletion

### 3. Modules (`test_modules.py`) - 20+ Tests

| Category | Tests | Business Logic |
|----------|-------|----------------|
| List Modules | 4 | Pagination, permissions |
| Create Module | 6 | Prerequisites, circular detection |
| Get Module | 5 | Locking status, prerequisites |
| Update Module | 4 | Prerequisites validation |
| Delete Module | 4 | Cascade deletion |

**Key Business Rules Tested:**
- ✅ Circular prerequisite detection (CIRCULAR_PREREQUISITE)
- ✅ Module locking based on prerequisites
- ✅ Cascade deletion of quizzes, questions, sessions

### 4. Quizzes (`test_quizzes.py`) - 25+ Tests

| Category | Tests | Business Logic |
|----------|-------|----------------|
| List Quizzes | 4 | Locked status, pagination |
| Create Quiz | 6 | Prerequisites, validation |
| Get Quiz | 5 | Locking, prerequisites |
| Update Quiz | 5 | Active/inactive, prerequisites |
| Delete Quiz | 4 | Cascade deletion |

**Key Business Rules Tested:**
- ✅ Circular prerequisite detection
- ✅ Quiz locking (QUIZ_LOCKED)
- ✅ Active/inactive state
- ✅ minScoreToUnlockNext validation

### 5. Questions (`test_questions.py`) - 40+ Tests

| Question Type | Tests | Validation |
|---------------|-------|------------|
| QCM (Multiple Choice) | 8 | Options, correct answers |
| VRAI_FAUX (True/False) | 3 | Exactly 2 options |
| MATCHING (Pairing) | 4 | Pairs, minimum count |
| TEXT (Text Input) | 6 | Case sensitivity, fuzzy matching |
| IMAGE (Clickable Zones) | 6 | Media ID, zones, coordinates |
| General CRUD | 8 | Permissions, deletion, Leitner |

**Key Features Tested:**
- ✅ All 5 polymorphic question types
- ✅ Type-specific validation
- ✅ Media integration (IMAGE type)
- ✅ Leitner box integration on deletion
- ✅ Anti-cheat (hiding correct answers during gameplay)

### 6. Quiz Sessions (`test_sessions.py`) - 45+ Tests

| Category | Tests | Question Types Covered |
|----------|-------|----------------------|
| Start Session | 7 | All types, locking |
| Submit Answer - QCM | 3 | Single, multiple |
| Submit Answer - TEXT | 4 | Exact, fuzzy, case |
| Submit Answer - IMAGE | 2 | Click zones |
| Submit Answer - MATCHING | 3 | Correct, incorrect, partial |
| Submit Answer - Errors | 4 | Session state validation |
| Finish Session | 7 | Scoring, unlocking, Leitner |
| Review Session | 6 | Corrections, explanations |

**Key Business Rules Tested:**
- ✅ Quiz locking (QUIZ_LOCKED)
- ✅ Session state management
- ✅ Score calculation
- ✅ Unlocking next quizzes/modules
- ✅ Leitner Box 1 addition on success
- ✅ Review system with explanations

### 7. Leitner System (`test_leitner.py`) - 30+ Tests

| Category | Tests | Business Logic |
|----------|-------|----------------|
| Box Status | 5 | 5 boxes, distribution |
| Start Session | 8 | 5/10/15/20 questions, distribution |
| Submit Answer | 4 | Correct, incorrect |
| Finish Session | 7 | Promotion, demotion, stats |
| Review Session | 6 | Box movements, explanations |

**Key Business Rules Tested:**
- ✅ Question distribution (50%, 25%, 15%, 7%, 3%)
- ✅ Promotion rules (Box N → Box N+1)
- ✅ Demotion rules (Any Box → Box 1 on incorrect)
- ✅ Box 5 stays at Box 5
- ✅ Question count validation (5, 10, 15, 20 only)
- ✅ No questions available (LEITNER_NO_QUESTIONS)

### 8. Statistics & Progress (`test_stats.py`) - 35+ Tests

| Category | Tests | Calculations |
|----------|-------|--------------|
| Student Stats | 5 | Total quizzes, avg score, Leitner mastery |
| Leaderboard | 7 | Ranking, sorting, pagination |
| Professor Dashboard | 6 | Module stats, hardest questions, alerts |
| Module Progress | 4 | Completion rate, quizzes |
| Quiz Progress | 4 | Best score, attempts |
| Classroom Progress | 4 | All modules |
| Student View (Prof) | 5 | Permissions, data access |

**Key Calculations Tested:**
- ✅ Total completed quizzes (COUNT)
- ✅ Average score (AVG)
- ✅ Leitner mastery (% in boxes 4-5)
- ✅ Completion rate
- ✅ Leaderboard sorting (completedQuizzes DESC, averageScore DESC)
- ✅ Hardest questions (lowest success rate)

### 9. Media Management (`test_media.py`) - 30+ Tests

| Category | Tests | Validation |
|----------|-------|------------|
| Upload | 9 | JPG, PNG, size, type |
| List Media | 5 | Pagination, filtering |
| Get Media | 3 | Access, not found |
| Delete Media | 7 | Usage check, permissions |
| Orphaned Media | 4 | Detection, admin access |
| Integration | 2 | Question association |

**Key Business Rules Tested:**
- ✅ File type validation (image/* only)
- ✅ File size limits (413 error)
- ✅ Deletion blocked if in use (400/409)
- ✅ Orphaned media detection
- ✅ Professor-only upload
- ✅ Filename sanitization

## HTTP Status Code Coverage

| Code | Description | Tests |
|------|-------------|-------|
| 200 | OK | 150+ |
| 201 | Created | 40+ |
| 204 | No Content | 25+ |
| 400 | Bad Request | 50+ |
| 401 | Unauthorized | 30+ |
| 403 | Forbidden | 45+ |
| 404 | Not Found | 35+ |
| 409 | Conflict | 10+ |
| 422 | Unprocessable Entity | 8+ |
| 413 | Payload Too Large | 2+ |

## Authentication Scenario Coverage

| Scenario | Tests | Endpoints |
|----------|-------|-----------|
| Admin | 15+ | All admin endpoints |
| Prof Responsible | 80+ | Classroom, module, quiz management |
| Prof Secondary | 25+ | Quiz, question management |
| Student | 100+ | Sessions, progress, stats |
| No Auth | 30+ | Public endpoints, 401 errors |
| Invalid Token | 10+ | All protected endpoints |
| Expired Token | 5+ | Token expiration |

## Business Error Codes Coverage

| Error Code | Tests | Endpoints |
|------------|-------|-----------|
| QUIZ_LOCKED | 5 | Sessions, quizzes |
| MODULE_PREREQUISITE_NOT_MET | 3 | Modules |
| CIRCULAR_PREREQUISITE | 4 | Modules, quizzes |
| LEITNER_NO_QUESTIONS | 2 | Leitner sessions |
| ALREADY_ENROLLED | 2 | Classroom enrollment |
| CLASSROOM_CODE_INVALID | 2 | Classroom join |
| SESSION_ALREADY_FINISHED | 3 | Session operations |
| INVALID_QUESTION_COUNT | 1 | Leitner sessions |

## Test File Summary

| File | Tests | Lines | Coverage Focus |
|------|-------|-------|----------------|
| test_auth.py | 20+ | ~500 | Authentication, authorization |
| test_classrooms.py | 40+ | ~800 | Classroom CRUD, membership |
| test_modules.py | 20+ | ~450 | Module CRUD, prerequisites |
| test_quizzes.py | 25+ | ~500 | Quiz CRUD, locking |
| test_questions.py | 40+ | ~700 | 5 question types, validation |
| test_sessions.py | 45+ | ~800 | Gameplay, all question types |
| test_leitner.py | 30+ | ~700 | Spaced repetition, box rules |
| test_stats.py | 35+ | ~700 | Statistics, progress, leaderboard |
| test_media.py | 30+ | ~600 | Upload, validation, orphans |
| **TOTAL** | **280+** | **~5,750** | **Complete API coverage** |

## Validation Coverage

| Validation Type | Tests | Examples |
|----------------|-------|----------|
| Required Fields | 25+ | Missing email, password, name |
| Format Validation | 15+ | Email format, password length |
| Enum Validation | 10+ | Level (L1-M2), question type |
| Range Validation | 8+ | minScoreToUnlockNext >= 0 |
| Uniqueness | 6+ | Email, classroom code |
| File Type | 5+ | Image vs non-image |
| File Size | 2+ | Max upload size |
| Business Rules | 15+ | Circular deps, prerequisites |

## Edge Cases Tested

- ✅ Empty lists/responses
- ✅ Pagination boundaries
- ✅ Maximum values
- ✅ Duplicate operations
- ✅ Concurrent access scenarios
- ✅ Partial correctness (matching questions)
- ✅ Case sensitivity (text questions)
- ✅ Fuzzy matching (text questions)
- ✅ Coordinate validation (image questions)
- ✅ Box boundary conditions (Leitner)

---

**Total Coverage**: 280+ tests covering 35+ endpoints, 10 HTTP status codes, 7 authentication scenarios, and 8+ business error codes.
