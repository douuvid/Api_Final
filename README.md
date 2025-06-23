# Projet d'Intégration des API France Travail

Ce projet fournit un client Python et un outil en ligne de commande pour interagir avec plusieurs API de France Travail. Il permet non seulement de rechercher des offres d'emploi, mais aussi d'analyser la compatibilité d'un CV avec une offre et d'identifier des entreprises à fort potentiel de recrutement.

## Fonctionnalités

*   **Recherche d'offres d'emploi** : Filtrez les offres par mots-clés, département, commune ou code ROME.
*   **Analyse de CV** : Calculez un score de compatibilité entre votre CV (formats PDF, DOCX, TXT) et une offre d'emploi spécifique.
*   **La Bonne Boite (LBB)** : Identifiez les entreprises les plus susceptibles de recruter prochainement, même sans offre publiée, pour des candidatures spontanées ciblées.

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

## 3. Utilisation en Ligne de Commande

L'application utilise des commandes distinctes pour chaque fonctionnalité.

### A. `search` : Rechercher des offres d'emploi

Utilisez la commande `search` pour trouver des offres d'emploi.

**Syntaxe :**
```bash
python app.py search [options]
```

**Exemples :**

-   Chercher un poste de "développeur python" dans le Rhône (69) :
    ```bash
    python app.py search --motsCles "développeur python" --departement "69"
    ```
-   Chercher des offres pour le code ROME "M1805" (Informatique et télécoms) :
    ```bash
    python app.py search --codeROME "M1805"
    ```

### B. `match` : Analyser un CV

Utilisez la commande `match` pour évaluer la compatibilité de votre CV avec une offre d'emploi.

**Syntaxe :**
```bash
python app.py match <chemin_vers_cv> <id_offre>
```

**Exemple :**
```bash
python app.py match ./mon_cv.pdf 1234567X
```

### C. `lbb` : Trouver "La Bonne Boite"

Utilisez la commande `lbb` pour identifier les entreprises à fort potentiel d'embauche pour des candidatures spontanées.

**À quoi ça sert ?**
L'API "La Bonne Boite" ne liste pas des offres publiées, mais **prédit les entreprises qui vont probablement recruter bientôt**. C'est un outil puissant pour envoyer des candidatures spontanées ciblées.

**Syntaxe :**
```bash
python app.py lbb --rome <code_rome> --lat <latitude> --lon <longitude> [options]
```

**Exemples :**

-   Trouver les entreprises susceptibles de recruter des développeurs (ROME M1805) près de Paris :
    ```bash
    python app.py lbb --rome "M1805" --lat 48.8566 --lon 2.3522
    ```
-   Recherche plus large (rayon de 25 km) :
    ```bash
    python app.py lbb --rome "M1805" --lat 48.8566 --lon 2.3522 --dist 25
    ```

---

## 4. Utilisation en tant que Serveur Web (Optionnel)

Le projet inclut également un serveur Flask simple pour exposer les fonctionnalités via une API web. Pour le lancer, exécutez le script sans arguments (note : cette fonctionnalité est actuellement désactivée par défaut au profit de l'interface en ligne de commande) :

```bash
# Pour réactiver le serveur, une modification du code dans app.py est nécessaire.
```

Les endpoints disponibles (si réactivés) sont :
-   `/api/search?params...`
-   `/api/job_details/<job_id>`

-   Pour chercher un poste de "vendeur" dans les Bouches-du-Rhône :
    ```bash
    python3 app.py --motsCles "vendeur" --departement 13
    ```

**Arguments disponibles :**
-   `--motsCles`: Le métier ou les compétences (obligatoire).
-   `--departement`: Le numéro du département.
-   `--commune`: Le code INSEE de la commune.
-   `--range`: La plage de résultats (ex: `0-10`). Par défaut, les 5 premières offres sont affichées.

### B. Lancement du Serveur Web

Si vous n'utilisez aucun argument, le script lancera un serveur web local.

**Commande :**
```bash
python3 app.py
```

Le serveur sera alors accessible à l'adresse `http://127.0.0.1:5000`.
