# 🧪 Prompt Complet - Suite de Tests Exhaustive pour l'API Duobingo

## 📌 Objectif Principal

Créer une **suite de tests complète** qui teste **TOUS les endpoints** de l'API Duobingo avec :
- ✅ Tous les codes HTTP de retour (200, 201, 204, 400, 401, 403, 404, 409, 422, 500)
- ✅ Tous les types de retour (JSON, statut, messages d'erreur)
- ✅ Tous les types d'authentification (Bearer token, admin, prof, étudiant, pas d'auth, token invalide, permissions insuffisantes)
- ✅ Validation complète des structures de réponse
- ✅ Vérification des codes d'erreur métier

---

## 📚 Documentation de Référence

### Documentation officielle du projet :
1. **[Endpoints complets](doc/endpoints.md)** - 35+ endpoints détaillés avec :
   - Méthode HTTP
   - Paramètres (path, query, body)
   - Réponses attendues
   - Codes d'erreur métier
   - Règles de permission

2. **[DTOs (Data Transfer Objects)](doc/dto.md)** - 40+ structures avec :
   - Exemples JSON complets
   - Descriptions des champs
   - Champs calculés vs stockés
   - Types de questions polymorphes

3. **[Diagramme de classes](doc/class-diagram.md)** - Architecture du modèle de données

4. **[README explicatif](README.md)** - Principes de conception et choix architecturaux

### Comptes de test fournis :
- Admin : `admin@univ-rennes.fr` / `admin123`
- Prof responsable : `house@univ-rennes.fr` / `prof123`
- Prof secondaire : `wilson@univ-rennes.fr` / `prof123`
- Étudiant 1 : `marie.martin@univ-rennes.fr` / `student123`
- Étudiant 2 : `jean.dupont@univ-rennes.fr` / `student123`
- Classroom de test : Code `ANAT26`

---

## 🏗️ Structure des Tests

### 1. **Fichier `tests/conftest.py`** - Configuration globale

```python
# ✅ Créer les fixtures suivantes :

@pytest.fixture
def client():
    """Client de test FastAPI (TestClient)"""
    
@pytest.fixture
def admin_token():
    """Token JWT valide pour un Admin"""
    # Login avec admin@univ-rennes.fr
    
@pytest.fixture
def prof_responsible_token():
    """Token JWT valide pour un Prof Responsable"""
    # Login avec house@univ-rennes.fr
    
@pytest.fixture
def prof_secondary_token():
    """Token JWT valide pour un Prof secondaire"""
    # Login avec wilson@univ-rennes.fr
    
@pytest.fixture
def student_token():
    """Token JWT valide pour un Étudiant"""
    # Login avec marie.martin@univ-rennes.fr

@pytest.fixture
def invalid_token():
    """Token JWT invalide/expiré"""
    # Return "eyJhbGciOi..." (faux token)

@pytest.fixture
def classroom_id():
    """UUID d'une classroom créée pour les tests"""
    
@pytest.fixture
def module_id(classroom_id):
    """UUID d'un module créé pour les tests"""
    
@pytest.fixture
def quiz_id(module_id):
    """UUID d'un quiz créé pour les tests"""
    
@pytest.fixture
def question_id(quiz_id):
    """UUID d'une question créée pour les tests"""

# 🎯 Mock du service d'authentification (si besoin)
@pytest.fixture
def mock_auth_service(monkeypatch):
    """Mock du service d'auth pour tester différents scénarios"""
```

---

### 2. **Fichier `tests/test_auth.py`** - Authentification & Utilisateurs

