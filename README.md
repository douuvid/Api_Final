# Client API France Travail (Pôle Emploi)

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Ce client Python permet d'interagir avec l'API France Travail (anciennement Pôle Emploi) pour rechercher des offres d'emploi et obtenir des détails sur des offres spécifiques.

## Table des matières

1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Utilisation](#utilisation)
5. [Exemples](#exemples)
6. [Documentation de l'API](#documentation-de-lapi)
7. [Dépannage](#dépannage)
8. [Contribution](#contribution)
9. [Licence](#licence)

## Prérequis

- Python 3.6 ou supérieur
- Compte développeur France Travail (Pôle Emploi)
- Identifiants API (client ID et client secret)

## Installation

### Option 1 : Installation via pip (recommandé)

```bash
# Créer un environnement virtuel (recommandé)
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer le package
pip install france-travail-api
```

### Option 2 : Installation à partir des sources

```bash
# Cloner le dépôt
git clone https://github.com/votre-utilisateur/france-travail-api.git
cd france-travail-api

# Créer et activer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer en mode développement
pip install -e .

# Installer les dépendances de développement
pip install -r requirements-dev.txt
```

## Configuration

1. **Obtenir des identifiants API** :
   - Allez sur le [Portail Développeur France Travail](https://www.emploi-store-dev.fr/)
   - Créez un compte si ce n'est pas déjà fait
   - Créez une nouvelle application pour obtenir vos identifiants (client ID et client secret)

2. **Configurer les variables d'environnement** :
   - Créez un fichier `.env` à la racine du projet
   - Ajoutez vos identifiants :
     ```
     FRANCE_TRAVAIL_CLIENT_ID=votre_client_id
     FRANCE_TRAVAIL_CLIENT_SECRET=votre_client_secret
     ```

## Utilisation

### Initialisation du client

```python
from france_travail import FranceTravailAPI

# Initialiser le client avec vos identifiants
client = FranceTravailAPI(
    client_id="votre_client_id",
    client_secret="votre_client_secret"
)

# Ou utiliser les variables d'environnement (recommandé)
import os
from dotenv import load_dotenv

load_dotenv()
client = FranceTravailAPI(
    client_id=os.getenv("FRANCE_TRAVAIL_CLIENT_ID"),
    client_secret=os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")
)
```

### Authentification

```python
# S'authentifier
if client.authenticate():
    print("Authentification réussie !")
else:
    print("Échec de l'authentification. Vérifiez vos identifiants.")
```

### Recherche d'offres d'emploi

```python
# Paramètres de recherche
params = {
    'motsCles': 'développeur python',  # Mots-clés de recherche
    'typeContrat': 'CDI,CDD',           # Types de contrat (optionnel)
    'range': '0-9',                     # Pagination (10 premiers résultats)
    'commune': '75056',                 # Code INSEE de la commune (optionnel)
    'distance': '10',                   # Rayon de recherche en km (optionnel)
}

# Effectuer la recherche
resultats = client.search_jobs(params)

# Traiter les résultats
if resultats and isinstance(resultats, list):
    print(f"{len(resultats)} offres trouvées")
    for offre in resultats[:5]:  # Afficher les 5 premières offres
        print(f"\n--- {offre.get('intitule')} ---")
        print(f"Entreprise: {offre.get('entreprise', {}).get('nom', 'Non spécifié')}")
        print(f"Lieu: {offre.get('lieuTravail', {}).get('libelle', 'Non spécifié')}")
        print(f"Type de contrat: {offre.get('typeContrat', 'Non spécifié')}")
```

### Obtenir les détails d'une offre spécifique

```python
# ID de l'offre (obtenu via la recherche)
offre_id = "1234567890"

# Récupérer les détails
details = client.get_job_details(offre_id)

if details:
    print(f"\n=== DÉTAILS DE L'OFFRE ===")
    print(f"Titre: {details.get('intitule')}")
    print(f"Entreprise: {details.get('entreprise', {}).get('nom', 'Non spécifié')}")
    print(f"Lieu: {details.get('lieuTravail', {}).get('libelle', 'Non spécifié')}")
    print(f"Type de contrat: {details.get('typeContrat', 'Non spécifié')}")
    print(f"Date de publication: {details.get('dateCreation', 'Non spécifiée')}")
    print(f"Salaire: {details.get('salaire', {}).get('libelle', 'Non spécifié')}")
    print(f"Expérience: {details.get('experienceLibelle', 'Non spécifiée')}")
    print("\nDescription du poste:")
    print(details.get('description', 'Aucune description disponible'))
    
    # Afficher les compétences requises
    competences = details.get('competences', [])
    if competences:
        print("\nCompétences requises:")
        for comp in competences:
            print(f"- {comp.get('libelle', '')}")
    
    # Lien vers l'offre
    print(f"\nPour postuler: https://candidat.pole-emploi.fr/offres/emploi/detail/{offre_id}")
```

## Exemples

Le répertoire `examples/` contient des scripts d'exemple :

- `basic_usage.py` : Exemple de base d'utilisation de l'API
- `recherche_developpeur_test.py` : Exemple de recherche d'offres pour "Développeur Test"

Pour exécuter un exemple :

```bash
# Se placer dans le répertoire racine du projet
cd france-travail-api

# Exécuter un exemple
python examples/recherche_developpeur_test.py
```

## Limites d'API

France Travail applique des limites de débit (rate limiting) pour chaque API. Voici les principales limites à connaître :

| API | Version | Limite | Description |
|-----|---------|--------|-------------|
| Offres d'emploi | v2 | 10 appels/seconde | Pour la recherche et la consultation des offres d'emploi |
| ROMEO | v2 | 2 appels/seconde | Pour la recherche d'entreprises |
| La Bonne Boite | v2 | 2 appels/seconde | Pour la recherche d'entreprises qui recrutent |
| Match via Soft Skills | v1 | 1 appel/seconde | Pour le matching par compétences |

### Bonnes pratiques

1. **Respectez les limites** : Le non-respect des limites peut entraîner un blocage temporaire.
2. **Implémentez un système de file d'attente** : Pour gérer les appaux API de manière optimale.
3. **Mettez en cache les réponses** : Pour réduire le nombre d'appaux inutiles.
4. **Gérez les erreurs 429** : En cas de dépassement, attendez avant de réessayer.

## Base de données

Le module `database` fournit une interface complète pour gérer les utilisateurs et leurs données dans une base de données PostgreSQL.

### Configuration

1. Assurez-vous que PostgreSQL est installé et en cours d'exécution
2. Créez un fichier `.env` à la racine du projet avec les informations de connexion :
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=job_search_app
   DB_USER=postgres
   DB_PASSWORD=votre_mot_de_passe
   ```

### Utilisation de base

```python
from database import UserDatabase

# Initialisation
db = UserDatabase(
    host="localhost",
    database="job_search_app",
    user="postgres",
    password="votre_mot_de_passe"
)

# Création des tables (à exécuter une seule fois)
if db.connect():
    db.create_tables()

# Création d'un utilisateur
user_data = {
    'email': 'utilisateur@example.com',
    'password': 'MotDePasseSécurisé123!',
    'first_name': 'Prénom',
    'last_name': 'Nom',
    'phone': '+33612345678'
}
user_id, token = db.create_user(user_data)
```

### Fonctionnalités clés

- Gestion des utilisateurs (création, authentification, mise à jour)
- Gestion des compétences (ajout, suppression, recherche)
- Suivi des expériences professionnelles
- Gestion des formations
- Sécurité intégrée (hachage des mots de passe, protection contre les attaques par force brute)

Pour plus de détails, consultez la [documentation complète du module database](database/README.md).

## Documentation de l'API

Pour plus d'informations sur les paramètres de recherche disponibles, consultez la [documentation officielle de l'API France Travail](https://www.emploi-store-dev.fr/).

### Paramètres de recherche courants

- `motsCles` : Mots-clés de recherche (ex: "développeur python")
- `typeContrat` : Type de contrat (CDI, CDD, etc.)
- `commune` : Code INSEE de la commune
- `distance` : Rayon de recherche en km (autour de la commune)
- `experience` : Niveau d'expérience requis
- `qualification` : Niveau de qualification
- `secteurActivite` : Secteur d'activité
- `range` : Pagination (ex: "0-9" pour les 10 premiers résultats)

## Méthodes disponibles

#### `search_jobs(params: Optional[Dict[str, Any]] = None) -> Optional[Dict]`

Recherche des offres d'emploi selon les critères spécifiés.

**Paramètres :**
- `params` (dict, optionnel) : Dictionnaire des paramètres de recherche. Les clés possibles sont :
  - `motsCles` (str) : Mots-clés pour la recherche
  - `commune` (str) : Code INSEE de la commune
  - `distance` (int) : Rayon de recherche en kilomètres
  - `typeContrat` (str) : Type de contrat (CDI, CDD, etc.)
  - `experience` (str) : Niveau d'expérience requis
  - `qualification` (str) : Niveau de qualification
  - `secteurActivite` (str) : Secteur d'activité
  - `entrepriseAdaptee` (bool) : Entreprise adaptée
  - `range` (str) : Plage de résultats (ex: "0-9" pour les 10 premiers résultats)

**Retourne :**
- Un dictionnaire contenant les résultats de la recherche ou None en cas d'erreur

#### `get_job_details(job_id: str) -> Optional[Dict]`

Récupère les détails d'une offre d'emploi spécifique.

**Paramètres :**
- `job_id` (str) : Identifiant de l'offre d'emploi

**Retourne :**
- Un dictionnaire contenant les détails de l'offre ou None en cas d'erreur

#### `match_soft_skills(rome_code: str, skills: list) -> Optional[Dict]`

Évalue la correspondance entre des compétences douces et un métier spécifique.

**Paramètres :**
- `rome_code` (str) : Code ROME du métier cible (ex: 'M1805' pour Développeur informatique)
- `skills` (list) : Liste des compétences douces à évaluer (ex: ['communication', 'travail d\'équipe'])

**Retourne :**
Un dictionnaire contenant :
- `match_score` (float) : Score global de correspondance (entre 0 et 1)
- `matching_skills` (list) : Liste des compétences pertinentes trouvées
- `missing_skills` (list) : Liste des compétences importantes manquantes
- `recommendations` (list) : Suggestions pour améliorer le matching

Retourne None en cas d'erreur.

**Exemple d'utilisation :**

```python
from france_travail import FranceTravailAPI

# Initialisation du client
api = FranceTravailAPI(client_id, client_secret)

# Compétences à évaluer
competences = [
    'communication',
    'travail d\'équipe',
    'résolution de problèmes',
    'autonomie',
    'créativité'
]

# Appel de l'API
resultats = api.match_soft_skills('M1805', competences)

# Affichage des résultats
if resultats:
    print(f"Score de correspondance: {resultats.get('match_score', 0):.0%}")
    print("\nCompétences pertinentes:")
    for comp in resultats.get('matching_skills', []):
        print(f"- {comp}")
    print("\nCompétences à développer:")
    for comp in resultats.get('missing_skills', []):
        print(f"- {comp}")
```

### Erreur d'authentification
- Vérifiez que votre client ID et client secret sont corrects
- Assurez-vous que votre compte développeur est actif
- Vérifiez que vous avez les bonnes autorisations (scopes)

### Aucun résultat trouvé
- Élargissez les critères de recherche
- Vérifiez l'orthographe des mots-clés
- Essayez avec des termes plus génériques

### Problèmes courants
- `400 Bad Request` : Vérifiez la validité des paramètres de recherche
- `401 Unauthorized` : Votre token a peut-être expiré, réauthentifiez-vous
- `429 Too Many Requests` : Vous avez dépassé la limite de requêtes, attendez avant de réessayer

## Contribution

Les contributions sont les bienvenues ! Voici comment contribuer :

1. Forkez le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/ma-fonctionnalite`)
3. Committez vos changements (`git commit -am 'Ajout d\'une fonctionnalité'`)
4. Poussez vers la branche (`git push origin feature/ma-fonctionnalite`)
5. Créez une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

Développé avec ❤️ pour faciliter l'accès aux offres d'emploi de France Travail.
