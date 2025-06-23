# Projet d'Intégration des API France Travail

Ce projet fournit un client Python, un outil en ligne de commande et une API web (basée sur FastAPI) pour interagir avec plusieurs API de France Travail. Il permet de rechercher des offres d'emploi, d'analyser la compatibilité d'un CV avec une offre, et d'identifier des entreprises à fort potentiel de recrutement.

## Architecture

Le projet est maintenant divisé en trois parties principales :
1.  **Clients API (`france_travail/`)**: La logique de bas niveau pour communiquer avec les API de France Travail.
2.  **Interface en Ligne de Commande (`cli.py`)**: Un outil pour utiliser les fonctionnalités directement depuis le terminal.
3.  **Serveur API (`api_server/`)**: Une API web moderne (FastAPI) qui expose les fonctionnalités via des endpoints HTTP.

---

## 1. Prérequis

-   Python 3.
-   Un fichier `.env` à la racine du projet contenant vos identifiants API :

    ```
    FRANCE_TRAVAIL_CLIENT_ID=VOTRE_CLIENT_ID
    FRANCE_TRAVAIL_CLIENT_SECRET=VOTRE_CLIENT_SECRET
    ```

---

## 2. Installation

1.  Clonez le projet sur votre machine.
2.  Ouvrez un terminal dans le dossier du projet et installez les dépendances :

    ```bash
    pip install -r requirements.txt
    ```

---

## 3. Utilisation

Vous pouvez interagir avec le projet de deux manières : via l'interface en ligne de commande ou via le serveur API.

### A. Interface en Ligne de Commande (`cli.py`)

C'est l'outil idéal pour des tests rapides ou des scripts.

**Syntaxe générale :**
```bash
python3 cli.py <commande> [arguments]
```

**Exemples :**

-   **Rechercher** un poste de "développeur python" :
    ```bash
    python3 cli.py search "développeur python"
    ```
-   **Analyser un CV** (`mon_cv.txt`) avec une offre (`194FPYN`) :
    ```bash
    python3 cli.py match data/mon_cv.txt 194FPYN
    ```
-   **Trouver "La Bonne Boite"** pour des développeurs (ROME M1805) près de Paris :
    ```bash
    python3 cli.py lbb --rome "M1805" --lat 48.8566 --lon 2.3522
    ```

### B. Serveur API (FastAPI)

C'est la méthode recommandée pour intégrer ces fonctionnalités dans une application web ou mobile.

**1. Lancement du serveur :**

Exécutez la commande suivante depuis la racine du projet :
```bash
uvicorn api_server.main:app --reload
```
Le serveur sera accessible à l'adresse `http://127.0.0.1:8000`.

**2. Documentation Interactive :**

Une fois le serveur lancé, ouvrez votre navigateur à l'adresse suivante pour accéder à une documentation complète et interactive de l'API :
[**http://127.0.0.1:8000/docs**](http://127.0.0.1:8000/docs)

Depuis cette page, vous pouvez tester tous les endpoints directement.

**3. Endpoints disponibles :**

*   `GET /search?keywords=...`: Recherche des offres d'emploi.
    *   Exemple : `http://127.0.0.1:8000/search?keywords=comptable`
*   `GET /details/{job_id}`: Récupère les détails d'une offre spécifique.
    *   Exemple : `http://127.0.0.1:8000/details/194FPYN`
*   `POST /match/{job_id}`: Calcule le score de compatibilité entre un CV et une offre. Le corps de la requête doit contenir le texte du CV au format JSON :
    ```json
    {
      "cv_text": "Le texte de votre CV ici..."
    }
    ```