**Endpoints à tester** (voir [doc/endpoints.md - Section 1](doc/endpoints.md#1-authentification--utilisateurs)) :

| Endpoint | Méthode | Code HTTP | Auth requise |
|----------|---------|-----------|--------------|
| `/api/auth/login` | POST | 200 / 401 | ❌ Non |
| `/api/auth/register` | POST | 201 / 400 / 409 | ❌ Non |
| `/api/users/me` | GET | 200 / 401 | ✅ Oui |
| `/api/users/me` | PATCH | 200 / 400 / 401 | ✅ Oui |
| `/api/admin/users` | POST | 201 / 403 / 400 | ✅ Admin |

**Tests à implémenter** :

```python
# POST /api/auth/login
def test_login_valid_credentials(client):
    """Connexion réussie avec credentials valides"""
    # Assertions : status 200, response contient JWT token

def test_login_invalid_password(client):
    """Échec de connexion avec mauvais mot de passe"""
    # Assertions : status 401

def test_login_user_not_found(client):
    """Échec de connexion utilisateur inexistant"""
    # Assertions : status 401

def test_login_missing_email(client):
    """Validation : email manquant"""
    # Assertions : status 400

def test_login_missing_password(client):
    """Validation : password manquant"""
    # Assertions : status 400

# POST /api/auth/register
def test_register_student_success(client):
    """Inscription étudiant réussie"""
    # Body : RegisterStudentDto (voir dto.md)
    # Assertions : status 201, response contient UserResponseDto

def test_register_duplicate_email(client):
    """Inscription avec email déjà utilisé"""
    # Assertions : status 409

def test_register_invalid_password(client):
    """Inscription avec password < 8 caractères"""
    # Assertions : status 400

def test_register_invalid_level(client):
    """Inscription avec niveau invalide"""
    # Assertions : status 400

# GET /api/users/me
def test_get_user_profile_authenticated(client, student_token):
    """Récupération du profil utilisateur authentifié"""
    # Headers : Authorization Bearer token
    # Assertions : status 200, response contient UserResponseDto

def test_get_user_profile_no_token(client):
    """Tentative sans token"""
    # Assertions : status 401

def test_get_user_profile_invalid_token(client, invalid_token):
    """Token invalide/expiré"""
    # Assertions : status 401

# PATCH /api/users/me
def test_update_user_email(client, student_token):
    """Modification du profil (email)"""
    # Assertions : status 200, email mis à jour

def test_update_user_invalid_email(client, student_token):
    """Validation format email"""
    # Assertions : status 400

# POST /api/admin/users
def test_create_teacher_as_admin(client, admin_token):
    """Création d'un compte Professeur par Admin"""
    # Assertions : status 201

def test_create_teacher_as_student(client, student_token):
    """Tentative par étudiant (permission insuffisante)"""
    # Assertions : status 403

def test_create_user_invalid_role(client, admin_token):
    """Validation rôle"""
    # Assertions : status 400
```

---

### 3. **Fichier `tests/test_classrooms.py`** - Gestion des Cours

**Endpoints à tester** (voir [doc/endpoints.md - Section 2](doc/endpoints.md#2-gestion-des-cours-classroom)) :

| Endpoint | Méthode | Scénarios |
|----------|---------|-----------|
| `/api/classrooms` | GET | Tous, filtrés par rôle |
| `/api/classrooms` | POST | Succès, validation |
| `/api/classrooms/{id}` | GET | Accès autorisé, non membre, 404 |
| `/api/classrooms/{id}` | PATCH | Prof responsable, prof secondaire, étudiant |
| `/api/classrooms/{id}` | DELETE | Prof responsable, autres (403), 404 |
| `/api/classrooms/{id}/members` | GET | Pagination, permissions |
| `/api/classrooms/{id}/teachers` | POST | Ajout prof, validation email |
| `/api/classrooms/{id}/teachers/{tid}` | DELETE | Retrait prof, permissions |
| `/api/classrooms/{id}/enroll` | POST | Inscription étudiant, validation |
| `/api/classrooms/{id}/students/{sid}` | DELETE | Retrait étudiant |
| `/api/classrooms/{id}/join` | POST | Rejoindre avec code (étudiant) |
| `/api/classrooms/{id}/regenerate-code` | POST | Génération nouveau code |

**Tests critiques** :

```python
def test_create_classroom_success(client, prof_responsible_token):
    """Création d'une classroom"""
    body = { "name": "Anatomie L1", "level": "L1" }
    # Assertions : status 201, response contient ClassroomDto, code généré

def test_list_classrooms_student(client, student_token):
    """Étudiant voit ses classrooms (inscrits)"""
    # Assertions : status 200, list filtrée

def test_list_classrooms_professor(client, prof_responsible_token):
    """Prof voit ses classrooms (gérées)"""
    # Assertions : status 200, list filtrée

def test_get_classroom_as_member(client, student_token, classroom_id):
    """Accès autorisé (membre)"""
    # Assertions : status 200

def test_get_classroom_as_non_member(client, student_token, other_classroom_id):
    """Accès refusé (non membre)"""
    # Assertions : status 403

def test_patch_classroom_as_responsible(client, prof_responsible_token, classroom_id):
    """Modification par prof responsable"""
    body = { "name": "Anatomie L2" }
    # Assertions : status 200

def test_patch_classroom_as_secondary_prof(client, prof_secondary_token, classroom_id):
    """Tentative par prof secondaire"""
    # Assertions : status 403

def test_delete_classroom_cascade(client, prof_responsible_token, classroom_id):
    """Suppression cascade (modules, quiz, sessions)"""
    # Assertions : status 204
    # Vérifier que modules/quiz associés sont supprimés

def test_join_classroom_valid_code(client, student_token):
    """Rejoindre avec code valide"""
    body = { "code": "ANAT26" }
    # Assertions : status 200

def test_join_classroom_invalid_code(client, student_token):
    """Code invalide"""
    body = { "code": "INVALID" }
    # Assertions : status 400 CLASSROOM_CODE_INVALID

def test_join_classroom_already_enrolled(client, student_token, classroom_id):
    """Déjà inscrit"""
    # Assertions : status 409 ALREADY_ENROLLED

def test_regenerate_code(client, prof_responsible_token, classroom_id):
    """Régénération du code"""
    # Assertions : status 200, newCode généré, oldCode invalidé
```

---

### 4. **Fichier `tests/test_modules.py`** - Gestion des Modules

**Endpoints à tester** (voir [doc/endpoints.md - Section 3](doc/endpoints.md#3-gestion-des-modules)) :

```python
def test_list_modules(client, student_token, classroom_id):
    """Lister modules d'un cours"""
    # Pagination, permission
    
def test_create_module_success(client, prof_responsible_token, classroom_id):
    """Création de module"""
    body = { "name": "Membre Inférieur", "category": "Ostéologie" }
    # Assertions : status 201

def test_create_module_with_prerequisite(client, prof_responsible_token, classroom_id, prereq_module_id):
    """Module avec prérequis"""
    body = { "name": "...", "prerequisiteModuleId": prereq_module_id }
    # Assertions : status 201

def test_create_module_circular_prerequisite(client, prof_responsible_token, classroom_id, module_a_id, module_b_id):
    """Détection de dépendance circulaire (A → B → A)"""
    # Assertions : status 422 CIRCULAR_PREREQUISITE

def test_module_is_locked_for_student(client, student_token, locked_module_id):
    """Module verrouillé (prérequis non satisfait)"""
    # Vérifier isLocked = true dans response

def test_module_unlocked_after_prerequisite(client, student_token, module_id):
    """Module débloqué après complétion du prérequis"""
    # Assertions : isLocked = false

def test_update_module(client, prof_responsible_token, module_id):
    """Modification de module"""
    # Assertions : status 200

def test_delete_module_cascade(client, prof_responsible_token, module_id):
    """Suppression cascade (quiz, questions, sessions)"""
    # Assertions : status 204
```

---

### 5. **Fichier `tests/test_quizzes.py`** - Gestion des Quiz

```python
def test_list_quizzes(client, student_token, module_id):
    """Lister quiz d'un module"""
    
def test_create_quiz_success(client, prof_responsible_token, module_id):
    """Création de quiz"""
    body = {
        "title": "Le Pied",
        "minScoreToUnlockNext": 15,
        "isActive": True
    }
    # Assertions : status 201, questionCount = 0

def test_create_quiz_with_prerequisite(client, prof_responsible_token, module_id, prereq_quiz_id):
    """Quiz avec prérequis"""
    # Assertions : status 201

def test_quiz_locked_prerequisite_not_met(client, student_token, locked_quiz_id):
    """Quiz verrouillé (prérequis non satisfait)"""
    # Assertions : isLocked = true, status 403 si tentative de jouer

def test_quiz_unlocked_after_prerequisite(client, student_token, quiz_id):
    """Quiz débloqué après réussite du prérequis"""
    # Assertions : isLocked = false

def test_update_quiz(client, prof_responsible_token, quiz_id):
    """Modification quiz (minScore, isActive)"""
    
def test_delete_quiz_cascade(client, prof_responsible_token, quiz_id):
    """Suppression cascade (questions, sessions)"""
    # Assertions : status 204
```

---

### 6. **Fichier `tests/test_questions.py`** - Banque de Questions (5 types polymorphes)

**Types de questions** (voir [doc/dto.md - QuestionCreateDto](doc/dto.md#questioncreatedto-polymorphe)) :

```python
# QCM (Choix Multiple)
def test_create_qcm_question(client, prof_responsible_token, quiz_id):
    """Création QCM"""
    body = {
        "type": "QCM",
        "contentText": "Quel os constitue le talon ?",
        "options": [
            { "textChoice": "Calcanéus", "isCorrect": True },
            { "textChoice": "Talus", "isCorrect": False }
        ],
        "explanation": "Le calcanéus..."
    }
    # Assertions : status 201

# VRAI/FAUX
def test_create_truefalse_question(client, prof_responsible_token, quiz_id):
    """Création Vrai/Faux"""
    body = {
        "type": "VRAI_FAUX",
        "contentText": "Le tibia est l'os interne de la jambe",
        "options": [
            { "textChoice": "Vrai", "isCorrect": True },
            { "textChoice": "Faux", "isCorrect": False }
        ]
    }
    # Assertions : status 201

# MATCHING (Appariement)
def test_create_matching_question(client, prof_responsible_token, quiz_id):
    """Création Appariement"""
    body = {
        "type": "MATCHING",
        "contentText": "Appariez les os avec leur localisation",
        "matchingPairs": [
            { "itemLeft": "Tibia", "itemRight": "Interne" },
            { "itemLeft": "Fibula", "itemRight": "Externe" }
        ]
    }
    # Assertions : status 201

# TEXT (Saisie textuelle)
def test_create_text_question(client, prof_responsible_token, quiz_id):
    """Création Text"""
    body = {
        "type": "TEXT",
        "contentText": "Nommez l'os du talon",
        "textConfig": {
            "acceptedAnswer": "Calcanéus",
            "isCaseSensitive": False,
            "ignoreSpellingErrors": True
        }
    }
    # Assertions : status 201

# IMAGE (Zones cliquables)
def test_create_image_question(client, prof_responsible_token, quiz_id, media_id):
    """Création Image avec zones"""
    body = {
        "type": "IMAGE",
        "contentText": "Cliquez sur le talus",
        "mediaId": media_id,
        "imageZones": [
            { "labelName": "Talus", "x": 50, "y": 60, "radius": 15 },
            { "labelName": "Calcanéus", "x": 40, "y": 80, "radius": 20 }
        ]
    }
    # Assertions : status 201

# Tests généraux sur questions
def test_update_question(client, prof_responsible_token, question_id):
    """Modification question"""

def test_delete_question_removes_from_leitner(client, prof_responsible_token, question_id):
    """Suppression retire la question des boîtes Leitner"""

def test_question_visibility_in_session(client, student_token, session_id, question_id):
    """Les réponses ne sont pas visibles pendant la session (anti-triche)"""
    # Faire un GET pour voir les questions
    # Assertions : options ne contiennent pas isCorrect
```

---

### 7. **Fichier `tests/test_sessions.py`** - Gameplay (Quiz)

**Endpoints** (voir [doc/endpoints.md - Section 6](doc/endpoints.md#6-gameplay--session-étudiant)) :

```python
# POST /api/sessions/start
def test_start_session_success(client, student_token, accessible_quiz_id):
    """Démarrage d'une session"""
    body = { "quizId": accessible_quiz_id }
    # Assertions : status 200, sessionId, questions (sans réponses correctes)

def test_start_session_locked_quiz(client, student_token, locked_quiz_id):
    """Tentative sur quiz verrouillé"""
    # Assertions : status 403 QUIZ_LOCKED

def test_start_session_not_a_student(client, prof_responsible_token, quiz_id):
    """Prof ne peut pas jouer"""
    # Assertions : status 403

# POST /api/sessions/{sid}/submit-answer
def test_submit_answer_correct(client, student_token, session_id, question_id):
    """Soumettre une réponse correcte"""
    body = {
        "questionId": question_id,
        "selectedOptionId": "correct_option_id"  # Pour QCM
    }
    # Assertions : status 200, isCorrect = true, pas de correction

def test_submit_answer_incorrect(client, student_token, session_id, question_id):
    """Soumettre une réponse incorrecte"""
    # Assertions : status 200, isCorrect = false

def test_submit_answer_text_with_typo(client, student_token, session_id, text_question_id):
    """Text: réponse avec typo (ignorSpellingErrors = true)"""
    body = {
        "questionId": text_question_id,
        "textResponse": "Calcaneum"  # Typo
    }
    # Assertions : status 200, isCorrect = true

def test_submit_answer_image_click(client, student_token, session_id, image_question_id):
    """Image: clic dans une zone"""
    body = {
        "questionId": image_question_id,
        "clickedCoordinates": { "x": 50, "y": 60 }
    }
    # Assertions : status 200, isCorrect = true

def test_submit_answer_matching(client, student_token, session_id, matching_question_id):
    """Matching: appariement correct"""
    body = {
        "questionId": matching_question_id,
        "matchedPairs": [
            { "leftId": "tibia_id", "rightId": "interne_id" },
            { "leftId": "fibula_id", "rightId": "externe_id" }
        ]
    }
    # Assertions : status 200, isCorrect = true

def test_submit_answer_session_not_found(client, student_token):
    """Session inexistante"""
    # Assertions : status 404

def test_submit_answer_session_already_finished(client, student_token, finished_session_id):
    """Session déjà terminée"""
    # Assertions : status 400 SESSION_ALREADY_FINISHED

# POST /api/sessions/{sid}/finish
def test_finish_session_with_passing_score(client, student_token, session_id):
    """Terminer avec score >= minScoreToUnlockNext"""
    # Assertions : status 200, passed = true
    # Vérifier que CompletedQuiz est créé
    # Vérifier que questions ajoutées en LeitnerBox 1

def test_finish_session_with_failing_score(client, student_token, session_id):
    """Terminer avec score < minScoreToUnlockNext"""
    # Assertions : status 200, passed = false
    # Vérifier que CompletedQuiz n'est pas créé

def test_finish_session_unlock_next_module(client, student_token, session_id):
    """Terminer avec succès débloque le module suivant"""
    # Assertions : status 200, passed = true
    # Vérifier que CompletedModule est créé

def test_finish_unlocks_next_quiz(client, student_token, session_id, next_quiz_id):
    """Terminer avec succès débloque le quiz suivant"""
    # Assertions : isLocked = false pour next_quiz_id

# GET /api/sessions/{sid}/review
def test_review_session_before_finish(client, student_token, in_progress_session_id):
    """Correction non disponible avant fin"""
    # Assertions : status 404 ou 403

def test_review_session_after_finish(client, student_token, finished_session_id):
    """Correction complète après fin"""
    # Assertions : status 200, contient correct answers + explanations
```

---

### 8. **Fichier `tests/test_leitner.py`** - Système de Révision Espacée

**Endpoints** (voir [doc/endpoints.md - Section 7](doc/endpoints.md#système-leitner-révision-espacée)) :

```python
# GET /api/classrooms/{cid}/leitner/status
def test_get_leitner_status(client, student_token, classroom_id):
    """État des 5 boîtes"""
    # Assertions : status 200
    # Vérifier boxes[1..5] avec count et distribution %

def test_leitner_status_no_questions(client, student_token, empty_classroom_id):
    """Classroom avec aucune question débloquée"""
    # Assertions : status 200, totalQuestions = 0

# POST /api/classrooms/{cid}/leitner/start
def test_start_leitner_session_10_questions(client, student_token, classroom_id):
    """Démarrer révision avec 10 questions"""
    body = { "questionCount": 10 }
    # Assertions : status 200, sessionId, 10 questions sélectionnées
    # Vérifier distribution par boîte (50%, 25%, 15%, 7%, 3%)

def test_start_leitner_session_5_questions(client, student_token, classroom_id):
    """Démarrer avec 5 questions"""
    body = { "questionCount": 5 }
    # Assertions : status 200, 5 questions

def test_start_leitner_session_invalid_count(client, student_token, classroom_id):
    """Nombre de questions invalide (6 au lieu de 5/10/15/20)"""
    body = { "questionCount": 6 }
    # Assertions : status 400 INVALID_QUESTION_COUNT

def test_start_leitner_no_questions_available(client, student_token, empty_classroom_id):
    """Aucune question disponible"""
    body = { "questionCount": 10 }
    # Assertions : status 400 LEITNER_NO_QUESTIONS

# POST /api/leitner/sessions/{sid}/submit-answer
def test_leitner_submit_correct_answer(client, student_token, leitner_session_id, question_id):
    """Réponse correcte"""
    # Assertions : status 200, isCorrect = true

def test_leitner_submit_incorrect_answer(client, student_token, leitner_session_id, question_id):
    """Réponse incorrecte"""
    # Assertions : status 200, isCorrect = false

# POST /api/leitner/sessions/{sid}/finish
def test_finish_leitner_session(client, student_token, leitner_session_id):
    """Terminer la révision"""
    # Assertions : status 200
    # Vérifier promoted (réponses correctes)
    # Vérifier demoted (réponses incorrectes)
    # Vérifier newBoxDistribution

def test_leitner_promotion_rules(client, student_token, leitner_session_id):
    """Vérifier les règles de promotion des boîtes"""
    # Box 1 + correct → Box 2
    # Box 2 + incorrect → Box 1
    # etc.

def test_leitner_demotion_to_box_1(client, student_token, leitner_session_id):
    """Mauvaise réponse = retour à Box 1"""
    # Question en Box 3 + incorrect → Box 1

# GET /api/leitner/sessions/{sid}/review
def test_leitner_review_after_finish(client, student_token, finished_leitner_session_id):
    """Correction Leitner après fin"""
    # Assertions : status 200
    # Vérifier answers avec previousBox, newBox, explanation
    # Vérifier summary (accuracy, promoted, demoted)
```

---

### 9. **Fichier `tests/test_stats.py`** - Statistiques & Progression

**Endpoints** (voir [doc/endpoints.md - Section 7](doc/endpoints.md#progression--statistiques)) :

```python
# GET /api/stats/student
def test_student_stats_complete(client, student_token):
    """Statistiques personnelles complètes"""
    # Assertions : status 200
    # Vérifier totalCompletedQuizzes, averageScore, leitnerMastery
    # Vérifier classroomsProgress[]

def test_student_stats_with_no_progress(client, new_student_token):
    """Étudiant sans progrès"""
    # Assertions : status 200, totalCompletedQuizzes = 0, averageScore = 0

# GET /api/stats/leaderboard/{cid}
def test_leaderboard_ranking(client, student_token, classroom_id):
    """Classement d'une classroom"""
    # Assertions : status 200, pagination
    # Vérifier tri (completedQuizzes desc, averageScore desc)
    # Vérifier rank, studentName, averageScore, leitnerMastery

def test_leaderboard_pagination(client, student_token, classroom_id):
    """Pagination leaderboard"""
    # Assertions : status 200, hasNextPage, totalPages

def test_leaderboard_not_member(client, student_token, other_classroom_id):
    """Étudiant non membre"""
    # Assertions : status 403

# GET /api/stats/dashboard/{cid}
def test_professor_dashboard(client, prof_responsible_token, classroom_id):
    """Dashboard professeur"""
    # Assertions : status 200
    # Vérifier modulesStats[], hardestQuestions, leitnerStats
    # Vérifier alertStudents (étudiants en difficulté)

def test_dashboard_non_professor(client, student_token, classroom_id):
    """Étudiant accède au dashboard"""
    # Assertions : status 403

# GET /api/progress/modules/{moduleId}
def test_module_progress(client, student_token, module_id):
    """Progression sur un module"""
    # Assertions : status 200
    # Vérifier isCompleted, completionRate, quizzes[]

# GET /api/progress/quizzes/{quizId}
def test_quiz_progress(client, student_token, quiz_id):
    """Progression sur un quiz"""
    # Assertions : status 200
    # Vérifier bestScore, attemptsCount, isCompleted

# GET /api/progress/classroom/{cid}
def test_classroom_progress(client, student_token, classroom_id):
    """Progression globale dans un cours"""
    # Assertions : status 200, Array<ModuleProgressDto>
    # Vérifier tous les modules avec progression

# GET /api/progress/classroom/{cid}/student/{sid}
def test_student_progress_view_professor(client, prof_responsible_token, classroom_id, student_id):
    """Vue prof de la progression d'un étudiant"""
    # Assertions : status 200

def test_student_progress_view_unauthorized(client, other_student_token, classroom_id, student_id):
    """Étudiant ne peut pas voir la progression d'un autre"""
    # Assertions : status 403
```

---

### 10. **Fichier `tests/test_media.py`** - Upload de Médias

**Endpoints** (voir [doc/endpoints.md - Section 5](doc/endpoints.md#banque-de-questions)) :

```python
# POST /api/media
def test_upload_image_success(client, prof_responsible_token):
    """Upload d'une image (JPG/PNG)"""
    # Body : multipart/form-data avec image
    # Assertions : status 200 / 201, mediaId, url

def test_upload_invalid_file_type(client, prof_responsible_token):
    """Upload d'un fichier non-image (PDF)"""
    # Assertions : status 400

def test_upload_file_too_large(client, prof_responsible_token):
    """Fichier > limite"""
    # Assertions : status 413

# GET /api/media
def test_list_media(client, prof_responsible_token):
    """Lister ses médias"""
    # Assertions : status 200, pagination

# DELETE /api/media/{mediaId}
def test_delete_unused_media(client, prof_responsible_token, unused_media_id):
    """Supprimer un média non utilisé"""
    # Assertions : status 204

def test_delete_used_media(client, prof_responsible_token, used_media_id):
    """Tentative de suppression d'un média utilisé"""
    # Assertions : status 400 (ou 409)

# GET /api/media/orphaned
def test_list_orphaned_media(client, admin_token):
    """Admin: médias non utilisés"""
    # Assertions : status 200
```

---

## 📊 Matrice de Tests (Résumé)

| Domaine | Endpoint | Cas de test | Token | Code HTTP |
|---------|----------|------------|-------|-----------|
| **Auth** | POST /login | valid, invalid, missing | ❌ | 200, 401, 400 |
| **Auth** | POST /register | success, duplicate, validation | ❌ | 201, 409, 400 |
| **Classroom** | GET /classrooms | student, professor, filtered | ✅ | 200 |
| **Classroom** | POST /classrooms | success, validation | ✅ Prof | 201, 400 |
| **Classroom** | GET /{id} | member, non-member, 404 | ✅ | 200, 403, 404 |
| **Classroom** | PATCH /{id} | responsible, secondary, 403 | ✅ Prof | 200, 403 |
| **Classroom** | DELETE /{id} | cascade, 403, 404 | ✅ Prof | 204, 403, 404 |
| **Classroom** | POST /join | valid code, invalid, 409 | ✅ Student | 200, 400, 409 |
| **Module** | GET /modules | list, pagination | ✅ | 200 |
| **Module** | POST /modules | success, circular dep | ✅ Prof | 201, 422 |
| **Module** | PATCH /{id} | success, 403, 404 | ✅ Prof | 200, 403, 404 |
| **Module** | DELETE /{id} | cascade, 403 | ✅ Prof | 204, 403 |
| **Quiz** | GET /quizzes | list, locked, unlocked | ✅ | 200 |
| **Quiz** | POST /quizzes | success, circular dep | ✅ Prof | 201, 422 |
| **Quiz** | PATCH /{id} | success, 403 | ✅ Prof | 200, 403 |
| **Quiz** | DELETE /{id} | cascade, 403 | ✅ Prof | 204, 403 |
| **Question** | POST /questions | QCM, TEXT, IMAGE, MATCHING | ✅ Prof | 201, 400 |
| **Question** | PATCH /{id} | update, 403, 404 | ✅ Prof | 200, 403, 404 |
| **Question** | DELETE /{id} | removes from Leitner, 403 | ✅ Prof | 204, 403 |
| **Session** | POST /start | success, locked, 403 | ✅ Student | 200, 403 |
| **Session** | POST /submit-answer | correct, incorrect, validation | ✅ Student | 200, 400 |
| **Session** | POST /finish | pass, fail, unlock next | ✅ Student | 200 |
| **Session** | GET /review | after finish, not before | ✅ Student | 200, 404 |
| **Leitner** | GET /status | boxes, distribution | ✅ Student | 200 |
| **Leitner** | POST /start | 5/10/15/20, invalid count | ✅ Student | 200, 400 |
| **Leitner** | POST /submit-answer | correct, incorrect | ✅ Student | 200, 400 |
| **Leitner** | POST /finish | promotion rules, demotion | ✅ Student | 200 |
| **Leitner** | GET /review | after finish | ✅ Student | 200, 404 |
| **Stats** | GET /student | complete, no progress | ✅ | 200 |
| **Stats** | GET /leaderboard | ranking, pagination, 403 | ✅ | 200, 403 |
| **Stats** | GET /dashboard | modules, hardest, alert | ✅ Prof | 200, 403 |
| **Progress** | GET /modules/{id} | completion, quizzes | ✅ | 200 |
| **Progress** | GET /quizzes/{id} | best score, attempts | ✅ | 200 |
| **Progress** | GET /classroom/{id} | all modules | ✅ | 200 |

---

## 🚀 Exécution des Tests

```bash
# Tous les tests
pytest tests/ -v

# Tests spécifiques
pytest tests/test_auth.py -v
pytest tests/test_sessions.py::test_start_session_success -v

# Avec couverture de code
pytest tests/ --cov=app --cov-report=html

# Arrêt à la première erreur
pytest tests/ -x

# Mode verbose + affichage des prints
pytest tests/ -vv -s

# Uniquement tests rapides (marqués @pytest.mark.fast)
pytest tests/ -m fast
```

---

## 📌 Remarques Importantes

1. **Mocking du service d'auth** : Utilisez `unittest.mock` pour mocker `auth_service.verify_token()` si l'implémentation n'existe pas encore
2. **Tokens de test** : Créez les tokens avec `jose` ou directement par fixture
3. **Base de données de test** : Utilisez une BD SQLite séparée (`:memory:` ou `test.db`)
4. **Fixtures partagées** : Réutilisez les fixtures dans `conftest.py`
5. **Données seed** : Utilisez `seed_data.py` ou créez les données dans les fixtures
6. **Isolation** : Chaque test doit être indépendant (pas de dépendances d'ordre)
7. **Nettoyage** : Utilisez `autouse=True` pour nettoyer après chaque test

---

## 📖 Lien vers Documentation Complète

- **Endpoints détaillés** : [doc/endpoints.md](doc/endpoints.md)
- **DTOs avec exemples JSON** : [doc/dto.md](doc/dto.md)
- **Architecture et principes** : [README.md](README.md)
- **Diagramme de classes** : [doc/class-diagram.md](doc/class-diagram.md)
