#!/bin/bash

# Ce script lance le scraper iQuesta avec l'email fourni
# Usage: ./launch_iquestra.sh email_utilisateur

# Définir le dossier du scraper (nouveau chemin vers iquesta_automation)
SCRAPER_PATH="/Users/davidravin/Desktop/Api_Final/scrapers/site etudiant/Iquestra/iquesta_automation"

# Créer le dossier de logs si nécessaire
mkdir -p "$SCRAPER_PATH/logs"

# Récupérer l'email de l'utilisateur
USER_EMAIL=$1

# Afficher les informations de démarrage
echo "========== LANCEMENT SCRAPER IQUESTRA =========="
echo "Date: $(date)"
echo "Email utilisateur: $USER_EMAIL"
echo "=============================================="

# Activer l'environnement virtuel si présent
if [ -d "/Users/davidravin/Desktop/Api_Final/.venv" ]; then
    source "/Users/davidravin/Desktop/Api_Final/.venv/bin/activate"
elif [ -d "/Users/davidravin/Desktop/Api_Final/venv" ]; then
    source "/Users/davidravin/Desktop/Api_Final/venv/bin/activate"
fi

# Aller dans le répertoire du scraper
cd "$SCRAPER_PATH"

# Lancer le script Python avec l'email fourni (nouveau script iquesta_scraper.py)
python3 scraper/iquesta_scraper.py --email "$USER_EMAIL" &

echo "Scraper iQuesta lancé avec succès !"
exit 0
