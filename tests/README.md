# Tests de l'API ROMEO

Ce répertoire contient les tests pour l'API ROMEO de France Travail.

## Configuration requise

1. Python 3.8 ou supérieur
2. Les dépendances du projet (`pip install -r requirements.txt`)
3. Un fichier `.env` configuré avec vos identifiants API

## Structure des tests

- `test_romeo.py` : Script principal de test qui vérifie toutes les fonctionnalités de l'API

## Comment exécuter les tests

### 1. Configuration de l'environnement

Créez un fichier `.env` à la racine du projet avec vos identifiants :

```bash
# API ROMEO (Entreprises)
ROMEO_CLIENT_ID=votre_client_id
ROMEO_CLIENT_SECRET=votre_client_secret
```

### 2. Exécution des tests

Depuis la racine du projet, exécutez :

```bash
# Installer les dépendances si nécessaire
pip install -r requirements.txt

# Exécuter les tests
python -m tests.test_romeo
```

## Fonctionnalités testées

- [ ] Authentification OAuth2
- [ ] Récupération du statut de l'API
- [ ] Recherche d'entreprises
- [ ] Récupération des secteurs d'activité
- [ ] Récupération des formes juridiques
- [ ] Gestion du rate limiting
- [ ] Recherches spécifiques (SIRET, géolocalisation)

## Dépannage

### Erreur d'authentification

Si vous obtenez une erreur 401 :
1. Vérifiez que vos identifiants sont corrects
2. Assurez-vous que votre compte a les bonnes autorisations
3. Vérifiez que les variables d'environnement sont correctement chargées

### Problèmes de connexion

Si les tests échouent à cause de problèmes de connexion :
1. Vérifiez votre connexion Internet
2. Assurez-vous que l'API ROMEO est disponible
3. Vérifiez que vous n'avez pas dépassé vos quotas d'API

## Personnalisation

Vous pouvez modifier les paramètres de test dans le fichier `test_romeo.py` pour tester des cas spécifiques à votre utilisation.
