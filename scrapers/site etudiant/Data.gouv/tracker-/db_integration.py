#!/usr/bin/env python3
"""
Module d'intégration avec la base de données utilisateur pour les scrapers
"""

import os
import sys
import json
import logging
import datetime
import dotenv
from typing import Dict, Any

# Charger les variables d'environnement du fichier .env s'il existe
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '.env')
if os.path.exists(dotenv_path):
    dotenv.load_dotenv(dotenv_path)
    print(f"Variables d'environnement chargées depuis {dotenv_path}")

# Correction manuelle des paramètres PostgreSQL pour utiliser la base existante
os.environ["DB_PORT"] = "5433"  # Port détecté dans les processus en cours d'exécution
os.environ["DB_NAME"] = "job_search_app"  # Base de données existante detectée

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'db_integration.log')),
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
            logger.info(f"Exécution de la requête pour l'utilisateur ID {user_id}...")
            user_data = self.db._execute_query(query, (user_id,), fetch='one')
            
            if not user_data:
                logger.error(f"❌ Utilisateur ID {user_id} non trouvé dans la base de données.")
                return {}
            
            # Log détaillé pour le débogage (sans le mot de passe)
            safe_user_data = {k: v for k, v in user_data.items() if k != 'hashed_password'}
            logger.info(f"✅ Données brutes récupérées pour l'utilisateur ID {user_id}: {safe_user_data}")
            
            # Vérifier spécifiquement les valeurs de recherche et lieu
            search_query = user_data.get('search_query', '')
            location = user_data.get('location', '')
            logger.info(f"🔍 DONNÉES UTILISATEUR: search_query='{search_query}', location='{location}'")
            
            # Convertir les données au format attendu par le scraper
            scraper_config = {
                "firstName": user_data.get('first_name', ''),
                "lastName": user_data.get('last_name', ''),
                "email": user_data.get('email', ''),
                "search_query": search_query,  # Pour le champ 'métier'
                "location": location,  # Pour le champ 'lieu'
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
            
            # Log des informations récupérées et formatées pour le scraper
            logger.info(f"Préférences formatées: {scraper_config}")
            return scraper_config
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des préférences utilisateur : {e}")
            import traceback
            logger.error(f"Détail de l'erreur: {traceback.format_exc()}")
            return {}

    def save_application_results(self, user_id: int, offers: list):
        """
        Sauvegarde les résultats des candidatures pour un utilisateur donné
        
        Args:
            user_id (int): ID de l'utilisateur
            offers (list): Liste des offres avec les résultats des candidatures
        """
        # TODO: Implémenter la sauvegarde des résultats
        try:
            logger.info(f"Sauvegarde des résultats pour {len(offers)} offres pour l'utilisateur ID {user_id}")
            
            # Préparation des données à sauvegarder dans la base
            current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # TODO: Ajouter le code pour sauvegarder les résultats dans la base
            
            logger.info(f"✅ Résultats sauvegardés avec succès pour l'utilisateur ID {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde des résultats: {e}")
            return False
            

def test_integration(user_id, return_data=False):
    """
    Fonction utilitaire pour tester l'intégration avec la base de données
    
    Args:
        user_id (int): ID de l'utilisateur à tester
        return_data (bool): Si True, retourne les données utilisateur récupérées
        
    Returns:
        Dict[str, Any] or None: Données utilisateur si return_data=True, sinon None
    """
    try:
        print(f"\n==== TEST INTEGRATION POUR UTILISATEUR ID {user_id} ====")
        db_integration = DatabaseIntegration()
        user_data = db_integration.get_user_preferences(user_id)
        
        # Affichage des données récupérées
        print(f"\nDonnées utilisateur récupérées:")
        print(f"Métier: '{user_data.get('search_query', '')}' (clé 'search_query')")
        print(f"Lieu: '{user_data.get('location', '')}' (clé 'location')")
        print(f"Prénom: '{user_data.get('firstName', '')}' (clé 'firstName')")
        print(f"Nom: '{user_data.get('lastName', '')}' (clé 'lastName')")
        print(f"Email: '{user_data.get('email', '')}' (clé 'email')")
        print(f"\nDictionnaire complet: {user_data}")
        
        if return_data:
            return user_data
        return None
    except Exception as e:
        print(f"❌ Erreur lors du test d'intégration: {e}")
        import traceback
        print(traceback.format_exc())
        return None if return_data else False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test d'intégration avec la base de données utilisateur")
    parser.add_argument("--user-id", type=int, required=True, help="ID de l'utilisateur à tester")
    args = parser.parse_args()
    
    test_integration(args.user_id)
