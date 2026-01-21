# Diagramme de Classes - Duobingo

Ce document présente le diagramme de classes UML du projet Duobingo basé sur les DTOs et la structure API.

---

## Diagramme Principal (Mermaid)

```mermaid
classDiagram
    direction TB

    %% ==========================================
    %% UTILISATEURS
    %% ==========================================
    
    class User {
        +UUID id
        +String email
        +String password
        +String name
        +Role role
        +DateTime createdAt
    }

    class StudentProfile {
        +UUID id
        +UUID userId
        +Level level
        +Integer totalPoints
        +Integer currentStreak
    }

    class TeacherProfile {
        +UUID id
        +UUID userId
        +String facultyDepartment
    }

    class Role {
        <<enumeration>>
        STUDENT
        TEACHER
        ADMIN
    }

    class Level {
        <<enumeration>>
        L1
        L2
        L3
        M1
        M2
    }

    User "1" -- "0..1" StudentProfile : has
    User "1" -- "0..1" TeacherProfile : has
    User --> Role
    StudentProfile --> Level

    %% ==========================================
    %% STRUCTURE PÉDAGOGIQUE
    %% ==========================================

    class Classroom {
        +UUID id
        +String name
        +Level level
        +String code
        +UUID responsibleProfessorId
        +DateTime createdAt
    }

    class ClassroomTeacher {
        +UUID classroomId
        +UUID teacherId
        +DateTime joinedAt
    }

    class ClassroomStudent {
        +UUID classroomId
        +UUID studentId
        +DateTime enrolledAt
    }

    class Module {
        +UUID id
        +UUID classroomId
        +String name
        +String category
        +UUID prerequisiteModuleId
        +DateTime createdAt
    }

    class Quiz {
        +UUID id
        +UUID moduleId
        +String title
        +UUID prerequisiteQuizId
        +Integer minScoreToUnlockNext
        +Boolean isActive
        +UUID createdById
        +DateTime createdAt
    }

    Classroom "1" *-- "*" Module : contains
    Module "1" *-- "*" Quiz : contains
    Module "0..1" <-- Module : prerequisite
    Quiz "0..1" <-- Quiz : prerequisite
    
    User "1" --> "*" Classroom : responsible for
    Classroom "1" -- "*" ClassroomTeacher : has teachers
    Classroom "1" -- "*" ClassroomStudent : has students
    ClassroomTeacher --> User
    ClassroomStudent --> User

    %% ==========================================
    %% QUESTIONS (POLYMORPHISME)
    %% ==========================================

    class Question {
        <<abstract>>
        +UUID id
        +UUID quizId
        +QuestionType type
        +String contentText
        +String explanation
        +UUID mediaId
        +DateTime createdAt
    }

    class QuestionType {
        <<enumeration>>
        QCM
        VRAI_FAUX
        MATCHING
        IMAGE
        TEXT
    }

    class QuestionOption {
        +UUID id
        +UUID questionId
        +String textChoice
        +Boolean isCorrect
        +Integer displayOrder
    }

    class MatchingPair {
        +UUID id
        +UUID questionId
        +String itemLeft
        +String itemRight
    }

    class ImageZone {
        +UUID id
        +UUID questionId
        +String labelName
        +Float x
        +Float y
        +Float radius
    }

    class TextConfig {
        +UUID id
        +UUID questionId
        +String acceptedAnswer
        +Boolean isCaseSensitive
        +Boolean ignoreSpellingErrors
    }

    class Media {
        +UUID id
        +String url
        +String filename
        +String mimeType
        +UUID uploadedById
        +DateTime uploadedAt
    }

    Quiz "1" *-- "*" Question : contains
    Question --> QuestionType
    Question "1" -- "*" QuestionOption : has (QCM/VRAI_FAUX)
    Question "1" -- "*" MatchingPair : has (MATCHING)
    Question "1" -- "*" ImageZone : has (IMAGE)
    Question "1" -- "0..1" TextConfig : has (TEXT)
    Question "*" --> "0..1" Media : uses

    %% ==========================================
    %% SESSIONS DE JEU
    %% ==========================================

    class QuizSession {
        +UUID id
        +UUID quizId
        +UUID studentId
        +UUID classroomId
        +SessionStatus status
        +Integer totalScore
        +Integer maxScore
        +Boolean passed
        +Integer pointsEarned
        +Integer questionsUnlocked
        +DateTime startedAt
        +DateTime completedAt
    }

    class SessionStatus {
        <<enumeration>>
        IN_PROGRESS
        COMPLETED
        ABANDONED
    }

    class SessionAnswer {
        +UUID id
        +UUID sessionId
        +UUID questionId
        +Boolean isCorrect
        +DateTime answeredAt
    }

    Quiz "1" -- "*" QuizSession : generates
    User "1" -- "*" QuizSession : takes
    Classroom "1" -- "*" QuizSession : hosts
    QuizSession --> SessionStatus
    QuizSession "1" *-- "*" SessionAnswer : contains
    SessionAnswer "*" --> "1" Question : answers

    %% ==========================================
    %% SYSTÈME LEITNER
    %% ==========================================

    class LeitnerBox {
        +UUID id
        +UUID classroomId
        +UUID studentId
        +UUID questionId
        +Integer boxLevel
        +DateTime addedAt
        +DateTime lastReviewedAt
    }

    class LeitnerSession {
        +UUID id
        +UUID classroomId
        +UUID studentId
        +Integer questionCount
        +Integer correctAnswers
        +Integer wrongAnswers
        +Integer promoted
        +Integer demoted
        +DateTime startedAt
        +DateTime completedAt
    }

    class LeitnerSessionAnswer {
        +UUID id
        +UUID sessionId
        +UUID questionId
        +Boolean isCorrect
        +Integer previousBox
        +Integer newBox
        +DateTime answeredAt
    }

    Classroom "1" -- "*" LeitnerBox : has boxes for
    User "1" -- "*" LeitnerBox : has progress
    Question "1" -- "*" LeitnerBox : stored in
    
    User "1" -- "*" LeitnerSession : takes
    Classroom "1" -- "*" LeitnerSession : hosts
    LeitnerSession "1" *-- "*" LeitnerSessionAnswer : contains
    LeitnerSessionAnswer "*" --> "1" Question : reviews
```

