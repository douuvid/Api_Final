# Projet d'Intégration API France Travail

Ce projet permet de rechercher des offres d'emploi en utilisant l'API de France Travail (anciennement Pôle Emploi).

Il peut être utilisé de deux manières :
1.  En ligne de commande (CLI) pour des recherches rapides dans le terminal.
2.  En tant que serveur web pour des requêtes via un navigateur ou une autre application.

---

## 1. Prérequis

-   Python 3 installé sur votre machine.
-   Un fichier `.env` à la racine du projet contenant vos identifiants API :

    ```
    FRANCE_TRAVAIL_CLIENT_ID=VOTRE_CLIENT_ID
    FRANCE_TRAVAIL_CLIENT_SECRET=VOTRE_CLIENT_SECRET
    ```

---

## 2. Installation

Ouvrez un terminal dans le dossier du projet et installez les dépendances nécessaires avec la commande suivante :

```bash
python3 -m pip install -r requirements.txt
```

---

## 3. Utilisation

### A. Recherche en Ligne de Commande (CLI)

C'est le mode le plus simple pour trouver des offres rapidement.

**Syntaxe :**
```bash
python3 app.py --motsCles "<le métier>" --departement <numéro_département>
```

**Exemples :**

-   Pour chercher un poste de "Product Owner" à Paris :
    ```bash
    python3 app.py --motsCles "product owner" --departement 75
    ```

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
