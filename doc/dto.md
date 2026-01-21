# DTOs (Data Transfer Objects) - Duobingo API

Ce document recense l'ensemble des DTOs utilisés dans l'API Duobingo.

---

## 0. DTOs Génériques

### PaginatedResponseDto<T>
*Réponse paginée pour les listes longues.*

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "limit": 20,
    "totalItems": 150,
    "totalPages": 8,
    "hasNextPage": true,
    "hasPreviousPage": false
  }
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `data` | Array<T> | Liste des éléments de la page courante |
| `pagination.page` | Integer | Numéro de la page actuelle |
| `pagination.limit` | Integer | Nombre d'éléments par page |
| `pagination.totalItems` | Integer | Nombre total d'éléments |
| `pagination.totalPages` | Integer | Nombre total de pages |
| `pagination.hasNextPage` | Boolean | Existe-t-il une page suivante |
| `pagination.hasPreviousPage` | Boolean | Existe-t-il une page précédente |

### ErrorResponseDto
*Format standard des erreurs.*

```json
{
  "error": "QUIZ_LOCKED",
  "message": "Le quiz est verrouillé car le prérequis n'est pas validé",
  "statusCode": 403,
  "timestamp": "2026-01-21T14:30:00Z",
  "path": "/api/sessions/start"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `error` | String | Code d'erreur métier |
| `message` | String | Message explicatif |
| `statusCode` | Integer | Code HTTP |
| `timestamp` | DateTime | Date/heure de l'erreur |
| `path` | String | Endpoint appelé |

---

## 1. Authentification & Utilisateurs

### AuthRequestDto
```json
{
  "email": "user@univ-rennes.fr",
  "password": "password123"
}
```

### RegisterStudentDto
```json
{
  "email": "etudiant@univ-rennes.fr",
  "password": "password123",
  "name": "Jean Dupont",
  "level": "L1"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `email` | String | Email institutionnel |
| `password` | String | Mot de passe (min 8 caractères) |
| `name` | String | Nom complet de l'étudiant |
| `level` | Enum | Niveau universitaire (L1, L2, L3, M1, M2) |
```

### UserResponseDto
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "role": "STUDENT",
  "studentProfile": {
    "level": "L1"
  },
  "teacherProfile": {
    "department": "Anatomie"
  }
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique de l'utilisateur |
| `email` | String | Email de l'utilisateur |
| `role` | Enum | `STUDENT`, `TEACHER`, `ADMIN` |
| `studentProfile` | Object | Présent uniquement si `role = STUDENT` |
| `teacherProfile` | Object | Présent uniquement si `role = TEACHER` |

---

## 2. Gestion des Cours (Classroom)

### ClassroomDto
*Le niveau racine de la structure pédagogique (Classroom contient les Modules).*

```json
{
  "id": "uuid",
  "name": "Anatomie L1 - 2026",
  "level": "L1",
  "code": "ABC123",
  "responsibleProfessor": {
    "id": "uuid",
    "name": "Dr. House",
    "email": "house@univ.fr"
  },
  "otherTeachers": [
    {
      "id": "uuid",
      "name": "Dr. Wilson",
      "email": "wilson@univ.fr"
    }
  ],
  "studentCount": 150
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique du cours |
| `name` | String | Nom du cours |
| `level` | String | Niveau universitaire (L1, L2, L3, M1, M2) |
| `code` | String | Code d'inscription pour les étudiants |
| `responsibleProfessor` | Object | Professeur responsable (seul à avoir tous les droits) |
| `otherTeachers` | Array | Autres enseignants du cours (peuvent gérer les quiz) |
| `studentCount` | Integer | Nombre d'étudiants inscrits (calculé dynamiquement) |

### UserSummaryDto
*Résumé d'un utilisateur (pour listes).*

```json
{
  "id": "uuid",
  "email": "user@univ.fr",
  "name": "Jean Dupont",
  "role": "STUDENT"
}
```

### ClassroomMembersDto
*Liste complète des membres d'un cours.*

```json
{
  "classroomId": "uuid",
  "responsibleProfessor": {
    "id": "uuid",
    "email": "house@univ.fr",
    "name": "Dr. House",
    "role": "TEACHER"
  },
  "otherTeachers": [
    {
      "id": "uuid",
      "email": "wilson@univ.fr",
      "name": "Dr. Wilson",
      "role": "TEACHER"
    }
  ],
  "students": [
    {
      "id": "uuid",
      "email": "etudiant@univ.fr",
      "name": "Marie Martin",
      "role": "STUDENT"
    }
  ],
  "totalTeachers": 2,
  "totalStudents": 150
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `classroomId` | UUID | Identifiant du cours |
| `responsibleProfessor` | UserSummaryDto | Professeur responsable |
| `otherTeachers` | Array | Liste des autres enseignants |
| `students` | Array | Liste des étudiants (paginée) |
| `totalTeachers` | Integer | Nombre total d'enseignants |
| `totalStudents` | Integer | Nombre total d'étudiants |

### AddTeacherToClassroomDto
*Pour ajouter un enseignant à un cours.*

```json
{
  "email": "professor@univ.fr"
}
```

### EnrollStudentDto
*Pour inscrire un étudiant à un cours.*

```json
{
  "email": "etudiant@univ.fr"
}
```

### RegenerateCodeResponseDto
*Réponse après régénération du code d'accès.*

```json
{
  "classroomId": "uuid",
  "newCode": "XYZ789",
  "generatedAt": "2026-01-21T10:00:00Z"
}
```

---

## 3. Modules & Quiz

### ModuleDto
*Les modules sont enfants d'une Classroom.*

```json
{
  "id": "uuid",
  "classroomId": "uuid",
  "name": "Membre Inférieur",
  "category": "Ostéologie",
  "prerequisiteModuleId": "uuid",
  "isLocked": false
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique du module |
| `classroomId` | UUID | Référence au cours parent |
| `name` | String | Nom du module |
| `category` | String | Catégorie du module |
| `prerequisiteModuleId` | UUID | Module prérequis (optionnel) |
| `isLocked` | Boolean | Calculé pour l'étudiant (true si prérequis non complété) |

### QuizDto
```json
{
  "id": "uuid",
  "moduleId": "uuid",
  "title": "Le Pied",
  "prerequisiteQuizId": "uuid",
  "minScoreToUnlockNext": 15,
  "questionCount": 20,
  "isActive": true,
  "isLocked": false,
  "createdBy": {
    "id": "uuid",
    "name": "Dr. House",
    "email": "house@univ.fr"
  },
  "createdAt": "2026-01-15T10:00:00Z"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique du quiz |
| `moduleId` | UUID | Référence au module parent |
| `title` | String | Titre du quiz |
| `prerequisiteQuizId` | UUID | Quiz prérequis (optionnel, débloque ce quiz après réussite) |
| `minScoreToUnlockNext` | Integer | Note minimale pour débloquer le suivant (ex: 15/20) |
| `questionCount` | Integer | Nombre de questions (calculé dynamiquement) |
| `isActive` | Boolean | Quiz activé/désactivé |
| `isLocked` | Boolean | Calculé pour l'étudiant (true si prérequis non validé) |
| `createdBy` | UserSummaryDto | Créateur du quiz |
| `createdAt` | DateTime | Date de création |

---

## 4. Banque de Questions

### QuestionCreateDto (Polymorphique)

DTO unique gérant tous les types via le champ `type`.

```json
{
  "type": "QCM | VRAI_FAUX | MATCHING | IMAGE | TEXT",
  "contentText": "Intitulé de la question",
  "explanation": "Explication pédagogique (affichée à la fin)",
  "mediaId": "uuid",

  "options": [
    { "textChoice": "Réponse A", "isCorrect": true, "displayOrder": 1 },
    { "textChoice": "Réponse B", "isCorrect": false, "displayOrder": 2 }
  ],

  "matchingPairs": [
    { "itemLeft": "Tibia", "itemRight": "Interne" },
    { "itemLeft": "Fibula", "itemRight": "Externe" }
  ],

  "imageZones": [
    {
      "labelName": "Talus",
      "x": 10.5,
      "y": 20.0,
      "radius": 5.0
    }
  ],

  "textConfig": {
    "acceptedAnswer": "Calcanéus",
    "isCaseSensitive": false,
    "ignoreSpellingErrors": true
  }
}
```

#### Types de questions

| Type | Champs requis | Description |
|------|---------------|-------------|
| `QCM` | `options` | Question à choix multiples |
| `VRAI_FAUX` | `options` | Question vrai/faux |
| `MATCHING` | `matchingPairs` | Question d'appariement |
| `IMAGE` | `imageZones` | Zones cliquables sur image |
| `TEXT` | `textConfig` | Saisie textuelle libre |

#### TextConfig (pour type TEXT)

| Champ | Type | Description |
|-------|------|-------------|
| `acceptedAnswer` | String | Réponse attendue |
| `isCaseSensitive` | Boolean | Sensible à la casse |
| `ignoreSpellingErrors` | Boolean | Tolérance orthographique (Levenshtein) |

---

## 5. Gameplay & Session

### GameSessionStartDto
*Réponse au démarrage de session. Les réponses correctes ne sont pas incluses.*

```json
{
  "sessionId": "uuid",
  "questions": [
    {
      "id": "uuid",
      "type": "TEXT",
      "contentText": "Nommez cet os.",
      "mediaUrl": "http://..."
    },
    {
      "id": "uuid",
      "type": "QCM",
      "contentText": "...",
      "options": [
        { "id": "opt1", "textChoice": "A" },
        { "id": "opt2", "textChoice": "B" }
      ]
    }
  ]
}
```

### SubmitAnswerDto
*Envoi d'une réponse. Remplir UN seul champ selon le type.*

```json
{
  "questionId": "uuid",
  "type": "TEXT",

  "selectedOptionId": "uuid",
  "clickedCoordinates": { "x": 12, "y": 34 },
  "textResponse": "calcanéum",
  "matchedPairs": [
    { "leftId": "uuid_left", "rightId": "uuid_right" }
  ]
}
```

| Champ | Type | Utilisé pour |
|-------|------|--------------|
| `selectedOptionId` | UUID | QCM / VRAI_FAUX |
| `clickedCoordinates` | Object | IMAGE |
| `textResponse` | String | TEXT |
| `matchedPairs` | Array | MATCHING |

### AnswerResultDto
*Réponse immédiate du serveur (sans correction pour éviter la triche).*

```json
{
  "questionId": "uuid",
  "isCorrect": false,
  "message": "Réponse enregistrée."
}
```

### SessionResultDto
*Résultat après clôture de la session quiz.*

```json
{
  "sessionId": "uuid",
  "quizId": "uuid",
  "totalScore": 14,
  "maxScore": 20,
  "passed": true,
  "completedAt": "2026-01-21T14:30:00Z"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `sessionId` | UUID | Identifiant de la session |
| `quizId` | UUID | Identifiant du quiz |
| `totalScore` | Integer | Score obtenu |
| `maxScore` | Integer | Score maximum possible |
| `passed` | Boolean | Quiz réussi (score >= minScoreToUnlockNext) |
| `completedAt` | DateTime | Date de complétion |

**Note** : Si `passed = true`, une entrée est automatiquement créée dans `CompletedQuiz` (si première réussite) et les questions sont ajoutées en boîte Leitner 1.

---

## 6. Progression & Statistiques (Système Leitner)

### LeitnerBoxesStatusDto
*Visualisation de la distribution des questions dans les 5 boîtes de Leitner d'un cours.*

```json
{
  "classroomId": "uuid",
  "classroomName": "Anatomie L1 - 2026",
  "totalQuestions": 150,
  "boxes": [
    {
      "level": 1,
      "questionCount": 45,
      "percentage": 30.0,
      "selectionWeight": 50
    },
    {
      "level": 2,
      "questionCount": 40,
      "percentage": 26.7,
      "selectionWeight": 25
    },
    {
      "level": 3,
      "questionCount": 35,
      "percentage": 23.3,
      "selectionWeight": 15
    },
    {
      "level": 4,
      "questionCount": 20,
      "percentage": 13.3,
      "selectionWeight": 7
    },
    {
      "level": 5,
      "questionCount": 10,
      "percentage": 6.7,
      "selectionWeight": 3
    }
  ],
  "lastReviewedAt": "2026-01-20T14:30:00Z"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `classroomId` | UUID | Identifiant du cours |
| `classroomName` | String | Nom du cours |
| `totalQuestions` | Integer | Nombre total de questions débloquées |
| `boxes` | Array | Distribution des questions dans les 5 boîtes |
| `boxes[].level` | Integer | Niveau de la boîte (1 à 5) |
| `boxes[].questionCount` | Integer | Nombre de questions dans cette boîte |
| `boxes[].percentage` | Float | Pourcentage du total |
| `boxes[].selectionWeight` | Integer | Poids pour la sélection aléatoire (%) |
| `lastReviewedAt` | DateTime | Date de la dernière session de révision |

### LeitnerSessionStartRequestDto
*Paramètres pour démarrer une session de révision Leitner.*

```json
{
  "questionCount": 10
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `questionCount` | Integer | Nombre de questions (5, 10, 15 ou 20) |

**Note** : Le `classroomId` est passé dans l'URL (`/api/classrooms/{cid}/leitner/start`).

### LeitnerSessionStartResponseDto
*Questions sélectionnées pour la session de révision.*

```json
{
  "sessionId": "uuid",
  "classroomId": "uuid",
  "questions": [
    {
      "id": "uuid",
      "type": "QCM",
      "contentText": "Question ici...",
      "mediaUrl": "http://...",
      "currentBox": 2,
      "options": [
        { "id": "opt1", "textChoice": "A" },
        { "id": "opt2", "textChoice": "B" }
      ]
    }
  ],
  "selectionDistribution": {
    "box1": 5,
    "box2": 3,
    "box3": 2,
    "box4": 0,
    "box5": 0
  }
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `sessionId` | UUID | Identifiant de la session |
| `classroomId` | UUID | Cours concerné |
| `questions` | Array | Questions sélectionnées (sans réponses) |
| `questions[].currentBox` | Integer | Boîte actuelle de la question (1-5) |
| `selectionDistribution` | Object | Répartition des questions sélectionnées par boîte |

### LeitnerSessionResultDto
*Résultat d'une session de révision Leitner (minimal).*

```json
{
  "sessionId": "uuid",
  "classroomId": "uuid",
  "totalQuestions": 10,
  "correctAnswers": 7,
  "wrongAnswers": 3,
  "accuracyRate": 0.70,
  "boxMovements": {
    "promoted": 7,
    "demoted": 3
  },
  "newBoxDistribution": {
    "box1": 48,
    "box2": 37,
    "box3": 36,
    "box4": 19,
    "box5": 10
  }
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `sessionId` | UUID | Identifiant de la session |
| `classroomId` | UUID | Cours concerné |
| `totalQuestions` | Integer | Nombre total de questions |
| `correctAnswers` | Integer | Nombre de bonnes réponses |
| `wrongAnswers` | Integer | Nombre de mauvaises réponses |
| `accuracyRate` | Float | Taux de réussite (0.0 à 1.0) |
| `boxMovements.promoted` | Integer | Questions montées d'une boîte |
| `boxMovements.demoted` | Integer | Questions redescendues en boîte 1 |
| `newBoxDistribution` | Object | Nouvelle répartition après la session |

### LeitnerSessionReviewDto
*Correction détaillée d'une session de révision Leitner.*

```json
{
  "sessionId": "uuid",
  "classroomId": "uuid",
  "answers": [
    {
      "questionId": "uuid",
      "questionText": "Nommez cet os.",
      "isCorrect": true,
      "previousBox": 2,
      "newBox": 3,
      "correctAnswer": "Calcanéus",
      "explanation": "Le calcanéus est l'os du talon."
    }
  ],
  "summary": {
    "totalQuestions": 10,
    "correctAnswers": 7,
    "accuracyRate": 0.70
  }
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `sessionId` | UUID | Identifiant de la session |
| `classroomId` | UUID | Cours concerné |
| `answers` | Array | Détail de chaque question révisée |
| `answers[].questionId` | UUID | Identifiant de la question |
| `answers[].questionText` | String | Texte de la question |
| `answers[].isCorrect` | Boolean | Réponse correcte ou non |
| `answers[].previousBox` | Integer | Boîte avant la révision (1-5) |
| `answers[].newBox` | Integer | Boîte après la révision (1-5) |
| `answers[].correctAnswer` | String/Object | Réponse attendue (format selon type : String pour TEXT, Array pour QCM/MATCHING) |
| `answers[].explanation` | String | Explication pédagogique |
| `summary` | Object | Résumé de la session |

### CompletedModuleDto
*Simple marqueur de module complété.*

```json
{
  "studentId": "uuid",
  "moduleId": "uuid",
  "completedAt": "2026-01-20T16:00:00Z"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `studentId` | UUID | Identifiant de l'étudiant |
| `moduleId` | UUID | Identifiant du module complété |
| `completedAt` | DateTime | Date de complétion (quand le dernier quiz requis a été réussi) |

**Note** : Un module est considéré "complété" quand tous les quiz avec `minScoreToUnlockNext > 0` sont dans `CompletedQuiz`.

### CompletedQuizDto
*Simple marqueur de quiz complété (table de référence).*

```json
{
  "studentId": "uuid",
  "quizId": "uuid",
  "completedAt": "2026-01-20T14:30:00Z"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `studentId` | UUID | Identifiant de l'étudiant |
| `quizId` | UUID | Identifiant du quiz complété |
| `completedAt` | DateTime | Date de première complétion réussie |

**Note** : Un quiz est considéré "complété" quand l'étudiant obtient un score >= `minScoreToUnlockNext`. Cette table permet de vérifier rapidement les déblocages sans parcourir toutes les sessions.

### QuizProgressDto (Calculé Dynamiquement)
*Statistiques de progression sur un quiz - calculées à la volée depuis QuizSession et CompletedQuiz.*

```json
{
  "quizId": "uuid",
  "quizTitle": "Le Pied",
  "isCompleted": true,
  "bestScore": 17,
  "attemptsCount": 3,
  "firstAttemptAt": "2026-01-15T10:00:00Z",
  "lastAttemptAt": "2026-01-20T14:30:00Z",
  "completedAt": "2026-01-18T12:00:00Z"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `quizId` | UUID | Identifiant du quiz |
| `quizTitle` | String | Titre du quiz |
| `isCompleted` | Boolean | Quiz complété (existe dans CompletedQuiz) |
| `bestScore` | Integer | Meilleur score (MAX(totalScore) depuis QuizSession) |
| `attemptsCount` | Integer | Nombre de tentatives (COUNT depuis QuizSession) |
| `firstAttemptAt` | DateTime | Première tentative (MIN(completedAt) depuis QuizSession) |
| `lastAttemptAt` | DateTime | Dernière tentative (MAX(completedAt) depuis QuizSession) |
| `completedAt` | DateTime | Date de complétion (depuis CompletedQuiz, null si non complété) |

### ModuleProgressDto (Calculé Dynamiquement)
*Statistiques de progression sur un module - `isCompleted` depuis CompletedModule, reste calculé.*

```json
{
  "moduleId": "uuid",
  "moduleName": "Membre Inférieur",
  "isCompleted": true,
  "completedAt": "2026-01-20T16:00:00Z",
  "completedQuizzesCount": 8,
  "totalQuizzesCount": 10,
  "completionRate": 0.80,
  "quizzes": [
    {
      "quizId": "uuid",
      "quizTitle": "Le Pied",
      "isCompleted": true,
      "bestScore": 17
    }
  ]
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `moduleId` | UUID | Identifiant du module |
| `moduleName` | String | Nom du module |
| `isCompleted` | Boolean | Existe dans CompletedModule |
| `completedAt` | DateTime | Date depuis CompletedModule (null si non complété) |
| `completedQuizzesCount` | Integer | COUNT depuis CompletedQuiz |
| `totalQuizzesCount` | Integer | COUNT des quiz du module |
| `completionRate` | Float | Calculé (0.0 à 1.0) |
| `quizzes` | Array | Détail par quiz (optionnel) |

### StudentStatsDto
*Statistiques personnelles d'un étudiant (calculées dynamiquement).*

```json
{
  "studentId": "uuid",
  "totalCompletedQuizzes": 45,
  "averageScore": 16.2,
  "leitnerMastery": 0.62,
  "classroomsProgress": [
    {
      "classroomId": "uuid",
      "classroomName": "Anatomie L1",
      "completedQuizzes": 15,
      "totalQuizzes": 20,
      "averageScore": 16.5,
      "leitnerMastery": 0.45
    }
  ]
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `studentId` | UUID | Identifiant de l'étudiant |
| `totalCompletedQuizzes` | Integer | COUNT depuis CompletedQuiz |
| `averageScore` | Float | AVG(totalScore) depuis QuizSession |
| `leitnerMastery` | Float | % de questions en boîtes 4-5 |
| `classroomsProgress` | Array | Progression par cours |

**Note** : Toutes les données sont calculées dynamiquement, aucun point n'est stocké.
```

### ProfessorDashboardDto
*Tableau de bord professeur pour un cours.*

```json
{
  "classroomId": "uuid",
  "modulesStats": [
    {
      "moduleName": "Jambe",
      "averageScore": 14.5,
      "completionRate": 0.80,
      "alertStudents": ["Jean Dupont"],
      "hardestQuestions": [
        { "questionText": "Nerf fibulaire...", "failureRate": 0.85 }
      ]
    }
  ],
  "leitnerStats": {
    "totalActiveStudents": 145,
    "averageMastery": 0.62,
    "studentsInBox5": 23
  }
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `classroomId` | UUID | Identifiant du cours |
| `modulesStats` | Array | Statistiques par module |
| `modulesStats[].moduleName` | String | Nom du module |
| `modulesStats[].averageScore` | Float | Score moyen des étudiants |
| `modulesStats[].completionRate` | Float | Taux de complétion (0.0 à 1.0) |
| `modulesStats[].alertStudents` | Array | Étudiants en difficulté |
| `modulesStats[].hardestQuestions` | Array | Questions avec fort taux d'échec |
| `leitnerStats` | Object | Statistiques sur l'utilisation du système Leitner |
| `leitnerStats.averageMastery` | Float | Niveau moyen de maîtrise (% questions en boîtes 4-5) |

### LeaderboardEntryDto
*Entrée du classement d'un cours.*

```json
{
  "rank": 1,
  "studentId": "uuid",
  "studentName": "Marie Martin",
  "completedQuizzes": 18,
  "averageScore": 17.5,
  "leitnerMastery": 0.75
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `rank` | Integer | Position dans le classement |
| `studentId` | UUID | Identifiant de l'étudiant |
| `studentName` | String | Nom de l'étudiant |
| `completedQuizzes` | Integer | Nombre de quiz complétés |
| `averageScore` | Float | Score moyen (calculé depuis QuizSession) |
| `leitnerMastery` | Float | % de questions en boîtes 4-5 |

**Note** : Le classement est trié par `completedQuizzes` desc, puis `averageScore` desc.

### MediaDto
*Informations sur un fichier média uploadé.*

```json
{
  "id": "uuid",
  "url": "https://storage.example.com/media/abc123.jpg",
  "filename": "anatomie-pied.jpg",
  "mimeType": "image/jpeg",
  "uploadedBy": {
    "id": "uuid",
    "name": "Dr. House"
  },
  "uploadedAt": "2026-01-15T10:00:00Z",
  "isUsed": true
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant du média |
| `url` | String | URL d'accès au fichier |
| `filename` | String | Nom original du fichier |
| `mimeType` | String | Type MIME (image/jpeg, image/png, etc.) |
| `uploadedBy` | Object | Professeur qui a uploadé |
| `uploadedAt` | DateTime | Date d'upload |
| `isUsed` | Boolean | Média utilisé par au moins une question |