---

## Diagramme Simplifié (Vue d'ensemble)

```mermaid
classDiagram
    direction LR

    User "1" --> "*" Classroom : creates/manages
    User "*" --> "*" Classroom : enrolled in
    
    Classroom "1" *-- "*" Module : contains
    Module "1" *-- "*" Quiz : contains
    Quiz "1" *-- "*" Question : contains
    
    User "1" --> "*" QuizSession : plays
    Quiz "1" --> "*" QuizSession : generates
    
    User "1" --> "*" LeitnerBox : has progress
    Classroom "1" --> "*" LeitnerBox : contains
    Question "1" --> "*" LeitnerBox : stored in
```

---

## Description des Entités

### Utilisateurs

| Entité | Description |
|--------|-------------|
| **User** | Utilisateur du système (étudiant, professeur ou admin) |
| **StudentProfile** | Profil spécifique aux étudiants (niveau, points, streak) |
| **TeacherProfile** | Profil spécifique aux professeurs (département) |

### Structure Pédagogique

| Entité | Description |
|--------|-------------|
| **Classroom** | Cours/classe - conteneur principal géré par un prof responsable |
| **ClassroomTeacher** | Table de liaison - enseignants associés à un cours |
| **ClassroomStudent** | Table de liaison - étudiants inscrits à un cours |
| **Module** | Module thématique au sein d'un cours (peut avoir un prérequis) |
| **Quiz** | Quiz/examen au sein d'un module (peut avoir un quiz prérequis) |
| **CompletedModule** | Marqueur simple : module complété par un étudiant (pour débloquer les modules suivants) |
| **CompletedQuiz** | Marqueur simple : quiz réussi par un étudiant (pour vérifier les déblocages) |

