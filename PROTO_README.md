# Duobingo Backend - FastAPI Prototype

Backend API complet pour **Duobingo**, une plateforme d'apprentissage interactive pour les cours d'anatomie.

## 🚀 Démarrage rapide

### 1. Installation des dépendances

```bash
cd /home/mafoin/Documents/projet/m2-pojet-back

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Initialiser la base de données avec des données de test

```bash
python seed_data.py
```

### 3. Lancer le serveur

```bash
uvicorn main:app --reload
```

Le serveur sera accessible sur: **http://localhost:8000**

## 📖 Documentation API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Comptes de test

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| Admin | admin@univ-rennes.fr | admin123 |
| Professeur | house@univ-rennes.fr | prof123 |
| Professeur | wilson@univ-rennes.fr | prof123 |
| Étudiant | marie.martin@univ-rennes.fr | student123 |
| Étudiant | jean.dupont@univ-rennes.fr | student123 |

**Code Classroom**: `ANAT26`

## 📁 Structure du projet

```
m2-pojet-back/
├── app/
│   ├── core/           # Configuration, sécurité, base de données
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/         # Modèles SQLAlchemy
│   │   ├── user.py
│   │   ├── classroom.py
│   │   ├── module.py
│   │   ├── quiz.py
│   │   ├── question.py
│   │   ├── session.py
│   │   └── leitner.py
│   ├── schemas/        # Schémas Pydantic (DTOs)
│   │   ├── common.py
│   │   ├── user.py
│   │   ├── classroom.py
│   │   ├── module.py
│   │   ├── quiz.py
│   │   ├── question.py
│   │   ├── session.py
│   │   └── leitner.py
│   └── routes/         # Endpoints API
│       ├── auth.py
│       ├── classroom.py
│       ├── module.py
│       ├── quiz.py
│       ├── question.py
│       ├── session.py
│       ├── leitner.py
│       └── stats.py
├── main.py             # Point d'entrée FastAPI
├── seed_data.py        # Script de données de test
├── requirements.txt    # Dépendances Python
└── duobingo.db        # Base de données SQLite (créée au lancement)
```

## 🔧 Endpoints principaux

### Authentification
- `POST /api/auth/login` - Connexion (JWT)
- `POST /api/auth/register` - Inscription étudiant
- `GET /api/users/me` - Profil utilisateur

### Classrooms
- `GET /api/classrooms` - Liste des cours
- `POST /api/classrooms` - Créer un cours
- `POST /api/classrooms/{id}/join` - Rejoindre avec code

### Modules & Quiz
- `GET /api/classrooms/{cid}/modules` - Modules d'un cours
- `GET /api/modules/{mid}/quizzes` - Quiz d'un module
- `GET /api/quizzes/{qid}/questions` - Questions d'un quiz

### Gameplay
- `POST /api/sessions/start` - Démarrer une session
- `POST /api/sessions/{sid}/submit-answer` - Soumettre une réponse
- `POST /api/sessions/{sid}/finish` - Terminer la session

### Système Leitner
- `GET /api/classrooms/{cid}/leitner/status` - État des boîtes
- `POST /api/classrooms/{cid}/leitner/start` - Démarrer révision
- `POST /api/leitner/sessions/{sid}/submit-answer` - Répondre

### Statistiques
- `GET /api/stats/student` - Stats étudiant
- `GET /api/stats/leaderboard/{cid}` - Classement
- `GET /api/stats/dashboard/{cid}` - Dashboard prof

## 🧪 Test avec cURL

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "marie.martin@univ-rennes.fr", "password": "student123"}'

# Utiliser le token retourné
TOKEN="votre_token_ici"

# Voir les classrooms
curl -X GET http://localhost:8000/api/classrooms \
  -H "Authorization: Bearer $TOKEN"
```

## 📝 Fonctionnalités implémentées

- ✅ Authentification JWT
- ✅ Gestion des utilisateurs (Admin, Prof, Étudiant)
- ✅ CRUD Classrooms avec codes d'accès
- ✅ CRUD Modules avec prérequis
- ✅ CRUD Quiz avec prérequis
- ✅ Questions polymorphes (QCM, Vrai/Faux, Matching, Text, Image)
- ✅ Sessions de jeu (quiz gameplay)
- ✅ Système Leitner (5 boîtes de révision)
- ✅ Statistiques et progression
- ✅ Leaderboard
- ✅ Dashboard professeur
- ✅ Détection des dépendances circulaires
