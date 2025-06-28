# Projet d'Automatisation de Candidatures

Ce projet contient une collection de scrapers conçus pour automatiser le processus de recherche et de candidature à des offres d'emploi sur différentes plateformes.

## Scrapers Disponibles

- **France Travail** : Scraper complet pour rechercher et postuler automatiquement aux offres.
- **iQuesta** : Scraper pour la recherche, la sélection d'offres et le remplissage automatique du formulaire de candidature.

## Prérequis

- Python 3.x
- Google Chrome

## Installation

1.  **Clonez le dépôt :**
    ```bash
    git clone <URL_DU_DEPOT>
    cd Api_Final
    ```

2.  **Installez les dépendances Python :**
    Il est recommandé d'utiliser un environnement virtuel.
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Sur macOS/Linux
    # venv\Scripts\activate    # Sur Windows
    
    pip install -r requirements.txt
    ```

## Configuration

Ce projet utilise un fichier `.env` pour gérer les informations sensibles (identifiants, informations personnelles) de manière sécurisée. **Ce fichier n'est pas et ne doit pas être suivi par Git.**

1.  **Créez un fichier `.env`** à la racine du projet.

2.  **Ajoutez les variables d'environnement** nécessaires pour chaque scraper. Copiez, collez et remplissez le modèle ci-dessous :

    ```env
    #--- Identifiants France Travail ---
    FRANCE_TRAVAIL_IDENTIFIANT="votre_identifiant_francetravail"
    FRANCE_TRAVAIL_MOT_DE_PASSE="votre_mot_de_passe"
    
    #--- Informations pour iQuesta ---
    IQUESTA_EMAIL="votre_email@example.com"
    IQUESTA_PRENOM="VotrePrénom"
    IQUESTA_NOM="VotreNom"
    IQUESTA_MESSAGE="Message de candidature par défaut."
    IQUESTA_CV_PATH="/chemin/absolu/vers/votre/cv.pdf"
    IQUESTA_LM_PATH="/chemin/absolu/vers/votre/lm.pdf" # Optionnel
    ```

## Utilisation

Pour lancer un scraper, exécutez le script correspondant depuis la racine du projet.

-   **Pour lancer le scraper iQuesta :**

    ```bash
    python "scrapers/site etudiant/iquestra.py"
    ```
    *Note : Par défaut, le scraper iQuesta remplit le formulaire mais ne clique pas sur "Postuler". Pour activer la soumission automatique, vous devez décommenter les lignes appropriées dans le script `iquestra.py`.*

-   **Pour lancer le scraper France Travail (exemple) :**

    Le script `france_travail_original.py` contient la logique. Assurez-vous de l'adapter ou de l'appeler depuis un script principal si nécessaire.
