"""
Tests pour le module user_database.py
"""
import os
import sys
import unittest
import psycopg2
from datetime import datetime, timedelta
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from database import UserDatabase, DatabaseConfig
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def create_test_database():
    """Crée la base de données de test si elle n'existe pas"""
    try:
        # Se connecter à la base de données postgres par défaut
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database='postgres',
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'your_password'),
            port=int(os.getenv('DB_PORT', 5432))
        )
        conn.autocommit = True
        
        with conn.cursor() as cursor:
            # Vérifier si la base de données existe déjà
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'test_job_search_app'")
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute('CREATE DATABASE test_job_search_app')
                print("Base de données de test créée avec succès")
            else:
                print("Base de données de test existe déjà")
                
    except Exception as e:
        print(f"Erreur lors de la création de la base de test: {e}")
        raise
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# Créer la base de données de test avant d'exécuter les tests
create_test_database()

class TestUserDatabase(unittest.TestCase):    
    @classmethod
    def setUpClass(cls):
        """Configuration initiale pour tous les tests"""
        # Utiliser une base de données de test
        cls.db = UserDatabase(
            host=os.getenv('DB_HOST', 'localhost'),
            database='test_job_search_app',
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'your_password'),
            port=int(os.getenv('DB_PORT', 5432))
        )
        
        # Se connecter à la base de données
        if not cls.db.connect():
            raise Exception("Impossible de se connecter à la base de données de test")
        
        # Créer les tables
        cls.db.create_tables()
    
    def setUp(self):
        """Avant chaque test"""
        # S'assurer qu'on est connecté
        if not self.db.conn or self.db.conn.closed != 0:
            self.db.connect()
        
        # Nettoyer les tables avant chaque test
        self.cleanup_tables()
    
    def cleanup_tables(self):
        """Vide toutes les tables de la base de test"""
        tables = [
            'user_skills', 'skills', 'user_profiles', 'user_sessions',
            'user_preferences', 'job_applications', 'favorite_jobs',
            'saved_searches', 'user_educations', 'user_experiences', 'users'
        ]
        
        try:
            with self.db.conn.cursor() as cursor:
                # Désactiver temporairement les contraintes
                cursor.execute("SET session_replication_role = 'replica';")
                
                # Vider les tables
                for table in tables:
                    cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
                
                # Réactiver les contraintes
                cursor.execute("SET session_replication_role = 'origin';")
                self.db.conn.commit()
                
        except Exception as e:
            print(f"Erreur lors du nettoyage des tables: {e}")
            self.db.conn.rollback()
    
    def test_create_user(self):
        """Teste la création d'un utilisateur"""
        # Données de test
        user_data = {
            'email': 'test@example.com',
            'password': 'Test123!',
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'phone': '+33612345678',
            'date_of_birth': '1990-01-01',
            'gender': 'M'
        }
        
        # Créer l'utilisateur
        user_id, verification_token = self.db.create_user(user_data)
        
        # Vérifier que l'utilisateur a bien été créé
        self.assertIsNotNone(user_id)
        self.assertIsNotNone(verification_token)
        
        # Vérifier que le token de vérification est bien stocké
        with self.db.conn.cursor() as cursor:
            cursor.execute("SELECT verification_token FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            self.assertEqual(result[0], verification_token)
    
    def test_duplicate_email(self):
        """Teste qu'on ne peut pas créer deux utilisateurs avec le même email"""
        user_data = {
            'email': 'duplicate@example.com',
            'password': 'Test123!',
            'first_name': 'Jean',
            'last_name': 'Dupont'
        }
        
        # Premier utilisateur - doit fonctionner
        self.db.create_user(user_data)
        
        # Deuxième utilisateur avec le même email - doit échouer
        with self.assertRaises(ValueError):
            self.db.create_user(user_data)
    
    def test_authentication(self):
        """Teste l'authentification d'un utilisateur"""
        # Créer un utilisateur de test
        user_data = {
            'email': 'auth@test.com',
            'password': 'Auth123!',
            'first_name': 'Auth',
            'last_name': 'Test'
        }
        user_id, _ = self.db.create_user(user_data)
        
        # Test d'authentification réussi
        user, message = self.db.authenticate_user('auth@test.com', 'Auth123!')
        self.assertIsNotNone(user)
        self.assertEqual(user['email'], 'auth@test.com')
        self.assertEqual(message, "Authentification réussie")
        
        # Test avec mauvais mot de passe
        user, message = self.db.authenticate_user('auth@test.com', 'WrongPass')
        self.assertIsNone(user)
        self.assertEqual(message, "Email ou mot de passe incorrect")
        
        # Vérifier que le compteur de tentatives a été incrémenté
        with self.db.conn.cursor() as cursor:
            cursor.execute("SELECT login_attempts FROM users WHERE id = %s", (user_id,))
            attempts = cursor.fetchone()[0]
            self.assertEqual(attempts, 1)
    
    def test_account_lockout(self):
        """Teste le verrouillage du compte après plusieurs échecs"""
        # Créer un utilisateur de test
        user_data = {
            'email': 'lockout@test.com',
            'password': 'Lock123!',
            'first_name': 'Lock',
            'last_name': 'Out'
        }
        self.db.create_user(user_data)
        
        # Tenter de se connecter avec un mauvais mot de passe 5 fois
        for _ in range(5):
            user, message = self.db.authenticate_user('lockout@test.com', 'WrongPass')
        
        # La 6ème tentative devrait échouer avec un message de verrouillage
        user, message = self.db.authenticate_user('lockout@test.com', 'Lock123!')
        self.assertIsNone(user)
        self.assertIn("Compte verrouillé", message)
    
    def test_add_skill(self):
        """Teste l'ajout d'une compétence à un utilisateur"""
        # Créer un utilisateur de test
        user_data = {
            'email': 'skills@test.com',
            'password': 'Skills123!',
            'first_name': 'Skill',
            'last_name': 'Test'
        }
        user_id, _ = self.db.create_user(user_data)
        
        # Ajouter une compétence
        result = self.db.add_user_skill(
            user_id=user_id,
            skill_name='Python',
            level='Advanced',
            years_experience=5,
            is_primary=True
        )
        
        self.assertTrue(result)
        
        # Vérifier que la compétence a bien été ajoutée
        with self.db.conn.cursor() as cursor:
            cursor.execute("""
                SELECT s.name, us.level, us.years_experience, us.is_primary
                FROM user_skills us
                JOIN skills s ON us.skill_id = s.id
                WHERE us.user_id = %s
            """, (user_id,))
            
            skills = cursor.fetchall()
            self.assertEqual(len(skills), 1)
            self.assertEqual(skills[0][0], 'Python')
            self.assertEqual(skills[0][1], 'Advanced')
            self.assertEqual(skills[0][2], 5)
            self.assertTrue(skills[0][3])
    
    @classmethod
    def tearDownClass(cls):
        """Nettoyage après tous les tests"""
        if cls.db.conn:
            cls.db.disconnect()

if __name__ == "__main__":
    unittest.main()
