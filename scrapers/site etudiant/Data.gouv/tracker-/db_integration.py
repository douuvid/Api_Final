#!/usr/bin/env python3
"""
Module d'intégration avec la base de données utilisateur pour les scrapers
"""

import os
import sys
import json
import logging
import datetime
from typing import Dict, Any

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/db_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ajouter le chemin du projet principal pour pouvoir importer la classe UserDatabase
# Chemins possibles pour trouver le module database
paths_to_try = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')),  # /Users/davidravin/Desktop/Api_Final
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')),  # /Users/davidravin/Desktop
]

for path in paths_to_try:
    if os.path.exists(os.path.join(path, 'database', 'user_database.py')):
        root_path = path
        sys.path.insert(0, root_path)
        logger.info(f"Module UserDatabase trouvé dans: {root_path}")
        break
else:
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    sys.path.insert(0, root_path)
    logger.warning(f"Tentative de dernier recours avec: {root_path}")

logger.info(f"Ajout du chemin racine au sys.path: {root_path}")

try:
    from database.user_database import UserDatabase
    logger.info(f"Module UserDatabase importé avec succès depuis {root_path}")
except ImportError as e:
    logger.error(f"Erreur d'importation du module UserDatabase: {e}")
    logger.error(f"Chemin de recherche Python: {sys.path}")
    raise

class DatabaseIntegration:
    """
    Classe pour l'intégration entre la base de données utilisateur et le scraper
    """
    def __init__(self):
        """Initialise la connexion à la base de données."""
        try:
            self.db = UserDatabase()
            logger.info("✅ Connexion à la base de données utilisateur établie.")
        except Exception as e:
            logger.error(f"❌ Erreur de connexion à la base de données : {e}")
            raise

    def close(self):
        """Ferme la connexion à la base de données."""
        if hasattr(self, 'db') and self.db:
            self.db.close()
            logger.info("Connexion à la base de données fermée.")

    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Récupère les préférences de l'utilisateur depuis la base de données
        et les convertit au format attendu par le scraper.
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            Dict[str, Any]: Dictionnaire avec les préférences utilisateur pour le scraper
        """
        try:
            # Récupérer l'utilisateur complet pour avoir toutes les informations
            query = """
            SELECT * FROM users 
            WHERE id = %s
            """
            user_data = self.db._execute_query(query, (user_id,), fetch='one')
            
            if not user_data:
                logger.error(f"❌ Utilisateur ID {user_id} non trouvé dans la base de données.")
                return {}
            
            logger.info(f"✅ Informations utilisateur ID {user_id} récupérées avec succès.")
            
            # Convertir les données au format attendu par le scraper
            scraper_config = {
                "firstName": user_data.get('first_name', ''),
                "lastName": user_data.get('last_name', ''),
                "email": user_data.get('email', ''),
                "search_query": user_data.get('search_query', ''),  # Pour le champ 'métier'
                "location": user_data.get('location', ''),  # Pour le champ 'lieu'
                "contractTypes": user_data.get('contract_type', 'alternance'),
                "cvPath": user_data.get('cv_path', ''),
                "coverLetterPath": user_data.get('lm_path', ''),
                "settings": {
                    "delayBetweenApplications": 5,
                    "maxApplicationsPerSession": 10,
                    "autoFillForm": True,
                    "autoSendApplication": True,
                    "pauseBeforeSend": False,
                    "captureScreenshots": True
                }
            }
            
            # Log des informations récupérées (sans le mot de passe)
            logger.info(f"Préférences récupérées: métier='{scraper_config['search_query']}', lieu='{scraper_config['location']}'")
            return scraper_config
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des préférences utilisateur : {e}")
            return {}

    def save_application_results(self, user_id: int, offers: list):
        """
        Enregistre les résultats des candidatures dans la base de données
        
        Args:
            user_id (int): ID de l'utilisateur
            offers (list): Liste des offres traitées par le scraper
        """
        try:
            for offer in offers:
                offer_details = {
                    'Lien': offer.get('url', ''),
                    'Titre': offer.get('title', ''),
                    'Entreprise': offer.get('company', ''),
                    'Lieu': offer.get('location', ''),
                    'Description': offer.get('description', ''),
                    'Statut': offer.get('application_status', 'non_postulé')
                }
                
                self.db.record_application(user_id, offer_details)
            
            logger.info(f"✅ {len(offers)} candidatures enregistrées pour l'utilisateur ID {user_id}.")
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'enregistrement des candidatures : {e}")

# Fonction utilitaire pour tester l'intégration
def test_integration(user_id: int):
    """
    Fonction de test pour vérifier l'intégration avec la base de données
    
    Args:
        user_id (int): ID de l'utilisateur à tester
    """
    integration = DatabaseIntegration()
    try:
        user_prefs = integration.get_user_preferences(user_id)
        if user_prefs:
            print(f"\n🔍 Préférences pour l'utilisateur ID {user_id}:")
            print(json.dumps(user_prefs, indent=2))
        else:
            print(f"\n❌ Aucune préférence trouvée pour l'utilisateur ID {user_id}.")
    finally:
        integration.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test d'intégration avec la base de données utilisateur")
    parser.add_argument("--user-id", type=int, required=True, help="ID de l'utilisateur à tester")
    args = parser.parse_args()
    
    test_integration(args.user_id)
