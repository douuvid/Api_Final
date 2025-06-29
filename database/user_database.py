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
        """Crée les tables et s'assure que le schéma de la base de données est à jour."""
        # --- Gestion de la table 'users' ---
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            search_query VARCHAR(255),
            contract_type VARCHAR(100),
            location VARCHAR(255),
            cv_path VARCHAR(255),
            lm_path VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        logger.info("Vérification de la table 'users'...")
        self._execute_query(create_users_table)
        
        # Migrations simples pour la table 'users'
        logger.info("Mise à jour du schéma de la table 'users' si nécessaire...")
        self._execute_query("ALTER TABLE users ADD COLUMN IF NOT EXISTS cv_path VARCHAR(255);")
        self._execute_query("ALTER TABLE users ADD COLUMN IF NOT EXISTS lm_path VARCHAR(255);")
        self._execute_query("ALTER TABLE users ADD COLUMN IF NOT EXISTS search_query VARCHAR(255);")
        self._execute_query("ALTER TABLE users ADD COLUMN IF NOT EXISTS contract_type VARCHAR(100);")
        self._execute_query("ALTER TABLE users ADD COLUMN IF NOT EXISTS location VARCHAR(255);")
        logger.info("✅ Table 'users' prête et à jour.")

        # --- Gestion de la table 'job_applications' ---
        logger.info("Vérification de la table 'job_applications'...")
        create_applications_table = """
        CREATE TABLE IF NOT EXISTS job_applications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            offer_url VARCHAR(2048) NOT NULL,
            title VARCHAR(255),
            company VARCHAR(255),
            location VARCHAR(255),
            description TEXT,
            status VARCHAR(100),
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, offer_url)
        );
        """
        self._execute_query(create_applications_table)

        # Migrations pour la table 'job_applications'
        self._execute_query("ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS title VARCHAR(255);")
        self._execute_query("ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS company VARCHAR(255);")
        self._execute_query("ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS location VARCHAR(255);")
        self._execute_query("ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS description TEXT;")
        self._execute_query("ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS status VARCHAR(100);")
        logger.info("✅ Table 'job_applications' prête et à jour.")

    def get_user_by_email(self, email: str):
        """Récupère un utilisateur par son email."""
        query = "SELECT * FROM users WHERE email = %s"
        return self._execute_query(query, (email,), fetch='one')

    def create_user(self, user_data: dict, hashed_password: str):
        """Crée un nouvel utilisateur."""
        query = """
        INSERT INTO users (email, hashed_password, first_name, last_name, search_query, contract_type, location)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
        """
        params = (
            user_data['email'],
            hashed_password,
            user_data['first_name'],
            user_data['last_name'],
            user_data.get('search_query'),
            user_data.get('contract_type'),
            user_data.get('location')
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

    def record_application(self, user_id: int, offer_details: dict):
        """Enregistre une candidature pour un utilisateur."""
        query = """
        INSERT INTO job_applications (user_id, offer_url, title, company, location, description, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id, offer_url) DO UPDATE SET
            title = EXCLUDED.title,
            company = EXCLUDED.company,
            location = EXCLUDED.location,
            description = EXCLUDED.description,
            status = EXCLUDED.status,
            applied_at = CURRENT_TIMESTAMP;
        """
        params = (
            user_id,
            offer_details.get('Lien'),
            offer_details.get('Titre'),
            offer_details.get('Entreprise'),
            offer_details.get('Lieu'),
            offer_details.get('Description'),
            offer_details.get('Statut')
        )
        try:
            self._execute_query(query, params)
            logger.info(f"Candidature enregistrée/mise à jour pour l'utilisateur {user_id} à l'offre {offer_details.get('Lien')}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de la candidature : {e}")
            return False

    def get_user_applications(self, user_id: int):
        """Récupère toutes les candidatures pour un utilisateur donné."""
        query = "SELECT title, company, location, description, offer_url, status, applied_at FROM job_applications WHERE user_id = %s ORDER BY applied_at DESC;"
        return self._execute_query(query, (user_id,), fetch='all')

    def check_if_applied(self, user_id: int, offer_url: str) -> bool:
        """Vérifie si un utilisateur a déjà postulé à une offre."""
        query = "SELECT EXISTS(SELECT 1 FROM job_applications WHERE user_id = %s AND offer_url = %s);"
        result = self._execute_query(query, (user_id, offer_url), fetch='one')
        return result['exists'] if result else False

    def reset_user_applications(self, user_id: int):
        """Supprime toutes les candidatures pour un user_id donné."""
        logger.warning(f"⚠️  Réinitialisation des candidatures pour l'utilisateur ID {user_id}.")
        try:
            query = "DELETE FROM job_applications WHERE user_id = %s;"
            self._execute_query(query, (user_id,))
            self.conn.commit()
            logger.info(f"✅ Toutes les candidatures pour l'utilisateur ID {user_id} ont été supprimées.")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur lors de la réinitialisation des candidatures pour l'utilisateur {user_id}: {e}")
            return False

    def update_user_prefs(self, user_id, prefs_data):
        """Met à jour les préférences d'un utilisateur (search_query, location, etc.)."""
        if not prefs_data:
            logger.warning("Aucune préférence à mettre à jour n'a été fournie.")
            return False

        # Construire dynamiquement la requête SQL
        set_clauses = [f'"{key}" = %s' for key in prefs_data.keys()]
        query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = %s"
        
        values = list(prefs_data.values()) + [user_id]

        try:
            self._execute_query(query, tuple(values))
            logger.info(f"Préférences mises à jour pour l'utilisateur ID {user_id}.")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des préférences pour l'utilisateur ID {user_id}: {e}")
            return False

    def reset_job_applications_table(self):
        """Supprime et recrée la table 'job_applications' pour une réinitialisation propre."""
        logger.warning("⚠️  Réinitialisation de la table 'job_applications'. Toutes les données de candidatures seront perdues.")
        try:
            self._execute_query("DROP TABLE IF EXISTS job_applications;")
            logger.info("Ancienne table 'job_applications' supprimée.")
            self.create_tables() # Recrée les tables avec le bon schéma
            logger.info("✅ Table 'job_applications' réinitialisée avec succès.")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur lors de la réinitialisation de la table : {e}")
            return False

    def update_user_preferences(self, user_id: int, search_query: str = None, contract_type: str = None, location: str = None):
        """Met à jour les préférences de recherche pour un utilisateur."""
        updates = []
        params = []
        if search_query is not None:
            updates.append("search_query = %s")
            params.append(search_query)
        if contract_type is not None:
            updates.append("contract_type = %s")
            params.append(contract_type)
        if location is not None:
            updates.append("location = %s")
            params.append(location)

        if not updates:
            logger.info("Aucune préférence à mettre à jour.")
            return None

        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s RETURNING *;"
        params.append(user_id)
        
        logger.info(f"Mise à jour des préférences pour l'utilisateur ID {user_id}...")
        return self._execute_query(query, tuple(params), fetch='one')
