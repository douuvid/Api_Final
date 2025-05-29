"""
Configuration de la base de données PostgreSQL pour l'application de recherche d'emploi.
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

class DatabaseConfig:
    """Configuration de la base de données PostgreSQL"""
    
    # Paramètres de connexion avec valeurs par défaut
    HOST = os.getenv('DB_HOST', 'localhost')
    PORT = int(os.getenv('DB_PORT', 5432))
    DATABASE = os.getenv('DB_NAME', 'job_search_app')
    USER = os.getenv('DB_USER', 'postgres')
    PASSWORD = os.getenv('DB_PASSWORD', 'your_password')
    
    # Autres paramètres
    MIN_CONN = 1
    MAX_CONN = 10
    
    @classmethod
    def get_connection_string(cls):
        """Retourne la chaîne de connexion à la base de données"""
        return f"""
            dbname='{cls.DATABASE}'
            user='{cls.USER}'
            password='{cls.PASSWORD}'
            host='{cls.HOST}'
            port='{cls.PORT}'
        """
