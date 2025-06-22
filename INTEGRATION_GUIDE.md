# Guide d'Intégration - Base de Données Utilisateurs

## 📋 Prérequis

1. PostgreSQL installé localement
2. Python 3.8+
3. Bibliothèques requises :
   ```bash
   pip install psycopg2-binary python-dotenv
   ```

## 🛠 Configuration Initiale

1. **Créer une base de données** :
   ```bash
   createdb job_search_app
   ```

2. **Créer un fichier `.env`** à la racine du projet :
   ```env
   # Configuration PostgreSQL
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=job_search_app
   DB_USER=postgres
   DB_PASSWORD=votre_mot_de_passe
   ```

## 🔌 Intégration dans votre application

### 1. Initialisation

```python
from database.user_database import UserDatabase
from database.config import DatabaseConfig

# Initialiser la connexion
db = UserDatabase(
    host=DatabaseConfig.HOST,
    database=DatabaseConfig.DATABASE,
    user=DatabaseConfig.USER,
    password=DatabaseConfig.PASSWORD,
    port=DatabaseConfig.PORT
)

# Établir la connexion
if not db.connect():
    raise Exception("Impossible de se connecter à la base de données")

# Créer les tables (à exécuter une seule fois)
db.create_tables()
```

### 2. Gestion des Utilisateurs

#### Créer un utilisateur
```python
user_data = {
    'email': 'user@example.com',
    'password': 'motdepasse',
    'first_name': 'Jean',
    'last_name': 'Dupont',
    'phone': '+33612345678',
    'address': '123 Rue Exemple',
    'postal_code': '75000',
    'city': 'Paris'
}

user_id = db.create_user(**user_data)
```

#### Authentifier un utilisateur
```python
user = db.authenticate_user('user@example.com', 'motdepasse')
if user:
    print(f"Connecté en tant que {user['first_name']} {user['last_name']}")
else:
    print("Identifiants invalides")
```

### 3. Gestion des Compétences

#### Ajouter des compétences
```python
# Ajouter une compétence à un utilisateur
db.add_skill_to_user(
    user_id=1,
    skill_name='Python',
    level='Avancé',
    experience_years=3
)
```

#### Récupérer les compétences
```python
skills = db.get_user_skills(user_id=1)
for skill in skills:
    print(f"{skill['skill_name']}: {skill['level']} ({skill['experience_years']} ans)")
```

## 🔄 Intégration avec l'API France Travail

### 1. Sauvegarder une offre d'emploi pour un utilisateur

```python
def save_job_offer_for_user(user_id, job_data):
    """
    Sauvegarde une offre d'emploi pour un utilisateur
    """
    return db.add_user_job_offer(
        user_id=user_id,
        job_id=job_data.get('id'),
        title=job_data.get('intitule'),
        company=job_data.get('entreprise', {}).get('nom'),
        location=job_data.get('lieuTravail', {}).get('libelle'),
        description=job_data.get('description'),
        contract_type=job_data.get('typeContrat'),
        salary=job_data.get('salaire', {}).get('libelle')
    )
```

### 2. Rechercher des offres correspondant aux compétences utilisateur

```python
def find_matching_jobs(user_id):
    """
    Trouve des offres correspondant aux compétences de l'utilisateur
    """
    # Récupérer les compétences de l'utilisateur
    user_skills = [s['skill_name'].lower() for s in db.get_user_skills(user_id)]
    
    # Récupérer les offres sauvegardées
    saved_jobs = db.get_user_job_offers(user_id)
    
    # Filtrer les offres par compétences (exemple simplifié)
    matching_jobs = []
    for job in saved_jobs:
        if any(skill in job['description'].lower() for skill in user_skills):
            matching_jobs.append(job)
    
    return matching_jobs
```

## 🚨 Gestion des Erreurs

Toujours envelopper les appels à la base de données dans des blocs try/except :

```python
try:
    db.some_operation()
except Exception as e:
    print(f"Erreur base de données: {str(e)}")
    # Loguer l'erreur
    # Retourner une réponse d'erreur appropriée
```

## 🔄 Bonnes Pratiques

1. **Connexions** : Toujours fermer la connexion quand vous avez terminé
   ```python
   try:
       # Utiliser la base de données
   finally:
       db.disconnect()
   ```

2. **Sécurité** :
   - Ne jamais stocker de mots de passe en clair
   - Utiliser des requêtes paramétrées pour éviter les injections SQL
   - Valider toutes les entrées utilisateur

3. **Performances** :
   - Utiliser des transactions pour les opérations multiples
   - Fermer les curseurs après utilisation
   - Utiliser le pooling de connexions en production

## 🔍 Dépannage

### Problèmes de connexion
- Vérifiez que PostgreSQL est en cours d'exécution
- Vérifiez les identifiants dans `.env`
- Vérifiez que l'utilisateur a les droits sur la base de données

### Problèmes de permissions
```sql
-- Dans psql
GRANT ALL PRIVILEGES ON DATABASE job_search_app TO votre_utilisateur;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO votre_utilisateur;
```

## 📚 Ressources Utiles

- [Documentation psycopg2](https://www.psycopg.org/docs/)
- [Documentation PostgreSQL](https://www.postgresql.org/docs/)
- [Python Database API Specification](https://www.python.org/dev/peps/pep-0249/)

## 📞 Support

Pour toute question ou problème, veuillez ouvrir une issue sur le dépôt GitHub.
