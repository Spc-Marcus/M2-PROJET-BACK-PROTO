# Endpoints API - Duobingo

Ce document recense l'ensemble des endpoints de l'API Duobingo.

---

## 1. Authentification & Utilisateurs

*Sources : US 27, 28, 38, 39, 54*

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| `POST` | `/api/auth/login` | Connexion (retourne un JWT) | Public |
| `POST` | `/api/auth/register` | Inscription autonome (Étudiant uniquement) | Public |
| `GET` | `/api/users/me` | Récupérer le profil connecté (Role, Niveau) | Authentifié |
| `PATCH` | `/api/users/me` | Modifier son profil (Email, Avatar) | Authentifié |
| `POST` | `/api/admin/users` | Créer un compte Professeur ou Admin | Admin |

### Détails

#### POST `/api/auth/login`
- **Body** : `AuthRequestDto`
- **Response** : JWT Token
- **Accès** : Public

#### POST `/api/auth/register`
- **Body** : `RegisterStudentDto`
- **Response** : `UserResponseDto`
- **Accès** : Public

#### GET `/api/users/me`
- **Response** : `UserResponseDto`
- **Accès** : Authentifié

#### PATCH `/api/users/me`
- **Body** : Champs à modifier (email, avatar)
- **Response** : `UserResponseDto`
- **Accès** : Authentifié

#### POST `/api/admin/users`
- **Body** : Données du nouvel utilisateur
- **Response** : `UserResponseDto`
- **Accès** : Admin

---

## 2. Gestion des Cours (Classroom)

*Le niveau racine de la structure pédagogique. Gestion hiérarchique : Professeur Responsable > Autres Enseignants > Étudiants.*

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| `GET` | `/api/classrooms` | Liste des cours (Inscrits pour élève, Gérés pour prof) | Tous |
| `POST` | `/api/classrooms` | Créer un espace de cours (devient prof responsable) | Prof |
| `GET` | `/api/classrooms/{id}` | Détails d'un cours | Membres du cours |
| `PATCH` | `/api/classrooms/{id}` | Modifier les infos du cours (nom, niveau) | Prof Responsable |
| `DELETE` | `/api/classrooms/{id}` | Supprimer un cours complet | Prof Responsable |
| `GET` | `/api/classrooms/{id}/members` | Lister tous les membres (profs + étudiants) | Prof du cours |
| `POST` | `/api/classrooms/{id}/teachers` | Ajouter un enseignant au cours | Prof Responsable |
| `DELETE` | `/api/classrooms/{id}/teachers/{teacherId}` | Retirer un enseignant du cours | Prof Responsable |
| `POST` | `/api/classrooms/{id}/enroll` | Inscrire un étudiant (via email) | Prof Responsable |
| `DELETE` | `/api/classrooms/{id}/students/{studentId}` | Retirer un étudiant du cours | Prof Responsable |
| `POST` | `/api/classrooms/join` | Rejoindre un cours (via Code seul) | Étudiant |
| `POST` | `/api/classrooms/{id}/join` | Rejoindre un cours spécifique (via Code + ID) | Étudiant |
| `POST` | `/api/classrooms/{id}/regenerate-code` | Régénérer le code d'accès | Prof Responsable |

### Détails

#### GET `/api/classrooms`
- **Response** : Liste de `ClassroomDto`
- **Accès** : Tous (filtrés selon le rôle)

#### POST `/api/classrooms`
- **Body** : `{ "name": "Anatomie L1", "level": "L1" }`
- **Response** : `ClassroomDto`
- **Note** : Le créateur devient automatiquement le professeur responsable. Un code d'accès est généré automatiquement.
- **Accès** : Prof

#### GET `/api/classrooms/{id}`
- **Path Params** : `id` (UUID)
- **Response** : `ClassroomDto`
- **Accès** : Membres du cours

#### PATCH `/api/classrooms/{id}`
- **Path Params** : `id` (UUID)
- **Body** : `{ "name": "Nouveau nom", "level": "L2" }`
- **Response** : `ClassroomDto`
- **Accès** : Prof Responsable uniquement

