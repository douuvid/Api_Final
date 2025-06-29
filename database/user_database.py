import os
import logging
import pg8000.dbapi
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

class UserDatabase:
    """
    Gère la connexion et les opérations avec la base de données PostgreSQL
    pour les utilisateurs.
    """
    def __init__(self):
        """Initialise la connexion à la base de données."""
        self.conn = None
        try:
            logger.info("Tentative de connexion à la base de données...")
            self.conn = pg8000.dbapi.connect(
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT")),
                database=os.getenv("DB_NAME")
            )
            logger.info("✅ Connexion à la base de données réussie.")
            self.create_tables()
        except Exception as e:
            logger.error(f"❌ Erreur de connexion à la base de données : {e}")
            raise

    def close(self):
        """Ferme la connexion à la base de données."""
        if self.conn:
            self.conn.close()
            logger.info("Connexion à la base de données fermée.")

    def _execute_query(self, query, params=None, fetch=None):
        """
        Exécute une requête SQL de manière sécurisée.
        
        Args:
            query (str): La requête SQL à exécuter.
            params (tuple, optional): Les paramètres pour la requête.
            fetch (str, optional): Le type de récupération ('one' ou 'all').

        Returns:
            Le résultat de la requête si fetch est spécifié.
        """
        cursor = None
        result = None
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params or ())
            if fetch == 'one':
                desc = cursor.description
                row = cursor.fetchone()
                if row and desc:
                    # Convertir la ligne en dictionnaire
                    result = {col[0]: val for col, val in zip(desc, row)}
            elif fetch == 'all':
                desc = cursor.description
                rows = cursor.fetchall()
                if rows and desc:
                    # Convertir les lignes en liste de dictionnaires
                    result = [{col[0]: val for col, val in zip(desc, row)} for row in rows]
            self.conn.commit()
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la requête : {e}")
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
        return result

    def create_tables(self):
        """Crée la table des utilisateurs si elle n'existe pas."""
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            cv_path VARCHAR(255),
            lm_path VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        logger.info("Vérification de la table 'users'...")
        self._execute_query(create_users_table)
        
        # S'assurer que les colonnes pour les documents existent (migration simple)
        logger.info("Vérification des colonnes 'cv_path' et 'lm_path'...")
        alter_cv_query = "ALTER TABLE users ADD COLUMN IF NOT EXISTS cv_path VARCHAR(255);"
        alter_lm_query = "ALTER TABLE users ADD COLUMN IF NOT EXISTS lm_path VARCHAR(255);"
        self._execute_query(alter_cv_query)
        self._execute_query(alter_lm_query)
        
        logger.info("✅ Table 'users' prête et à jour.")

    def get_user_by_email(self, email: str):
        """Récupère un utilisateur par son email."""
        query = "SELECT * FROM users WHERE email = %s"
        return self._execute_query(query, (email,), fetch='one')

    def create_user(self, user_data: dict, hashed_password: str):
        """Crée un nouvel utilisateur."""
        query = """
        INSERT INTO users (email, hashed_password, first_name, last_name)
        VALUES (%s, %s, %s, %s)
        RETURNING *;
        """
        params = (
            user_data['email'],
            hashed_password,
            user_data['first_name'],
            user_data['last_name']
        )
        return self._execute_query(query, params, fetch='one')

    def update_user_document_paths(self, user_id: int, cv_path: str = None, lm_path: str = None):
        """Met à jour les chemins des documents pour un utilisateur."""
        updates = []
        params = []
        if cv_path is not None:
            updates.append("cv_path = %s")
            params.append(cv_path)
        if lm_path is not None:
            updates.append("lm_path = %s")
            params.append(lm_path)

        if not updates:
            logger.info("Aucun chemin de document à mettre à jour.")
            return None

        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s RETURNING *;"
        params.append(user_id)
        
        logger.info(f"Mise à jour des documents pour l'utilisateur ID {user_id}...")
        return self._execute_query(query, tuple(params), fetch='one')
