# 🚀 API France Travail - Matching de Compétences

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![API Status](https://img.shields.io/badge/API%20Status-En%20ligne-brightgreen)](https://www.emploi-store-dev.fr/)

Solution complète pour l'analyse et le matching des compétences avec les offres d'emploi France Travail.

## ✨ Fonctionnalités

- 🔍 Recherche intelligente d'offres d'emploi
- 🎯 Matching précis des compétences
- 📊 Analyse des tendances du marché
- 🚀 API RESTful simple d'utilisation
- 🔄 Données temps réel de l'API France Travail
- 🛠️ Outils d'analyse avancée

## 📋 Table des matières

- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [API Endpoints](#-api-endpoints)
- [Exemples](#-exemples)
- [Dépannage](#-dépannage)
- [Contribution](#-contribution)
- [Licence](#-licence)

## 🚀 Installation

### Prérequis

- Python 3.8+
- Compte développeur [France Travail](https://www.emploi-store-dev.fr/)
- Identifiants API (client ID et client secret)

### Installation

1. Cloner le dépôt :
   ```bash
   git clone https://github.com/douuvid/Api_Final.git
   cd Api_Final
   ```

2. Créer un environnement virtuel :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # OU
   .\venv\Scripts\activate  # Windows
   ```

3. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## 🏗️ Architecture du Projet

### 1. `app.py` - Le Serveur Principal
**Rôle** : Gère les requêtes HTTP et les réponses API.

**Fonctionnalités** :
- 🚀 Lance le serveur web (port 5000)
- 🔄 Gère les routes API
- 🔒 Gère l'authentification
- 🛠️ Orchestre les appaux aux différents services

### 2. `france_travail/alternative_client.py` - Le Moteur d'API
**Rôle** : Interface avec l'API France Travail.

**Fonctions clés** :
- 🔑 `get_access_token()` - Authentification
- 🔍 `get_job_details_by_rome()` - Récupère les offres
- 🎯 `match_soft_skills()` - Fait le matching des compétences
- 🛠️ `extract_skills_from_offers()` - Analyse les offres

### 3. `france_travail/rome4_api.py` - Référentiel des Métiers
**Rôle** : Gère la nomenclature des métiers (ROME).

**Utilité** :
- 📚 Base de données des métiers
- 🔎 Recherche par mot-clé
- 🔗 Conversion intitulé ↔ code ROME

### 🔄 Flux de Données
1. L'utilisateur envoie une requête (ex: matching de compétences)
2. `app.py` valide et route la requête
3. `alternative_client.py` appelle l'API France Travail
4. Les données sont traitées et analysées
5. Une réponse structurée est renvoyée

### 📊 Points Forts
- Architecture modulaire
- Gestion des erreurs robuste
- Code documenté
- Facile à étendre

## Installation

### Option 1 : Installation via pip (recommandé)

```bash
# Créer un environnement virtuel (recommandé)
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install requests python-dotenv

# Cloner le dépôt
git clone https://github.com/douuvid/Api_Final.git
cd Api_Final
```

## ⚙️ Configuration

1. Créer un fichier `.env` à la racine :
   ```env
   # France Travail API Credentials
   FRANCE_TRAVAIL_CLIENT_ID=votre_client_id
   FRANCE_TRAVAIL_CLIENT_SECRET=votre_client_secret
   
   # Paramètres du serveur
   DEBUG=True
   PORT=5000
   ```

2. Obtenez vos identifiants sur [France Travail Dev](https://www.emploi-store-dev.fr/)

## 🚀 Lancement du serveur

```bash
python app.py
```

Le serveur sera accessible sur : http://localhost:5000

## 🌐 API Endpoints

### 1. Recherche d'offres
```
GET /api/search_jobs?q=serveur&location=75056&max_results=10
```

### 2. Détails d'un métier
```
GET /api/job_details/G1603
```

### 3. Matching de compétences
```
POST /api/match_skills
{
    "rome_code": "G1603",
    "skills": ["accueil", "service", "hygiène"]
}
```

### 4. Offres à Paris
```
GET /api/paris_jobs/serveur
```

## 💡 Exemples d'utilisation

### Recherche d'offres
```bash
curl "http://localhost:5000/api/search_jobs?q=serveur&max_results=5"
```

### Matching de compétences
```bash
curl -X POST http://localhost:5000/api/match_skills \
  -H "Content-Type: application/json" \
  -d '{
    "rome_code": "G1603",
    "skills": ["accueil", "service", "hygiène"]
  }'
```

## 🛠️ Structure du projet

```
.
├── app.py                 # Serveur Flask principal
├── france_travail/
│   ├── __init__.py
│   ├── alternative_client.py  # Client API France Travail
│   └── rome4_api.py          # Client ROME 4.0
├── .env.example           # Exemple de configuration
└── requirements.txt       # Dépendances
```

## 🔍 Comment ça marche ?

1. Le serveur utilise l'API officielle France Travail
2. Les requêtes sont authentifiées avec OAuth2
3. Les compétences sont analysées avec des algorithmes de similarité
4. Les résultats sont retournés en JSON

## 🚨 Dépannage

### Erreurs courantes
- **401 Unauthorized** : Vérifiez vos identifiants API
- **429 Too Many Requests** : Attendez avant de réessayer
- **500 Server Error** : Consultez les logs du serveur

### Logs de débogage
Activez les logs détaillés :
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 🤝 Contribution

1. Forkez le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos modifications (`git commit -m 'Add some AmazingFeature'`)
4. Poussez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📄 Licence

Distribué sous licence MIT. Voir `LICENSE` pour plus d'informations.

---

Développé avec ❤️ par [Votre Nom] - [@votretwitter](https://twitter.com/votretwitter)

[Lien du projet](https://github.com/douuvid/Api_Final)

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

## Exemples d'utilisation

### 1. Recherche d'offres d'emploi

```python
from france_travail.alternative_client import FranceTravailAlternativeAPI

# Initialisation du client
api = FranceTravailAlternativeAPI(
    client_id="votre_client_id",
    client_secret="votre_client_secret"
)

# Obtenir les détails d'un métier par code ROME (ex: M1805 pour développeur)
job_details = api.get_job_details_by_rome("M1805")
print(f"Détails du métier: {job_details}")
```

### 2. Matching de compétences

```python
# Compétences de l'utilisateur
mes_competences = ["python", "travail d'équipe", "javascript", "communication"]

# Faire correspondre avec un métier
resultat = api.match_soft_skills("M1805", mes_competences)

print(f"Score de correspondance: {resultat['match_score']*100}%")
print(f"Compétences correspondantes: {resultat['matches']}")
print(f"Compétences manquantes: {resultat['missing_skills']}")
```

### 3. Extraire les compétences d'offres d'emploi

```python
# Récupérer des offres d'emploi
offres = api.get_job_details_by_rome("M1805")['offers_sample']

# Extraire les compétences des offres
competences = api.extract_skills_from_offers(offres)
print(f"Compétences requises: {competences}")
    print("\nCompétences à développer:")
    for comp in resultats.get('missing_skills', []):
        print(f"- {comp}")
```

## Fonctionnalités principales

### 1. Client Alternatif (`FranceTravailAlternativeAPI`)

- `get_job_details_by_rome(rome_code)` : Récupère les détails d'un métier par son code ROME
- `match_soft_skills(rome_code, user_skills)` : Fait correspondre les compétences utilisateur avec un métier
- `extract_skills_from_offers(offers)` : Extrait les compétences clés d'une liste d'offres
- `_similarity_score(str1, str2)` : Calcule la similarité entre deux chaînes

### 2. Client ROME 4.0 (`FranceTravailROME4API`)
- Accès aux référentiels ROME 4.0
- Récupération des fiches métiers détaillées
- Gestion de l'authentification OAuth2

## Dépannage

### Erreurs courantes

1. **Erreur 401** : Vérifiez vos identifiants API
2. **Erreur 206** : Réponse partielle, le traitement se fait normalement
3. **Erreur 429** : Trop de requêtes, attendez avant de réessayer

### Journaux de débogage

Activez les logs détaillés avec :

```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Problèmes courants
- `400 Bad Request` : Vérifiez la validité des paramètres de recherche
- `401 Unauthorized` : Votre token a peut-être expiré, réauthentifiez-vous
- `429 Too Many Requests` : Vous avez dépassé la limite de requêtes, attendez avant de réessayer

## Contribution

Les contributions sont les bienvenues ! Voici comment contribuer :

1. Forkez le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/ma-fonctionnalite`)
3. Committez vos modifications (`git commit -m 'Ajouter une fonctionnalité'`)
4. Poussez vers la branche (`git push origin feature/ma-fonctionnalite`)
5. Ouvrez une Pull Request

## Licence

Distribué sous licence MIT. Voir `LICENSE` pour plus d'informations.

## Contact

Votre Nom - [@votretwitter](https://twitter.com/votretwitter)

Lien du projet : [https://github.com/douuvid/Api_Final](https://github.com/douuvid/Api_Final)

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

Développé avec ❤️ pour faciliter l'accès aux offres d'emploi de France Travail.