#### POST `/api/classrooms/{id}/teachers`
- **Path Params** : `id` (UUID)
- **Body** : `AddTeacherToClassroomDto`
- **Response** : `ClassroomDto`
- **Note** : Ajoute un enseignant au cours (peut gérer quiz mais pas modules)
- **Accès** : Prof Responsable uniquement

#### DELETE `/api/classrooms/{id}/teachers/{teacherId}`
- **Path Params** : `id` (UUID), `teacherId` (UUID)
- **Response** : 204 No Content
- **Accès** : Prof Responsable uniquement

#### POST `/api/classrooms/{id}/enroll`
- **Path Params** : `id` (UUID)
- **Body** : `EnrollStudentDto`
- **Response** : 200 OK
- **Accès** : Prof Responsable uniquement

#### DELETE `/api/classrooms/{id}/students/{studentId}`
- **Path Params** : `id` (UUID), `studentId` (UUID)
- **Response** : 204 No Content
- **Accès** : Prof Responsable uniquement

#### POST `/api/classrooms/join`
- **Body** : `{ "code": "ABC123" }`
- **Response** : `ClassroomDto`
- **Note** : Cherche le cours par code uniquement et inscrit l'étudiant
- **Accès** : Étudiant

#### POST `/api/classrooms/{id}/join`
- **Path Params** : `id` (UUID)
- **Body** : `{ "code": "ABC123" }`
- **Response** : `ClassroomDto`
- **Note** : Vérifie que le code correspond au cours spécifié avant d'inscrire
- **Accès** : Étudiant

#### DELETE `/api/classrooms/{id}`
- **Path Params** : `id` (UUID)
- **Response** : 204 No Content
- **Accès** : Prof Responsable uniquement

#### GET `/api/classrooms/{id}/members`
- **Path Params** : `id` (UUID)
- **Query Params** : `?page=1&limit=50` (optionnel, pour paginer les étudiants)
- **Response** : `ClassroomMembersDto`
- **Accès** : Prof du cours

#### POST `/api/classrooms/{id}/regenerate-code`
- **Path Params** : `id` (UUID)
- **Response** : `RegenerateCodeResponseDto`
- **Note** : L'ancien code est immédiatement invalidé
- **Accès** : Prof Responsable uniquement

---

## 3. Gestion des Modules

*Les modules sont enfants d'une Classroom. Seul le professeur responsable peut créer/modifier/supprimer des modules.*

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| `GET` | `/api/classrooms/{cid}/modules` | Liste des modules d'un cours | Tous |
| `POST` | `/api/classrooms/{cid}/modules` | Ajouter un module au cours | Prof Responsable |
| `PUT` | `/api/modules/{id}` | Modifier un module (Nom, Catégorie) | Prof Responsable |
| `DELETE` | `/api/modules/{id}` | Supprimer un module | Prof Responsable |

### Détails

#### GET `/api/classrooms/{cid}/modules`
- **Path Params** : `cid` (UUID du cours)
- **Query Params** : `?page=1&limit=20` (optionnel)
- **Response** : Liste de `ModuleDto`
- **Accès** : Tous

#### POST `/api/classrooms/{cid}/modules`
- **Path Params** : `cid` (UUID du cours)
- **Body** : `ModuleDto`
- **Response** : `ModuleDto`
- **Note** : Seul le professeur responsable du cours peut créer des modules
- **Accès** : Prof Responsable uniquement

#### PUT `/api/modules/{id}`
- **Path Params** : `id` (UUID)
- **Body** : `ModuleDto`
- **Response** : `ModuleDto`
- **Accès** : Prof Responsable uniquement

#### DELETE `/api/modules/{id}`
- **Path Params** : `id` (UUID)
- **Response** : 204 No Content
- **Accès** : Prof Responsable uniquement

---

## 4. Gestion des Quiz

*Création et configuration des examens. Tous les enseignants du cours peuvent gérer les quiz.*

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| `GET` | `/api/modules/{mid}/quizzes` | Liste des quiz d'un module | Tous |
| `POST` | `/api/modules/{mid}/quizzes` | Créer un quiz | Prof du cours |
| `PUT` | `/api/quizzes/{id}` | Config (Actif, Seuil déblocage) | Prof du cours |
| `DELETE` | `/api/quizzes/{id}` | Supprimer un quiz | Prof du cours |
| `POST` | `/api/quizzes/import` | Import PowerPoint/Excel | Prof du cours |

