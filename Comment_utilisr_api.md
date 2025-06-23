# Guide d'utilisation de l'outil France Travail

Ce document explique comment utiliser les différentes fonctionnalités de cet outil en ligne de commande pour interagir avec les API de France Travail.

---

### 1. Rechercher des offres d'emploi (`search`)

Cette commande vous permet de rechercher des offres d'emploi en fonction d'un mot-clé.

**Syntaxe :**
```bash
python app.py search "<mot-clé>" [--limit <nombre>]
```

- `<mot-clé>` : Le métier ou la compétence que vous recherchez (ex: "développeur web", "boulanger"). Mettez-le entre guillemets.
- `[--limit <nombre>]` : (Optionnel) Le nombre maximum de résultats à afficher. Par défaut, c'est 5.

**Exemple :**
```bash
# Chercher les 3 dernières offres pour "vendeur"
python app.py search "vendeur" --limit 3
```

---

### 2. Analyser la compatibilité CV/Offre (`match`)

C'est la fonctionnalité la plus avancée. Elle prend un fichier CV et un ID d'offre d'emploi, puis analyse la compatibilité en se basant sur les compétences "soft skills" requises.

**Syntaxe :**
```bash
python app.py match <chemin/vers/votre/cv.txt> <ID_de_l'offre>
```

**Comment l'utiliser :**
1.  **Trouvez un ID d'offre** en utilisant la commande `search`.
2.  **Préparez votre CV** dans un fichier texte simple (`.txt`).
3.  **Lancez l'analyse**.

**Exemple :**
```bash
# Analyser mon_cv.txt par rapport à l'offre d'ID 194GWWX
python app.py match mon_cv.txt 194GWWX
```

---

### 3. Trouver des entreprises qui recrutent (`lbb`)

Cette commande utilise l'API "La Bonne Boîte" pour trouver des entreprises susceptibles de recruter dans un domaine, même si elles n'ont pas posté d'offres.

**Syntaxe :**
```bash
python app.py lbb <code_ROME> <latitude> <longitude> [--distance <km>]
```

- `<code_ROME>` : Le code du métier (vous pouvez le trouver via une recherche d'offre).
- `<latitude>` et `<longitude>` : Vos coordonnées géographiques.
- `[--distance <km>]` : (Optionnel) Le rayon de recherche en kilomètres. Par défaut, c'est 10.

**Exemple :**
```bash
# Trouver des entreprises qui recrutent des développeurs (M1805) près de Paris
python app.py lbb M1805 48.85 2.35 --distance 20
```

---

### 4. Prédire un code ROME (`romeo`)

Si vous avez un intitulé de poste et que vous voulez trouver le code ROME officiel correspondant, utilisez cette commande.

**Syntaxe :**
```bash
python app.py romeo "<intitulé_du_poste>" [--nb <nombre>]
```

**Exemple :**
```bash
# Trouver le code ROME pour "Responsable marketing digital"
python app.py romeo "Responsable marketing digital" --nb 5
```

---

### 5. Consulter les contextes de travail (API ROME V4.0)

Cette commande permet d'interagir avec le référentiel des situations de travail pour obtenir des détails sur les conditions, lieux, horaires, etc.

**Note :** Cette fonctionnalité nécessite que votre application soit abonnée au produit API "ROME V4.0 - Situations de travail" dans votre espace développeur France Travail.

#### Lister tous les contextes

Pour obtenir la liste complète de tous les contextes de travail disponibles.

```bash
python app.py contexte list
```

Vous pouvez choisir de ne retourner que certains champs :
```bash
python app.py contexte list --champs "libelle,code"
```

#### Obtenir les détails d'un contexte spécifique

Pour voir les informations d'un contexte précis grâce à son code.

```bash
python app.py contexte get 403091
```

#### Vérifier la version du référentiel

Pour connaître la version actuelle du référentiel ROME utilisé par l'API.

```bash
python app.py contexte version
```
