# Documentation API Duobingo - Explications des Choix Architecturaux

Ce README explique les principes et choix de conception derrière la documentation API Duobingo.

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Philosophie de conception](#philosophie-de-conception)
3. [Choix des DTOs](#choix-des-dtos)
4. [Modèle de données](#modèle-de-données)
5. [Système Leitner](#système-leitner)
6. [Permissions et hiérarchie](#permissions-et-hiérarchie)
7. [Validation et gestion d'erreurs](#validation-et-gestion-derreurs)
8. [Structure de la documentation](#structure-de-la-documentation)

---

## Vue d'ensemble

**Duobingo** est une plateforme d'apprentissage interactive pour des cours d'anatomie à l'Université Rennes. Elle combine :
- 📚 **Gestion pédagogique** : Cours (Classrooms), Modules, Quiz
- ❓ **Banque de questions** : 5 types polymorphes (QCM, Vrai/Faux, Matching, Image, Texte)
- 🧠 **Système de révision** : Leitner spaced-repetition (5 boîtes)
- 📊 **Progression** : Suivi dynamique des étudiants

---

## Philosophie de conception

### 1. **Minimal Storage, Maximum Calculation**

**Principe** : Ne stocker que ce qui est impossible ou inefficace de calculer.

#### ✅ Stocké
- **Données brutes** : Questions, réponses, sessions
- **Tables de cache** : `CompletedQuiz`, `CompletedModule` (pour déblocage rapide)
- **États mutables** : `LeitnerBox` (progresse avec chaque réponse)

#### ❌ NON stocké
- **Points/Scores de l'étudiant** : Calculés depuis `QuizSession.totalScore`
- **Statistiques** : `averageScore`, `leitnerMastery`, `completionRate` calculés à la demande
- **Streaks/Progressions** : Recalculés dynamiquement
- **Réponses Leitner** : Stockées dans `LeitnerSessionAnswer` (pour correction), pas dans `LeitnerSession`

**Avantage** : 
- Cohérence garantie (pas de désynchronisation)
- Queries rapides (índices sur `CompletedQuiz`, `CompletedModule`)
- Flexible (changement de règles sans migration)

---

### 2. **DTOs = Contrats API, pas reflections du modèle**

Les **DTOs ne reflètent pas 1:1 les entités** du modèle de données.

#### Exemple : `QuizDto`

```json
{
  "id": "uuid",
  "moduleId": "uuid",
  "title": "Le Pied",
  "questionCount": 20,        // ← Calculé dynamiquement
  "isLocked": false,          // ← Calculé par étudiant
  "isActive": true,
  "createdBy": { ... },       // ← Objet imbriqué (pas FK directe)
  "createdAt": "2026-01-15T..."
}
```

**Pourquoi** ?
- `questionCount` : Nombre réel de questions (COUNT depuis Question table)
- `isLocked` : Dépend de l'étudiant et ses complétions
- `createdBy` : Résolution de FK pour enrichir la réponse

---

### 3. **Pagination obligatoire pour les listes longues**

Toutes les réponses paginées utilisent `PaginatedResponseDto<T>` :

```json
{
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "totalItems": 1500,
    "totalPages": 75,
    "hasNextPage": true,
    "hasPreviousPage": false
  }
}
```

**Listes paginées** :
- `/api/classrooms` - Selon rôle (étudiant : inscrits, prof : gérés)
- `/api/classrooms/{cid}/modules`
- `/api/modules/{mid}/quizzes`
- `/api/stats/leaderboard/{cid}`
- `/api/progress/classroom/{cid}`

---

## Choix des DTOs

### Pourquoi ces 40+ DTOs ?

#### 1. **Séparation des préoccupations**

| DTO | Raison | Utilisation |
|-----|--------|-----------|
| `RegisterStudentDto` | Input spécifique (name + level) | POST `/api/auth/register` |
| `UserResponseDto` | Output complexe (profils multiples) | GET `/api/users/me` |
| `ClassroomDto` | Résumé avec profs + count étudiants | GET `/api/classrooms` |
| `ClassroomMembersDto` | Détail complet paginé | GET `/api/classrooms/{id}/members` |

#### 2. **Anti-redondance**

`UserSummaryDto` est réutilisé partout :
- Dans `ClassroomMembersDto.responsibleProfessor`
- Dans `QuizDto.createdBy`
- Dans `LeitnerSessionReviewDto.answers[].correctedBy` (futur)

➜ **Maintenance centralisée** : un changement à un endroit

#### 3. **DTOs polymorphes**

`QuestionCreateDto` gère tous les types via un seul DTO :

```json
{
  "type": "QCM | VRAI_FAUX | MATCHING | IMAGE | TEXT",
  "contentText": "...",
  "options": [ ... ],        // Optionnel, requis pour QCM/VRAI_FAUX
  "matchingPairs": [ ... ],  // Requis pour MATCHING
  "imageZones": [ ... ],     // Requis pour IMAGE
  "textConfig": { ... }      // Requis pour TEXT
}
```

**Avantage** : Pas de 5 DTOs différents, logique métier côté backend

---

### Champs calculés vs stockés : Règles

#### Exemple : `StudentStatsDto`

```json
{
  "totalCompletedQuizzes": 45,        // ← COUNT CompletedQuiz
  "averageScore": 16.2,               // ← AVG QuizSession.totalScore
  "leitnerMastery": 0.62,             // ← % questions en boîtes 4-5
  "classroomsProgress": [ ... ]       // ← Pour chaque cours
}
```

**Aucun point n'est jamais stocké** :
- `totalCompletedQuizzes` = COUNT(CompletedQuiz WHERE studentId = ?)
- `averageScore` = AVG(QuizSession.totalScore WHERE studentId = ?)
- `leitnerMastery` = COUNT(LeitnerBox WHERE boxLevel IN (4,5)) / COUNT(LeitnerBox)

**Performance** :
- Indices sur `CompletedQuiz(studentId)`, `QuizSession(studentId)`, `LeitnerBox(studentId, boxLevel)`
- Requêtes calculées à la demande (ou cachées en Redis si usage fréquent)

---

## Modèle de données

### Hiérarchie pédagogique

```
Classroom (niveau racine)
  ├── Module (enfant de Classroom)
  │     └── Quiz (enfant de Module)
  │           └── Question (5 types polymorphes)
  └── CompletedModule / CompletedQuiz (cache)
```

### Tables principales

| Table | Rôle | Clé |
|-------|------|-----|
| `User` | Authentification + Profils | `id` (UUID) |
| `Classroom` | Conteneur pédagogique | `id` (UUID) |
| `Module` | Unité d'apprentissage | `id` (UUID), FK `classroomId` |
| `Quiz` | Examen | `id` (UUID), FK `moduleId` |
| `Question` | Polymorphe (5 types) | `id` (UUID), FK `quizId` |
| `QuizSession` | Session jouée | `id` (UUID), FK `quizId`, `studentId`, `classroomId` |
| `SessionAnswer` | Réponse à 1 question | `id` (UUID), FK `sessionId`, `questionId` |
| **`CompletedQuiz`** | ⭐ **Cache** | PK composite `(studentId, quizId)` |
| **`CompletedModule`** | ⭐ **Cache** | PK composite `(studentId, moduleId)` |
| `LeitnerBox` | Progression Leitner | PK composite `(classroomId, studentId, questionId)` |
| `LeitnerSession` | Session de révision | `id` (UUID) |
| `LeitnerSessionAnswer` | Réponse Leitner | `id` (UUID), FK `sessionId`, `questionId` |

### Pourquoi `CompletedQuiz` et `CompletedModule` ?

**Problème sans cache** :
```sql
-- Déblocage rapide ?
SELECT 1 FROM QuizSession 
WHERE studentId = ? AND quizId = ? AND totalScore >= minScoreToUnlockNext;
-- ❌ Join 3 tables, slow pour chaque vérification
```

**Avec cache** :
```sql
-- Déblocage ultra-rapide
SELECT 1 FROM CompletedQuiz 
WHERE studentId = ? AND quizId = ?;
-- ✅ Requête instantanée sur composite key
```

**Maintenance** :
- `CompletedQuiz` créé automatiquement à `/api/sessions/{sid}/finish` si `passed = true`
- `CompletedModule` créé automatiquement si tous les quiz du module sont dans `CompletedQuiz`

---

## Système Leitner

### Principes

**Spaced-repetition** avec 5 boîtes par Classroom et Étudiant :

```
Box 1: 50% → Débutant
Box 2: 25% → Familier
Box 3: 15% → Confirmé
Box 4: 7%  → Expert
Box 5: 3%  → Maître
```

### Déblocage des questions

1. Étudiant réussit un quiz **pour la première fois** (score ≥ `minScoreToUnlockNext`)
2. ✅ Toutes les questions du quiz ajoutées en **Boîte 1**
3. Si une question existe déjà dans une boîte (2, 3, 4, 5), elle **reste à son niveau**

### Progression des boîtes

**Bonne réponse** :
```
Box 1 → Box 2
Box 2 → Box 3
...
Box 5 → Box 5 (reste)
```

**Mauvaise réponse** :
```
Box N → Box 1 (réinitialisation)
```

### Modèle de données Leitner

```
LeitnerBox (snapshot courant)
├── classroomId
├── studentId
├── questionId
├── boxLevel (1-5)
└── lastReviewedAt

LeitnerSession (historique)
├── id
├── classroomId, studentId
├── questionCount
├── startedAt, completedAt
└── LeitnerSessionAnswer[] (réponses détaillées)
```

**Pas de points ou statistiques stockées** :
- Correctness calculé à partir de `LeitnerSessionAnswer`
- Mouvements de boîtes (promoted, demoted) calculés pendant la session

---

## Permissions et hiérarchie

### 3 rôles principaux

| Rôle | Permissions |
|------|-----------|
| **STUDENT** | Jouer aux quiz, réviser Leitner, consulter stats perso |
| **TEACHER** | Créer/gérer quiz et questions dans ses cours |
| **ADMIN** | Accès total, gestion des comptes |

### Hiérarchie dans un Classroom

```
Prof Responsable (créateur)
  ├─ Créer/modifier/supprimer le cours
  ├─ Ajouter/retirer enseignants
  ├─ Ajouter/retirer étudiants
  ├─ Créer/modifier/supprimer modules
  └─ Créer/modifier/supprimer quiz et questions

Autres Enseignants
  ├─ Créer/modifier/supprimer quiz et questions
  └─ ❌ Gérer le cours ou les modules

Étudiants
  ├─ Rejoindre avec code
  ├─ Jouer aux quiz (si débloqués)
  └─ Réviser via Leitner
```

### Vérifications rapides

```sql
-- Prof responsable ?
SELECT 1 FROM Classroom 
WHERE id = ? AND responsibleProfessorId = ?;

-- Prof du cours ?
SELECT 1 FROM Classroom 
WHERE id = ? AND responsibleProfessorId = ? 
OR EXISTS (SELECT 1 FROM ClassroomTeacher 
           WHERE classroomId = ? AND teacherId = ?);

-- Étudiant inscrit ?
SELECT 1 FROM ClassroomStudent 
WHERE classroomId = ? AND studentId = ?;
```

---

## Validation et gestion d'erreurs

### Codes d'erreur métier

| Code | Signification | HTTP |
|------|---------------|------|
| `QUIZ_LOCKED` | Prérequis non satisfait | 403 |
| `MODULE_PREREQUISITE_NOT_MET` | Module bloqué | 403 |
| `CIRCULAR_PREREQUISITE` | Cycle dans dépendances | 422 |
| `LEITNER_NO_QUESTIONS` | Aucune question débloquée | 400 |
| `ALREADY_ENROLLED` | Étudiant déjà inscrit | 409 |

### Validation des dépendances

**Avant d'ajouter un prérequis** :
1. Vérifier qu'il n'existe pas de cycle (max 50 niveaux)
2. Rejeter si A → B → C → A détecté
3. Retourner erreur `422 CIRCULAR_PREREQUISITE`

```pseudo
function hasCycle(currentId, targetId, type='module', depth=0):
  if depth > 50:
    return true  // Profondeur excessive
  if currentId == targetId:
    return true  // Cycle détecté
  
  prereq = getPrerequisite(currentId, type)
  if not prereq:
    return false
  
  return hasCycle(prereq.id, targetId, type, depth + 1)
```

---

## Structure de la documentation

### 📄 Fichiers

```
doc/
├── README.md                    ← Vous êtes ici
├── dto.md                       ← 40+ DTOs avec exemples JSON
├── endpoints.md                 ← 35+ endpoints avec détails
├── class-diagram.puml           ← Diagramme PlantUML
├── class-diagram.md             ← Diagramme Mermaid + descriptions
```

### Conventions

#### DTOs

- **Nommage** : `[Nom]Dto` ou `[Action][Nom]Dto`
  - `RegisterStudentDto` (input d'enregistrement)
  - `UserResponseDto` (output de réponse)
  - `ClassroomMembersDto` (output détaillé)

- **Champs calculés** : Marqués dans la description
  ```markdown
  | `questionCount` | Integer | Nombre de questions (calculé dynamiquement) |
  ```

#### Endpoints

- **Hiérarchie claire** : Enfants sous parents
  ```
  POST   /api/classrooms
  GET    /api/classrooms
  GET    /api/classrooms/{id}
  PATCH  /api/classrooms/{id}
  DELETE /api/classrooms/{id}
  ```

- **Permissions précises** : Toujours spécifiées
  ```markdown
  **Accès** : Prof Responsable uniquement
  ```

#### Notes importantes

- `**Note** :` pour contexte métier
- `**Description** :` pour explication détaillée
- `**Règles** :` pour comportements spéciaux

---

## Principes clés à retenir

1. ✅ **DTOs ≠ Entités** : Adaptés au contrat API, pas au modèle DB
2. ✅ **Minimal Storage** : Stocker peu, calculer beaucoup
3. ✅ **Cache prudent** : Seulement pour déblocage rapide
4. ✅ **Permissions explicites** : Jamais ambiguës
5. ✅ **Validation stricte** : Cycles détectés, données valides
6. ✅ **Pagination obligatoire** : Même pour petites listes
7. ✅ **Dépendances testées** : Avant chaque création/modification

---

## Points de contact

Pour toute question sur :
- **DTOs** : Voir `dto.md`
- **Endpoints** : Voir `endpoints.md`
- **Modèle de données** : Voir `class-diagram.puml` ou `class-diagram.md`
- **Règles métier** : Voir `endpoints.md` → section "Règles Métier"

---

**Documentation générée le 21 janvier 2026** ✨
