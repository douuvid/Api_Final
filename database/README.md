# Gestion de la base de données

Ce dossier contient le code pour la gestion de la base de données PostgreSQL de l'application de recherche d'emploi.

## Structure

- `__init__.py` - Fichier d'initialisation du package
- `config.py` - Configuration de la base de données
- `user_database.py` - Implémentation de la classe UserDatabase
- `README.md` - Ce fichier de documentation

## Configuration

1. Copiez le fichier `.env.example` vers `.env` :
   ```bash
   cp .env.example .env
   ```

2. Modifiez les variables d'environnement dans `.env` selon votre configuration PostgreSQL.

3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

```python
from database import UserDatabase, DatabaseConfig

# Initialisation de la base de données
db = UserDatabase(
    host=DatabaseConfig.HOST,
    database=DatabaseConfig.DATABASE,
    user=DatabaseConfig.USER,
    password=DatabaseConfig.PASSWORD,
    port=DatabaseConfig.PORT
)

# Connexion à la base de données
if db.connect():
    # Création des tables
    db.create_tables()
    
    # Exemple: Création d'un utilisateur
    user_data = {
        'email': 'test@example.com',
        'password': 'motdepasse',
        'first_name': 'Jean',
        'last_name': 'Dupont'
    }
    
    try:
        user_id, verification_token = db.create_user(user_data)
        print(f"Utilisateur créé avec l'ID: {user_id}")
    except ValueError as e:
        print(f"Erreur: {e}")
    
    # Fermeture de la connexion
    db.disconnect()
```

## Schéma de la base de données

### Tables principales

1. **users** - Informations de base des utilisateurs
2. **user_profiles** - Profils professionnels des utilisateurs
3. **skills** - Compétences disponibles
4. **user_skills** - Compétences des utilisateurs avec niveau
5. **user_experiences** - Expériences professionnelles
6. **user_educations** - Formations
7. **saved_searches** - Recherches sauvegardées
8. **favorite_jobs** - Offres d'emploi favorites
9. **job_applications** - Candidatures
10. **user_preferences** - Préférences utilisateur
11. **user_sessions** - Sessions utilisateur

## Sécurité

- Les mots de passe sont hachés avec PBKDF2-HMAC-SHA256 et un sel unique
- Verrouillage des comptes après 5 tentatives de connexion échouées
- Validation des emails
- Gestion des jetons de vérification et de réinitialisation de mot de passe

## Tests

Les tests unitaires se trouvent dans le dossier `tests/`.

## Licence

[À spécifier]
