# Conventions de nommage (API & tests)

Ce mémo définit les règles de nommage à suivre et précise comment elles sont déjà respectées dans la suite de tests.

## Règles générales API

- DTO : noms en PascalCase terminés par `Dto` (ex. `QuizDto`, `RegisterStudentDto`).
- Champs JSON : camelCase pour refléter le contrat API (ex. `questionCount`, `minScoreToUnlockNext`).
- Codes/énumérations : MAJUSCULES avec underscores si nécessaire (ex. `ADMIN`, `STUDENT`, `VRAI_FAUX`).
- Routes : minuscules, segments au pluriel, ressources enfants imbriquées (`/classrooms/{id}/modules`).

## Règles Python (tests)

- Fichiers : `test_<domaine>.py` pour les tests, `conftest.py` pour les fixtures partagées.
- Fonctions de test : `test_<action>_<scenario>` en snake_case, verbes clairs (`test_create_classroom_success`).
- Fixtures : snake_case descriptif (`student_token`, `classroom_id`, `media_id`).
- Constantes : MAJUSCULES avec underscores (`TEST_USERS`, `TEST_JWT_SECRET`).
- Fonctions utilitaires : verbes en snake_case (`create_test_token`).
- Variables locales : snake_case concis (`response`, `payload`, `levels`).
- Données JSON envoyées aux endpoints : conserver le casing du contrat API (camelCase) même si la variable Python est en snake_case.
- Docstrings de test : triple guillemets, phrase courte « Expected: … » pour l’attendu métier/statut.

## Conformité actuelle (tests existants)

- Fichiers de test déjà au format `test_*.py` : voir [tests/test_auth.py](tests/test_auth.py) et [tests/test_classrooms.py](tests/test_classrooms.py).
- Fixtures en snake_case descriptif regroupées dans [tests/conftest.py](tests/conftest.py) (`student_token`, `module_id`, `media_id`).
- Constantes en MAJUSCULES dans [tests/conftest.py](tests/conftest.py) (`TEST_USERS`, `TEST_CLASSROOM_CODE`, `TEST_JWT_SECRET`).
- Fonctions de test en snake_case explicite dans [tests/test_auth.py](tests/test_auth.py) (ex. `test_login_valid_credentials`, `test_register_student_success`).
- Payloads JSON conservent le camelCase attendu par l’API (ex. `minScoreToUnlockNext` dans [tests/test_classrooms.py](tests/test_classrooms.py)).

## Checklist rapide avant d’ajouter du code

- Le nom du fichier commence par `test_` (sauf `conftest.py`).
- Les nouvelles fixtures sont en snake_case, réutilisables et déclarées dans `conftest.py` si partagées.
- Toute donnée envoyée à l’API respecte le casing contractuel (camelCase dans le JSON).
- Les constantes partagées sont en MAJUSCULES, définies au niveau module.
- La fonction de test est nommée `test_<action>_<scenario>` et possède une docstring précisant l’attendu.
