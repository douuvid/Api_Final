# Scraper pour alternance.emploi.gouv.fr

Ce scraper est conçu pour automatiser la recherche et la candidature aux offres d'alternance sur le site du gouvernement.

## Fonctionnalités

- [x] Recherche d'offres par mot-clé et localisation
- [x] Extraction et classification des offres d'emploi vs formations
- [x] Candidature automatisée
- [x] Remplissage automatique des formulaires de candidature
- [x] Upload automatique du CV
- [x] Option d'envoi automatisé des candidatures

## Nouvelle architecture

Le code a été réorganisé en plusieurs modules pour plus de maintenabilité :

- **alternance_gouv.py** : Script principal de scraping
- **postuler_functions.py** : Fonctions spécialisées pour la postulation
- **capture_functions.py** : Fonctions auxiliaires pour le débogage et la gestion des iframes

## Utilisation

### Exécution simple

```bash
python3 scrapers/site\ etudiant/alternance.emploi.gouv/alternance_gouv.py
```

### Options avancées

```bash
python3 scrapers/site\ etudiant/alternance.emploi.gouv/alternance_gouv.py --metier "Commercial" --ville "Paris" --postuler --remplir --cv "~/Documents/Mon_CV.pdf"
```

### Options disponibles

- **--email** : Email de l'utilisateur pour récupérer les données de profil
- **--metier** : Métier à rechercher (ex: 'Commercial')
- **--ville** : Ville ou localisation (ex: 'Paris')
- **--postuler / --no-postuler** : Activer/désactiver la postulation automatique
- **--remplir / --no-remplir** : Activer/désactiver le remplissage automatique du formulaire
- **--envoyer** : Envoyer automatiquement la candidature après remplissage
- **--pause** : Mettre en pause après l'ouverture du formulaire pour inspection manuelle
- **--cv** : Chemin vers le fichier CV (PDF ou DOCX)
- **--debug** : Activer le mode débogage avec plus de logs
