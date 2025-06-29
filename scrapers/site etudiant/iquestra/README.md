# iQuesta Scraper - Guide d'Utilisation

Ce projet automatise la recherche d'offres d'emploi sur iQuesta, postule aux offres et gère un historique complet des candidatures via une interface en ligne de commande (CLI) et une base de données PostgreSQL.

## Workflow Complet : de Zéro à la Candidature Automatisée

Voici la séquence complète pour configurer et lancer le scraper pour un nouvel utilisateur.

### Étape 1 : Installation et Configuration Initiale

1.  **Installation des dépendances :**
    ```bash
    # (Après avoir cloné le dépôt et créé un environnement virtuel)
    pip install -r requirements.txt
    ```

2.  **Configuration de l'environnement :**
    Créez un fichier `.env` à partir du modèle `example.env` et remplissez vos informations de base de données.

3.  **Initialisation de la base de données :**
    Cette commande crée les tables `users` et `job_applications`.
    ```bash
    python3 cli.py db init
    ```

### Étape 2 : Créer et Configurer un Utilisateur

1.  **Créer le profil utilisateur :**
    Enregistrez un nouvel utilisateur avec ses préférences de recherche.
    ```bash
    python3 cli.py user create --email "mon.email@example.com" --password "mon_mdp" --first-name "Jean" --last-name "Dupont" --search-query "Product Owner" --location "Ile de France" --contract-type "Alternance"
    ```

### Étape 3 : Lancer le Scraper

C'est la commande principale qui met à jour les documents de l'utilisateur et lance immédiatement le processus de scraping.

1.  **Réinitialiser l'historique (Optionnel mais recommandé pour les tests) :**
    Pour s'assurer que le scraper analyse toutes les offres disponibles.
    ```bash
    python3 cli.py user reset-apps --email "mon.email@example.com"
    ```

2.  **Mettre à jour les documents et lancer le scraper :**
    Fournissez les chemins vers le CV et la lettre de motivation. L'argument `--lancer-scraper` déclenche le scraping juste après la mise à jour.
    ```bash
    python3 cli.py user update-docs --email "mon.email@example.com" --cv-path "~/Documents/CV_Jean_Dupont.pdf" --lm-path "~/Documents/LM_Jean_Dupont.pdf" --lancer-scraper
    ```
Le terminal affichera en temps réel la progression du scraper.

### Étape 4 : Consulter les Résultats

Une fois le scraping terminé, vous pouvez générer un rapport CSV de toutes les candidatures envoyées.

```bash
python3 cli.py user download-report --email "mon.email@example.com"
```
Le rapport sera sauvegardé dans le dossier `reports/report_iquestra`.

## Commandes de Gestion Détaillées

Voici la liste de toutes les commandes disponibles pour une gestion plus fine.

### Mettre à jour les préférences d'un utilisateur

Si vous souhaitez changer le poste recherché, la localisation, etc., sans recréer l'utilisateur.
```bash
python3 cli.py user update-prefs --email "mon.email@example.com" --location "Lyon" --search-query "Chef de Projet Digital"
```

### Mettre à jour les documents (sans lancer le scraper)

Pour simplement mettre à jour le CV ou la LM dans la base de données.
```bash
python3 cli.py user update-docs --email "mon.email@example.com" --cv-path "~/Documents/Nouveau_CV.pdf" --lm-path "~/Documents/Nouvelle_LM.pdf"
```

### Réinitialiser l'historique des candidatures

Efface toutes les candidatures enregistrées pour un utilisateur.
```bash
python3 cli.py user reset-apps --email "mon.email@example.com"
```
