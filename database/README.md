# Module de Base de Données (`user_database`)

Ce dossier contient tout le code nécessaire à l'interaction avec la base de données PostgreSQL de l'application.

## Structure

- `user_database.py` : Le fichier principal contenant la classe `UserDatabase`. Cette classe encapsule toute la logique de connexion, de création de schéma et de manipulation des données (CRUD).
- `README.md` : Ce fichier de documentation.

## Configuration

La configuration de la connexion à la base de données est gérée par des variables d'environnement. Référez-vous au `README.md` principal du projet pour les instructions de configuration du fichier `.env`.

Les paramètres de connexion attendus sont :
- `DB_HOST`
- `DB_PORT` (par défaut `5433`)
- `DB_NAME`
- `DB_USER` (par défaut `davidravin` sur cet environnement)
- `DB_PASSWORD`

## Utilisation

Voici un exemple de base pour utiliser la classe `UserDatabase`.

```python
# main.py ou un script de test

from database.user_database import UserDatabase

# 1. Initialiser la classe avec les paramètres de connexion
db = UserDatabase(
    host="localhost",
    port=5433,
    database="job_search_app",
    user="davidravin",
    password=""
)

# 2. Établir la connexion
if db.connect():
    print("Connexion réussie !")

    # 3. Créer les tables (si elles n'existent pas)
    db.create_tables()
    print("Tables créées ou déjà existantes.")

    # 4. Utiliser les méthodes de la classe
    try:
        user_data = {
            'email': 'test@example.com',
            'password': 'a_very_secure_password',
            'first_name': 'Jean',
            'last_name': 'Dupont'
        }
        user_id, token = db.create_user(user_data)
        print(f"Utilisateur créé avec l'ID : {user_id}")
    except ValueError as e:
        print(f"Erreur lors de la création de l'utilisateur : {e}")

    # 5. Fermer la connexion
    db.disconnect()
```

## Schéma de la base de données

Le script crée automatiquement les tables suivantes :

- **users** : Informations de base des utilisateurs.
- **user_profiles** : Profils professionnels détaillés.
- **skills** : Liste centralisée des compétences.
- **user_skills** : Lie les utilisateurs aux compétences.
- **user_experiences** : Historique professionnel.
- **user_educations** : Parcours académique.
- **saved_searches** : Recherches d'emploi sauvegardées.
- **favorite_jobs** : Offres d'emploi mises en favori.
- **job_applications** : Suivi des candidatures.
- **user_preferences** : Paramètres de l'application pour un utilisateur.
- **user_sessions** : Gestion des sessions de connexion.

## Sécurité

- **Hachage de mot de passe** : Utilise PBKDF2-HMAC-SHA256 avec un sel unique pour chaque utilisateur.
- **Verrouillage de compte** : Le compte est temporairement verrouillé après 5 tentatives de connexion infructueuses.
- **Validation** : Le format des adresses e-mail est validé avant la création du compte.