### Questions

| Entité | Description |
|--------|-------------|
| **Question** | Question abstraite (polymorphisme via QuestionType) |
| **QuestionOption** | Option de réponse pour QCM/VRAI_FAUX |
| **MatchingPair** | Paire d'appariement pour MATCHING |
| **ImageZone** | Zone cliquable sur image pour IMAGE |
| **TextConfig** | Configuration de réponse textuelle pour TEXT |
| **Media** | Fichier média (image) associé aux questions |

### Sessions de Jeu

| Entité | Description |
|--------|-------------|
| **QuizSession** | Session de jeu d'un quiz par un étudiant |
| **SessionAnswer** | Réponse donnée pendant une session |

### Système Leitner

| Entité | Description |
|--------|-------------|
| **LeitnerBox** | Position d'une question dans les boîtes Leitner d'un étudiant pour un cours |
| **LeitnerSession** | Session de révision Leitner (statistiques agrégées) |
| **LeitnerSessionAnswer** | Détail d'une réponse durant une session Leitner (pour review) |

---

## Relations Clés

### Hiérarchie de Contenu
```
Classroom (1) ──contains──> (*) Module (1) ──contains──> (*) Quiz (1) ──contains──> (*) Question
```

### Gestion des Permissions
```
User (Prof Responsable) ──creates──> Classroom
Classroom ──has teachers──> User (via ClassroomTeacher)
Classroom ──has students──> User (via ClassroomStudent)
```

### Progression Étudiant
```
User (Student) ──takes──> QuizSession ──for──> Quiz
User (Student) ──has──> LeitnerBox ──in──> Classroom
LeitnerBox ──contains──> Question (avec boxLevel 1-5)
```

### Prérequis
```
Module ──prerequisite──> Module (self-reference optionnelle)
Quiz.minScoreToUnlockNext détermine si le quiz suivant est accessible
```

---

## Notes d'Implémentation

### Polymorphisme des Questions

Le champ `type` dans `Question` détermine quelles tables de détail sont utilisées :

| Type | Tables associées |
|------|------------------|
| `QCM` | QuestionOption (multiple, 1+ correctes) |
| `VRAI_FAUX` | QuestionOption (exactement 2) |
| `MATCHING` | MatchingPair |
| `IMAGE` | ImageZone + Media |
| `TEXT` | TextConfig |

### Tables de Liaison

Les relations many-to-many utilisent des tables intermédiaires :

- `ClassroomTeacher` : Classroom ↔ User (professeurs)
- `ClassroomStudent` : Classroom ↔ User (étudiants)
- `LeitnerBox` : Classroom ↔ User ↔ Question (avec boxLevel)

### Cascade de Suppression

```
DELETE Classroom → DELETE Modules → DELETE Quizzes → DELETE Questions
                                  → DELETE CompletedModule
                                  → DELETE CompletedQuiz
                → DELETE ClassroomTeachers
                → DELETE ClassroomStudents
                → DELETE LeitnerBoxes
                → DELETE LeitnerSessions → DELETE LeitnerSessionAnswers
                → DELETE QuizSessions → DELETE SessionAnswers

DELETE Module → DELETE CompletedModule (pour ce module)
DELETE Quiz → DELETE CompletedQuiz (pour ce quiz)

DELETE Media → ÉCHEC si utilisé par une Question (contrainte FK)

DELETE Student → DELETE CompletedModule + CompletedQuiz + LeitnerBox (redémarrage complet)
```

**Principe** : 
- `CompletedModule` et `CompletedQuiz` sont les seules tables de cache
- Permettent des vérifications de déblocage instantanées (index sur PK)
- Tout le reste (stats, scores) est calculé dynamiquement depuis `QuizSession`