### Détails

#### GET `/api/modules/{mid}/quizzes`
- **Path Params** : `mid` (UUID du module)
- **Query Params** : `?page=1&limit=20` (optionnel)
- **Response** : Liste de `QuizDto`
- **Accès** : Tous

#### POST `/api/modules/{mid}/quizzes`
- **Path Params** : `mid` (UUID du module)
- **Body** : `QuizDto`
- **Response** : `QuizDto`
- **Note** : Accessible au prof responsable ET aux autres enseignants du cours
- **Accès** : Prof du cours

#### PUT `/api/quizzes/{id}`
- **Path Params** : `id` (UUID)
- **Body** : Champs à modifier
- **Response** : `QuizDto`
- **Accès** : Prof du cours

#### DELETE `/api/quizzes/{id}`
- **Path Params** : `id` (UUID)
- **Response** : 204 No Content
- **Accès** : Prof du cours

#### POST `/api/quizzes/import`
- **Body** : Fichier PowerPoint/Excel (multipart/form-data)
- **Response** : `QuizDto`
- **Accès** : Prof du cours

---

## 5. Banque de Questions

*Sources : US 7-12, 18, 26, 27*

*Gestion polymorphique (QCM, Image, Texte, Appariement). Tous les enseignants du cours peuvent gérer les questions.*

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| `GET` | `/api/quizzes/{quizId}/questions` | Liste complète des questions (avec réponses) | Prof du cours |
| `POST` | `/api/quizzes/{quizId}/questions` | Ajouter une question au quiz | Prof du cours |
| `PATCH` | `/api/questions/{questionId}` | Modifier une question complète | Prof du cours |
| `DELETE` | `/api/questions/{questionId}` | Supprimer une question | Prof du cours |
| `POST` | `/api/media` | Uploader une image (retourne l'URL) | Prof du cours |

### Détails

#### GET `/api/quizzes/{quizId}/questions`
- **Path Params** : `quizId` (UUID)
- **Query Params** : `?page=1&limit=50` (optionnel)
- **Response** : `PaginatedResponseDto<QuestionCreateDto>`
- **Accès** : Prof du cours uniquement (inclut les réponses)

#### POST `/api/quizzes/{quizId}/questions`
- **Path Params** : `quizId` (UUID)
- **Body** : `QuestionCreateDto`
- **Response** : Question créée
- **Accès** : Prof du cours

#### PATCH `/api/questions/{questionId}`
- **Path Params** : `questionId` (UUID)
- **Body** : `QuestionCreateDto`
- **Response** : Question modifiée
- **Accès** : Prof du cours

#### DELETE `/api/questions/{questionId}`
- **Path Params** : `questionId` (UUID)
- **Response** : 204 No Content
- **Accès** : Prof du cours

#### POST `/api/media`
- **Body** : Fichier image (multipart/form-data)
- **Response** : `{ "mediaId": "uuid", "url": "http://..." }`
- **Accès** : Prof du cours

#### GET `/api/media`
- **Query Params** : `?page=1&limit=50` (optionnel)
- **Response** : `PaginatedResponseDto<MediaDto>` - Liste des médias uploadés
- **Accès** : Prof

#### DELETE `/api/media/{mediaId}`
- **Path Params** : `mediaId` (UUID)
- **Response** : 204 No Content
- **Note** : Supprime le fichier physique et l'entrée en base. Échoue si le média est utilisé par une question.
- **Accès** : Prof (propriétaire du média uniquement)

#### GET `/api/media/orphaned`
- **Response** : Liste des médias non utilisés par aucune question
- **Note** : Permet de nettoyer le stockage
- **Accès** : Admin

---

## 6. Gameplay & Session (Étudiant)

*Sources : US 2, 5, 6, 8, 13*

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| `POST` | `/api/sessions/start` | Démarre une session (questions **sans** réponses) | Étudiant |
| `POST` | `/api/sessions/{sessionId}/submit-answer` | Envoie une réponse (retourne succès/échec uniquement) | Étudiant |
| `POST` | `/api/sessions/{sessionId}/finish` | Clôture la session, calcule le score final | Étudiant |
| `GET` | `/api/sessions/{sessionId}/review` | Récupère le détail complet (Corrections) après fin | Étudiant |

### Détails

#### POST `/api/sessions/start`
- **Body** : `{ "quizId": "uuid" }`
- **Response** : `GameSessionStartDto`
- **Note** : Les réponses correctes ne sont **pas** incluses (anti-triche)
- **Accès** : Étudiant

#### POST `/api/sessions/{sessionId}/submit-answer`
- **Path Params** : `sessionId` (UUID)
- **Body** : `SubmitAnswerDto`
- **Response** : `AnswerResultDto`
- **Note** : Retourne uniquement `isCorrect`, pas la correction
- **Accès** : Étudiant

#### POST `/api/sessions/{sessionId}/finish`
- **Path Params** : `sessionId` (UUID)
- **Response** : `SessionResultDto`
- **Accès** : Étudiant

#### GET `/api/sessions/{sessionId}/review`
- **Path Params** : `sessionId` (UUID)
- **Response** : Détail complet avec corrections
- **Note** : Disponible uniquement après `/finish`
- **Accès** : Étudiant

---

## 7. Progression & Statistiques

*Sources : US 5, 20, 21, 63*

### Système Leitner (Révision Espacée)

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| `GET` | `/api/classrooms/{cid}/leitner/status` | Voir la distribution des questions dans les 5 boîtes | Étudiant |
| `POST` | `/api/classrooms/{cid}/leitner/start` | Démarrer une session de révision (5/10/15/20 questions) | Étudiant |
| `POST` | `/api/leitner/sessions/{sid}/submit-answer` | Soumettre une réponse pendant la révision | Étudiant |
| `POST` | `/api/leitner/sessions/{sid}/finish` | Terminer la session et mettre à jour les boîtes | Étudiant |
| `GET` | `/api/leitner/sessions/{sid}/review` | Voir la correction complète après la session | Étudiant |

### Statistiques

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| `GET` | `/api/stats/student` | Stats globales (quiz complétés, score moyen, maîtrise Leitner) | Étudiant |
| `GET` | `/api/stats/leaderboard/{cid}` | Classement des étudiants d'un cours | Étudiant |
| `GET` | `/api/stats/dashboard/{cid}` | Tableau de bord prof (Difficultés, Stats Leitner) | Prof du cours |

### Progression Étudiant

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| `GET` | `/api/progress/modules/{moduleId}` | Progression de l'étudiant sur un module | Étudiant |
| `GET` | `/api/progress/quizzes/{quizId}` | Progression de l'étudiant sur un quiz | Étudiant |
| `GET` | `/api/progress/classroom/{cid}` | Progression globale dans un cours (tous modules) | Étudiant |
| `GET` | `/api/progress/classroom/{cid}/student/{sid}` | Progression d'un étudiant spécifique (vue prof) | Prof du cours |

### Détails - Système Leitner

#### GET `/api/classrooms/{cid}/leitner/status`
- **Path Params** : `cid` (UUID du cours)
- **Response** : `LeitnerBoxesStatusDto`
- **Description** : Affiche la distribution des questions débloquées dans les 5 boîtes de Leitner. Les questions sont automatiquement ajoutées à la boîte 1 lors du déblocage de quiz/modules.
- **Accès** : Étudiant

**Règles de sélection dynamique** :
- Boîte 1 : 50% de probabilité
- Boîte 2 : 25% de probabilité
- Boîte 3 : 15% de probabilité
- Boîte 4 : 7% de probabilité
- Boîte 5 : 3% de probabilité

#### POST `/api/classrooms/{cid}/leitner/start`
- **Path Params** : `cid` (UUID du cours)
- **Body** : `LeitnerSessionStartRequestDto`
```json
{
  "questionCount": 10  // Valeurs acceptées : 5, 10, 15, 20
}
```
- **Response** : `LeitnerSessionStartResponseDto`
- **Description** : Démarre une session de révision avec X questions sélectionnées aléatoirement selon les pourcentages par boîte. Aucune réponse correcte n'est envoyée.
- **Accès** : Étudiant

#### POST `/api/leitner/sessions/{sid}/submit-answer`
- **Path Params** : `sid` (UUID de la session)
- **Body** : `SubmitAnswerDto` (même format que les quiz normaux)
- **Response** : `AnswerResultDto` (juste/faux uniquement)
- **Description** : Soumet une réponse. Le serveur enregistre le résultat mais ne renvoie pas la correction.
- **Accès** : Étudiant

#### POST `/api/leitner/sessions/{sid}/finish`
- **Path Params** : `sid` (UUID de la session)
- **Response** : `LeitnerSessionResultDto`
- **Description** : Clôture la session et met à jour les boîtes selon les règles :
  - **Bonne réponse** : Question monte d'une boîte (+1, max 5)
  - **Mauvaise réponse** : Question retourne en boîte 1
- **Note** : Les réponses sont stockées dans `LeitnerSessionAnswer` pour permettre la correction détaillée via `/review`.
- **Accès** : Étudiant

#### GET `/api/leitner/sessions/{sid}/review`
- **Path Params** : `sid` (UUID de la session)
- **Response** : `LeitnerSessionReviewDto`
- **Description** : Disponible uniquement après `/finish`. Retourne le détail de chaque question révisée avec la correction, l'explication, et les mouvements de boîtes.
- **Accès** : Étudiant

### Détails - Statistiques

#### GET `/api/stats/student`
- **Response** : `StudentStatsDto`
- **Description** : Statistiques personnelles (quiz complétés, score moyen, progression par cours, maîtrise Leitner)
- **Accès** : Étudiant

#### GET `/api/stats/leaderboard/{cid}`
- **Path Params** : `cid` (UUID du cours)
- **Query Params** : `?page=1&limit=50` (optionnel)
- **Response** : `PaginatedResponseDto<LeaderboardEntryDto>`
- **Description** : Classement des étudiants trié par nombre de quiz complétés puis score moyen
- **Accès** : Étudiant

#### GET `/api/stats/dashboard/{cid}`
- **Path Params** : `cid` (UUID du cours)
- **Response** : `ProfessorDashboardDto`
- **Description** : Tableau de bord avec stats par module + stats Leitner (maîtrise moyenne, étudiants actifs)
- **Accès** : Prof du cours

### Détails - Progression Étudiant

#### GET `/api/progress/modules/{moduleId}`
- **Path Params** : `moduleId` (UUID du module)
- **Response** : `ModuleProgressDto`
- **Description** : Calcule dynamiquement la progression depuis CompletedQuiz et QuizSession
- **Accès** : Étudiant

#### GET `/api/progress/quizzes/{quizId}`
- **Path Params** : `quizId` (UUID du quiz)
- **Response** : `QuizProgressDto`
- **Description** : Calcule les statistiques (meilleur score, tentatives) depuis QuizSession
- **Accès** : Étudiant

#### GET `/api/progress/classroom/{cid}`
- **Path Params** : `cid` (UUID du cours)
- **Response** : `Array<ModuleProgressDto>`
- **Description** : Progression sur tous les modules du cours (calculé dynamiquement)
- **Accès** : Étudiant

#### GET `/api/progress/classroom/{cid}/student/{sid}`
- **Path Params** : `cid` (UUID du cours), `sid` (UUID de l'étudiant)
- **Response** : `Array<ModuleProgressDto>`
- **Description** : Vue professeur de la progression d'un étudiant
- **Accès** : Prof du cours

---

## Récapitulatif des accès

| Niveau d'accès | Description |
|----------------|-------------|
| **Public** | Aucune authentification requise |
| **Authentifié** | Token JWT valide requis |
| **Étudiant** | Role = STUDENT |
| **Prof** | Role = TEACHER |
| **Prof Responsable** | Professeur créateur du cours (tous les droits) |
| **Prof du cours** | Professeur responsable OU autre enseignant du cours |
| **Admin** | Role = ADMIN |
| **Prof/Admin** | Role = TEACHER ou ADMIN |
| **Tous** | Authentifié (tout rôle) |

### Hiérarchie des permissions dans un Classroom

**Professeur Responsable (Créateur du cours)** :
- ✅ Créer/Modifier/Supprimer le cours
- ✅ Ajouter/Retirer des enseignants
- ✅ Ajouter/Retirer des étudiants
- ✅ Créer/Modifier/Supprimer des modules
- ✅ Créer/Modifier/Supprimer des quiz et questions

**Autres Enseignants du cours** :
- ❌ Modifier les infos du cours
- ❌ Gérer les inscriptions (profs/étudiants)
- ❌ Gérer les modules
- ✅ Créer/Modifier/Supprimer des quiz et questions

**Étudiants** :
- ✅ Rejoindre un cours (avec code)
- ✅ Consulter modules et quiz
- ✅ Jouer aux quiz
- ✅ Réviser via les boîtes Leitner

---

## Règles Métier

### Déblocage des Questions (Leitner)

1. **Quand un étudiant réussit un quiz pour la première fois** (score >= minScoreToUnlockNext), toutes les questions de ce quiz sont ajoutées à sa boîte Leitner 1
2. **Si une question existe déjà** dans une boîte (2, 3, 4 ou 5), elle reste à son niveau actuel
3. **Les questions d'un module/quiz non accessible** ne sont pas dans les boîtes Leitner
4. **Les tentatives échouées** (score < minScoreToUnlockNext) n'ajoutent pas de questions au Leitner

### Progression dans les Modules et Quiz

1. Un **module** avec `prerequisiteModuleId` est **verrouillé** jusqu'à ce que le prérequis soit complété
2. Un **quiz** avec `prerequisiteQuizId` est **verrouillé** jusqu'à ce que le quiz prérequis soit réussi avec un score ≥ `minScoreToUnlockNext`
3. Un module est **"complété"** quand tous ses quiz ont un score ≥ `minScoreToUnlockNext`
4. Un quiz sans `minScoreToUnlockNext` (ou = 0) est considéré comme **optionnel** pour la progression
5. **Ordre de déblocage** : Un quiz peut avoir un prérequis dans le même module ou dans un module différent (déjà complété)
6. **Validation des dépendances circulaires** :
   - Lors de la création/modification d'un module avec `prerequisiteModuleId`, le système vérifie qu'il n'existe pas de cycle (Module A → B → C → A)
   - Lors de la création/modification d'un quiz avec `prerequisiteQuizId`, le système vérifie qu'il n'existe pas de cycle (Quiz A → B → A)
   - Si un cycle est détecté, l'API retourne une erreur `422` avec le code `CIRCULAR_PREREQUISITE`
   - La validation parcourt récursivement la chaîne des prérequis (max 50 niveaux de profondeur)

### Mise à Jour de la Progression

**Automatisation lors de `/api/sessions/{sessionId}/finish`** :

1. **Si le quiz est réussi** (score >= minScoreToUnlockNext) :
   - Créer une entrée dans `CompletedQuiz` (si pas déjà présente)
   - Ajouter toutes les questions du quiz en boîte Leitner 1 (si pas déjà présentes dans des boîtes supérieures)

2. **Vérification de complétion du module** :
   - Vérifier si tous les quiz requis du module (minScoreToUnlockNext > 0) sont dans `CompletedQuiz`
   - Si oui : Créer une entrée dans `CompletedModule` (si pas déjà présente)

3. **Vérification des déblocages** :
   - Vérifier si des modules avec `prerequisiteModuleId` sont débloqués (requête simple sur `CompletedModule`)
   - Vérifier si des quiz avec `prerequisiteQuizId` sont débloqués (requête simple sur `CompletedQuiz`)

**Vérifications de déblocage (ultra-rapides)** :
```sql
-- Module débloqué ?
SELECT 1 FROM CompletedModule 
WHERE studentId=? AND moduleId=prerequisiteModuleId;

-- Quiz débloqué ?
SELECT 1 FROM CompletedQuiz 
WHERE studentId=? AND quizId=prerequisiteQuizId;
```

**Calculs dynamiques** :
- `isLocked` pour ModuleDto/QuizDto : Requête instantanée sur CompletedModule/CompletedQuiz
- `bestScore`, `attemptsCount` : Agrégation sur QuizSession (seulement si demandé)
- Progression module : COUNT des quiz dans CompletedQuiz (seulement pour affichage détaillé)

### Règles Leitner

1. **Bonne réponse** → La question monte d'une boîte (+1, maximum boîte 5)
2. **Mauvaise réponse** → La question retourne immédiatement en boîte 1
3. **Distribution de sélection** :
   - Boîte 1 : 50% des questions sélectionnées
   - Boîte 2 : 25%
   - Boîte 3 : 15%
   - Boîte 4 : 7%
   - Boîte 5 : 3%
4. **Si une boîte est vide**, son pourcentage est redistribué aux boîtes inférieures

### Workflow des Sessions

**États de session (SessionStatus)** :

| État | Description | Transitions |
|------|-------------|-------------|
| `IN_PROGRESS` | Session active, l'étudiant répond aux questions | → `COMPLETED` (via `/finish`)<br>→ `ABANDONED` (timeout 2h ou déconnexion) |
| `COMPLETED` | Session terminée normalement, score calculé | État final |
| `ABANDONED` | Session abandonnée (timeout ou déconnexion sans `/finish`) | État final (pas de points, pas de déblocage Leitner) |

**Règles** :
1. Une session devient `ABANDONED` automatiquement après **2 heures** d'inactivité
2. Une session `ABANDONED` ne compte pas dans les statistiques de progression
3. Les réponses partielles d'une session `ABANDONED` sont conservées mais non validées
4. L'étudiant peut relancer une nouvelle session du même quiz sans pénalité

### Gestion des Suppressions

| Suppression de... | Conséquence |
|-------------------|-------------|
| **Classroom** | Supprime modules, quiz, CompletedModule, CompletedQuiz, LeitnerBox, sessions, inscriptions |
| **Module** | Supprime les quiz du module, CompletedModule, CompletedQuiz associés, retire les questions du Leitner |
| **Quiz** | Supprime CompletedQuiz, retire les questions des boîtes Leitner de tous les étudiants |
| **Question** | Retire la question des boîtes Leitner de tous les étudiants |
| **Désinscription étudiant** | **Supprime** CompletedModule, CompletedQuiz et LeitnerBox (redémarrage complet si réinscription) |

### Code d'accès Classroom

1. Le code est **auto-généré** à la création du cours (6 caractères alphanumériques)
2. Le code **n'expire pas** automatiquement
3. Le professeur responsable peut **régénérer** le code à tout moment (l'ancien est invalidé)
4. Format : `[A-Z0-9]{6}` (ex: `ABC123`, `XK9P2M`)

### Validation des Données

| Champ | Règles |
|-------|--------|
| `email` | Format valide, domaine institutionnel autorisé |
| `password` | Minimum 8 caractères |
| `questionCount` (Leitner) | Valeurs acceptées : 5, 10, 15, 20 |
| `level` | Valeurs : L1, L2, L3, M1, M2 |
| `minScoreToUnlockNext` | 0 à 20 |

---

## Codes de réponse HTTP

| Code | Description |
|------|-------------|
| `200` | OK - Requête réussie |
| `201` | Created - Ressource créée |
| `204` | No Content - Suppression réussie |
| `400` | Bad Request - Données invalides |
| `401` | Unauthorized - Non authentifié |
| `403` | Forbidden - Accès refusé (permissions insuffisantes) |
| `404` | Not Found - Ressource non trouvée |
| `409` | Conflict - Ressource déjà existante (ex: déjà inscrit) |
| `422` | Unprocessable Entity - Données valides mais incohérentes |
| `500` | Internal Server Error |

---

## Codes d'erreur Métier

| Code | Description |
|------|-------------|
| `CLASSROOM_CODE_INVALID` | Le code d'accès est invalide |
| `ALREADY_ENROLLED` | L'utilisateur est déjà inscrit au cours |
| `QUIZ_LOCKED` | Le quiz est verrouillé (quiz prérequis non validé) |
| `MODULE_PREREQUISITE_NOT_MET` | Le module prérequis n'est pas complété |
| `QUIZ_PREREQUISITE_NOT_MET` | Le quiz prérequis n'est pas réussi |
| `CIRCULAR_PREREQUISITE` | Dépendance circulaire détectée dans les prérequis |
| `LEITNER_NO_QUESTIONS` | Aucune question disponible dans les boîtes Leitner |
| `INVALID_QUESTION_COUNT` | Le nombre de questions demandé n'est pas valide (5/10/15/20) |
| `INSUFFICIENT_PERMISSIONS` | Permissions insuffisantes pour cette action |
| `SESSION_ALREADY_FINISHED` | La session est déjà terminée |
| `SESSION_NOT_FOUND` | Session inexistante ou expirée |