---

## Diagramme PlantUML (Alternative)

```plantuml
@startuml Duobingo Class Diagram

skinparam classAttributeIconSize 0
skinparam linetype ortho

package "Users" {
    enum Role {
        STUDENT
        TEACHER
        ADMIN
    }
    
    enum Level {
        L1
        L2
        L3
        M1
        M2
    }
    
    class User {
        id: UUID
        email: String
        password: String
        name: String
        role: Role
        createdAt: DateTime
    }
    
    class StudentProfile {
        id: UUID
        userId: UUID
        level: Level
        totalPoints: Integer
        currentStreak: Integer
    }
    
    class TeacherProfile {
        id: UUID
        userId: UUID
        facultyDepartment: String
    }
}

package "Classroom" {
    class Classroom {
        id: UUID
        name: String
        level: Level
        code: String
        responsibleProfessorId: UUID
        createdAt: DateTime
    }
    
    class Module {
        id: UUID
        classroomId: UUID
        name: String
        category: String
        prerequisiteModuleId: UUID
        createdAt: DateTime
    }
    
    class Quiz {
        id: UUID
        moduleId: UUID
        title: String
        minScoreToUnlockNext: Integer
        isActive: Boolean
        createdById: UUID
        createdAt: DateTime
    }
}

package "Questions" {
    enum QuestionType {
        QCM
        VRAI_FAUX
        MATCHING
        IMAGE
        TEXT
    }
    
    abstract class Question {
        id: UUID
        quizId: UUID
        type: QuestionType
        contentText: String
        explanation: String
        mediaId: UUID
    }
    
    class QuestionOption {
        id: UUID
        questionId: UUID
        textChoice: String
        isCorrect: Boolean
    }
    
    class MatchingPair {
        id: UUID
        questionId: UUID
        itemLeft: String
        itemRight: String
    }
    
    class ImageZone {
        id: UUID
        questionId: UUID
        labelName: String
        x: Float
        y: Float
        radius: Float
    }
    
    class TextConfig {
        id: UUID
        questionId: UUID
        acceptedAnswer: String
        isCaseSensitive: Boolean
        ignoreSpellingErrors: Boolean
    }
}

package "Sessions" {
    class QuizSession {
        id: UUID
        quizId: UUID
        studentId: UUID
        totalScore: Integer
        maxScore: Integer
        passed: Boolean
        pointsEarned: Integer
        completedAt: DateTime
    }
    
    class LeitnerBox {
        id: UUID
        classroomId: UUID
        studentId: UUID
        questionId: UUID
        boxLevel: Integer
        lastReviewedAt: DateTime
    }
    
    class LeitnerSession {
        id: UUID
        classroomId: UUID
        studentId: UUID
        questionCount: Integer
        correctAnswers: Integer
        wrongAnswers: Integer
        completedAt: DateTime
    }
}

' Relations
User "1" -- "0..1" StudentProfile
User "1" -- "0..1" TeacherProfile
User "1" -- "*" Classroom : responsible
Classroom "1" *-- "*" Module
Module "1" *-- "*" Quiz
Quiz "1" *-- "*" Question
Question "1" -- "*" QuestionOption
Question "1" -- "*" MatchingPair
Question "1" -- "*" ImageZone
Question "1" -- "0..1" TextConfig
User "1" -- "*" QuizSession
Quiz "1" -- "*" QuizSession
User "1" -- "*" LeitnerBox
Classroom "1" -- "*" LeitnerBox
Question "1" -- "*" LeitnerBox

@enduml
```

---

## Visualisation

Pour visualiser ces diagrammes :

1. **Mermaid** : Copier le code dans [Mermaid Live Editor](https://mermaid.live/)
2. **PlantUML** : Copier le code dans [PlantUML Online](https://www.plantuml.com/plantuml/)
3. **VS Code** : Installer l'extension "Markdown Preview Mermaid Support" ou "PlantUML"
