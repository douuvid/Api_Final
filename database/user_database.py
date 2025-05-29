import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import uuid
import json
from datetime import datetime, timedelta
import logging
import re

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserDatabase:
    def __init__(self, host="localhost", database="job_search_app", 
                 user="postgres", password="your_password", port=5432):
        """
        Initialise la connexion à la base de données PostgreSQL pour les utilisateurs
        """
        self.connection_params = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port
        }
        self.conn = None
        
    def connect(self):
        """Établit la connexion à la base de données"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            logger.info("✅ Connexion à PostgreSQL établie")
            return True
        except psycopg2.Error as e:
            logger.error(f"❌ Erreur de connexion PostgreSQL: {e}")
            return False
    
    def disconnect(self):
        """Ferme la connexion à la base de données"""
        if self.conn:
            self.conn.close()
            logger.info("🔌 Connexion fermée")
    
    def create_tables(self):
        """
        Crée toutes les tables nécessaires pour la gestion des utilisateurs
        """
        
        # Table des utilisateurs principale
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            salt VARCHAR(255) NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            date_of_birth DATE,
            gender VARCHAR(10) CHECK (gender IN ('M', 'F', 'Other')),
            profile_picture_url VARCHAR(500),
            is_active BOOLEAN DEFAULT TRUE,
            is_verified BOOLEAN DEFAULT FALSE,
            verification_token VARCHAR(255),
            reset_password_token VARCHAR(255),
            reset_password_expires TIMESTAMP,
            last_login TIMESTAMP,
            login_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Table du profil professionnel
        create_user_profiles_table = """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(200),
            summary TEXT,
            experience_years INTEGER,
            current_salary DECIMAL(10,2),
            expected_salary DECIMAL(10,2),
            availability_date DATE,
            location_preference VARCHAR(200),
            remote_work_preference VARCHAR(50) CHECK (remote_work_preference IN ('Full remote', 'Hybrid', 'On-site', 'Flexible')),
            contract_preferences TEXT[], -- ['CDI', 'CDD', 'Freelance', etc.]
            linkedin_url VARCHAR(300),
            portfolio_url VARCHAR(300),
            github_url VARCHAR(300),
            other_links JSONB,
            cv_file_path VARCHAR(500),
            cover_letter_template TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Table des compétences
        create_skills_table = """
        CREATE TABLE IF NOT EXISTS skills (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) UNIQUE NOT NULL,
            category VARCHAR(100), -- 'Technical', 'Soft Skills', 'Languages', etc.
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Table de liaison utilisateur-compétences
        create_user_skills_table = """
        CREATE TABLE IF NOT EXISTS user_skills (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            skill_id UUID REFERENCES skills(id) ON DELETE CASCADE,
            level VARCHAR(50) CHECK (level IN ('Beginner', 'Intermediate', 'Advanced', 'Expert')),
            years_experience INTEGER,
            is_primary BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, skill_id)
        );
        """
        
        # Table des expériences professionnelles
        create_experiences_table = """
        CREATE TABLE IF NOT EXISTS user_experiences (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            company_name VARCHAR(200) NOT NULL,
            position VARCHAR(200) NOT NULL,
            description TEXT,
            start_date DATE NOT NULL,
            end_date DATE,
            is_current BOOLEAN DEFAULT FALSE,
            location VARCHAR(200),
            company_size VARCHAR(50),
            industry VARCHAR(100),
            achievements TEXT[],
            technologies_used TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Table des formations
        create_educations_table = """
        CREATE TABLE IF NOT EXISTS user_educations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            institution VARCHAR(200) NOT NULL,
            degree VARCHAR(200) NOT NULL,
            field_of_study VARCHAR(200),
            start_date DATE,
            end_date DATE,
            is_current BOOLEAN DEFAULT FALSE,
            grade VARCHAR(50),
            description TEXT,
            location VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Table des recherches sauvegardées
        create_saved_searches_table = """
        CREATE TABLE IF NOT EXISTS saved_searches (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(200) NOT NULL,
            search_criteria JSONB NOT NULL,
            is_alert_active BOOLEAN DEFAULT FALSE,
            alert_frequency VARCHAR(50) CHECK (alert_frequency IN ('Daily', 'Weekly', 'Monthly')),
            last_alert_sent TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Table des offres favorites
        create_favorite_jobs_table = """
        CREATE TABLE IF NOT EXISTS favorite_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            job_id VARCHAR(50) NOT NULL, -- ID de l'offre Pôle Emploi
            job_title VARCHAR(500),
            company_name VARCHAR(200),
            location VARCHAR(200),
            job_data JSONB, -- Copie des données de l'offre
            notes TEXT,
            status VARCHAR(50) DEFAULT 'Interested' CHECK (status IN ('Interested', 'Applied', 'Interview', 'Offer', 'Rejected', 'Not_Interested')),
            application_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, job_id)
        );
        """
        
        # Table des candidatures
        create_applications_table = """
        CREATE TABLE IF NOT EXISTS job_applications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            job_id VARCHAR(50) NOT NULL,
            job_title VARCHAR(500),
            company_name VARCHAR(200),
            application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'Sent' CHECK (status IN ('Sent', 'Viewed', 'Interview_Scheduled', 'Interview_Done', 'Offer', 'Rejected', 'Withdrawn')),
            cover_letter TEXT,
            cv_used VARCHAR(500),
            follow_up_date DATE,
            notes TEXT,
            contact_person VARCHAR(200),
            contact_email VARCHAR(255),
            contact_phone VARCHAR(20),
            interview_date TIMESTAMP,
            interview_location VARCHAR(300),
            interview_notes TEXT,
            offer_details JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Table des préférences utilisateur
        create_user_preferences_table = """
        CREATE TABLE IF NOT EXISTS user_preferences (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
            email_notifications BOOLEAN DEFAULT TRUE,
            sms_notifications BOOLEAN DEFAULT FALSE,
            push_notifications BOOLEAN DEFAULT TRUE,
            job_alert_frequency VARCHAR(50) DEFAULT 'Daily',
            newsletter_subscription BOOLEAN DEFAULT TRUE,
            data_sharing_consent BOOLEAN DEFAULT FALSE,
            marketing_consent BOOLEAN DEFAULT FALSE,
            language_preference VARCHAR(10) DEFAULT 'fr',
            timezone VARCHAR(50) DEFAULT 'Europe/Paris',
            theme_preference VARCHAR(20) DEFAULT 'light',
            dashboard_layout JSONB,
            privacy_settings JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Table des sessions utilisateur
        create_user_sessions_table = """
        CREATE TABLE IF NOT EXISTS user_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            session_token VARCHAR(255) UNIQUE NOT NULL,
            ip_address INET,
            user_agent TEXT,
            device_info JSONB,
            location_info JSONB,
            is_active BOOLEAN DEFAULT TRUE,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Création des index pour optimiser les performances
        create_indexes = """
        -- Index sur les utilisateurs
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
        CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
        
        -- Index sur les profils
        CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_profiles_location ON user_profiles(location_preference);
        
        -- Index sur les compétences
        CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name);
        CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(category);
        CREATE INDEX IF NOT EXISTS idx_user_skills_user_id ON user_skills(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_skills_skill_id ON user_skills(skill_id);
        
        -- Index sur les expériences
        CREATE INDEX IF NOT EXISTS idx_experiences_user_id ON user_experiences(user_id);
        CREATE INDEX IF NOT EXISTS idx_experiences_company ON user_experiences(company_name);
        CREATE INDEX IF NOT EXISTS idx_experiences_position ON user_experiences(position);
        
        -- Index sur les formations
        CREATE INDEX IF NOT EXISTS idx_educations_user_id ON user_educations(user_id);
        CREATE INDEX IF NOT EXISTS idx_educations_institution ON user_educations(institution);
        
        -- Index sur les recherches sauvegardées
        CREATE INDEX IF NOT EXISTS idx_saved_searches_user_id ON saved_searches(user_id);
        CREATE INDEX IF NOT EXISTS idx_saved_searches_alert_active ON saved_searches(is_alert_active);
        
        -- Index sur les favoris
        CREATE INDEX IF NOT EXISTS idx_favorite_jobs_user_id ON favorite_jobs(user_id);
        CREATE INDEX IF NOT EXISTS idx_favorite_jobs_job_id ON favorite_jobs(job_id);
        CREATE INDEX IF NOT EXISTS idx_favorite_jobs_status ON favorite_jobs(status);
        
        -- Index sur les candidatures
        CREATE INDEX IF NOT EXISTS idx_applications_user_id ON job_applications(user_id);
        CREATE INDEX IF NOT EXISTS idx_applications_job_id ON job_applications(job_id);
        CREATE INDEX IF NOT EXISTS idx_applications_status ON job_applications(status);
        CREATE INDEX IF NOT EXISTS idx_applications_date ON job_applications(application_date);
        
        -- Index sur les sessions
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
        CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);
        CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(is_active);
        """
        
        try:
            with self.conn.cursor() as cursor:
                # Créer toutes les tables
                cursor.execute(create_users_table)
                cursor.execute(create_user_profiles_table)
                cursor.execute(create_skills_table)
                cursor.execute(create_user_skills_table)
                cursor.execute(create_experiences_table)
                cursor.execute(create_educations_table)
                cursor.execute(create_saved_searches_table)
                cursor.execute(create_favorite_jobs_table)
                cursor.execute(create_applications_table)
                cursor.execute(create_user_preferences_table)
                cursor.execute(create_user_sessions_table)
                
                # Créer les index
                cursor.execute(create_indexes)
                
                self.conn.commit()
                logger.info("✅ Toutes les tables utilisateurs créées avec succès")
                return True
        except psycopg2.Error as e:
            logger.error(f"❌ Erreur création tables: {e}")
            self.conn.rollback()
            return False
    
    def hash_password(self, password):
        """
        Hash un mot de passe avec un salt unique
        """
        salt = uuid.uuid4().hex
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return password_hash.hex(), salt
    
    def verify_password(self, password, password_hash, salt):
        """
        Vérifie un mot de passe
        """
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex() == password_hash
    
    def validate_email(self, email):
        """
        Valide le format d'un email
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def create_user(self, user_data):
        """
        Crée un nouvel utilisateur
        """
        required_fields = ['email', 'password', 'first_name', 'last_name']
        
        # Validation des champs requis
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                raise ValueError(f"Le champ '{field}' est requis")
        
        # Validation de l'email
        if not self.validate_email(user_data['email']):
            raise ValueError("Format d'email invalide")
        
        # Hash du mot de passe
        password_hash, salt = self.hash_password(user_data['password'])
        
        # Génération du token de vérification
        verification_token = uuid.uuid4().hex
        
        insert_query = """
        INSERT INTO users (
            email, password_hash, salt, first_name, last_name, 
            phone, date_of_birth, gender, verification_token
        ) VALUES (
            %(email)s, %(password_hash)s, %(salt)s, %(first_name)s, %(last_name)s,
            %(phone)s, %(date_of_birth)s, %(gender)s, %(verification_token)s
        ) RETURNING id;
        """
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(insert_query, {
                    'email': user_data['email'].lower(),
                    'password_hash': password_hash,
                    'salt': salt,
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'phone': user_data.get('phone'),
                    'date_of_birth': user_data.get('date_of_birth'),
                    'gender': user_data.get('gender'),
                    'verification_token': verification_token
                })
                
                user_id = cursor.fetchone()[0]
                
                # Créer les préférences par défaut
                self.create_default_preferences(user_id)
                
                self.conn.commit()
                logger.info(f"✅ Utilisateur créé avec l'ID: {user_id}")
                return user_id, verification_token
                
        except psycopg2.IntegrityError:
            self.conn.rollback()
            raise ValueError("Un utilisateur avec cet email existe déjà")
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"❌ Erreur création utilisateur: {e}")
            raise Exception("Erreur lors de la création de l'utilisateur")
    
    def create_default_preferences(self, user_id):
        """
        Crée les préférences par défaut pour un nouvel utilisateur
        """
        insert_query = """
        INSERT INTO user_preferences (user_id) VALUES (%(user_id)s);
        """
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(insert_query, {'user_id': user_id})
        except psycopg2.Error as e:
            logger.error(f"❌ Erreur création préférences: {e}")
    
    def authenticate_user(self, email, password):
        """
        Authentifie un utilisateur
        """
        query = """
        SELECT id, email, password_hash, salt, is_active, is_verified, 
               login_attempts, locked_until, first_name, last_name
        FROM users 
        WHERE email = %(email)s;
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, {'email': email.lower()})
                user = cursor.fetchone()
                
                if not user:
                    return None, "Email ou mot de passe incorrect"
                
                # Vérifier si le compte est verrouillé
                if user['locked_until'] and user['locked_until'] > datetime.now():
                    return None, f"Compte verrouillé jusqu'à {user['locked_until']}"
                
                # Vérifier le mot de passe
                if not self.verify_password(password, user['password_hash'], user['salt']):
                    # Incrémenter les tentatives de connexion
                    self.increment_login_attempts(user['id'])
                    return None, "Email ou mot de passe incorrect"
                
                # Vérifier si le compte est actif
                if not user['is_active']:
                    return None, "Compte désactivé"
                
                # Réinitialiser les tentatives et mettre à jour la dernière connexion
                self.reset_login_attempts(user['id'])
                self.update_last_login(user['id'])
                
                return user, "Authentification réussie"
                
        except psycopg2.Error as e:
            logger.error(f"❌ Erreur authentification: {e}")
            return None, "Erreur lors de l'authentification"
    
    def increment_login_attempts(self, user_id):
        """
        Incrémente le nombre de tentatives de connexion échouées
        """
        query = """
        UPDATE users 
        SET login_attempts = login_attempts + 1,
            locked_until = CASE 
                WHEN login_attempts + 1 >= 5 THEN CURRENT_TIMESTAMP + INTERVAL '30 minutes'
                ELSE locked_until
            END
        WHERE id = %(user_id)s;
        """
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, {'user_id': user_id})
                self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"❌ Erreur incrémentation tentatives: {e}")
    
    def reset_login_attempts(self, user_id):
        """
        Remet à zéro les tentatives de connexion
        """
        query = """
        UPDATE users 
        SET login_attempts = 0, locked_until = NULL
        WHERE id = %(user_id)s;
        """
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, {'user_id': user_id})
                self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"❌ Erreur reset tentatives: {e}")
    
    def update_last_login(self, user_id):
        """
        Met à jour la date de dernière connexion
        """
        query = """
        UPDATE users 
        SET last_login = CURRENT_TIMESTAMP
        WHERE id = %(user_id)s;
        """
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, {'user_id': user_id})
                self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"❌ Erreur update last login: {e}")
    
    def get_user_profile(self, user_id):
        """
        Récupère le profil complet d'un utilisateur
        """
        query = """
        SELECT 
            u.id, u.email, u.first_name, u.last_name, u.phone, 
            u.date_of_birth, u.gender, u.profile_picture_url,
            u.is_verified, u.last_login, u.created_at,
            p.title, p.summary, p.experience_years, p.current_salary,
            p.expected_salary, p.availability_date, p.location_preference,
            p.remote_work_preference, p.contract_preferences,
            p.linkedin_url, p.portfolio_url, p.github_url, p.other_links
        FROM users u
        LEFT JOIN user_profiles p ON u.id = p.user_id
        WHERE u.id = %(user_id)s;
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, {'user_id': user_id})
                return cursor.fetchone()
        except psycopg2.Error as e:
            logger.error(f"❌ Erreur récupération profil: {e}")
            return None
    
    def add_user_skill(self, user_id, skill_name, level, years_experience=None, is_primary=False):
        """
        Ajoute une compétence à un utilisateur
        """
        # D'abord, créer la compétence si elle n'existe pas
        skill_id = self.get_or_create_skill(skill_name)
        
        insert_query = """
        INSERT INTO user_skills (user_id, skill_id, level, years_experience, is_primary)
        VALUES (%(user_id)s, %(skill_id)s, %(level)s, %(years_experience)s, %(is_primary)s)
        ON CONFLICT (user_id, skill_id) DO UPDATE SET
            level = EXCLUDED.level,
            years_experience = EXCLUDED.years_experience,
            is_primary = EXCLUDED.is_primary;
        """
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(insert_query, {
                    'user_id': user_id,
                    'skill_id': skill_id,
                    'level': level,
                    'years_experience': years_experience,
                    'is_primary': is_primary
                })
                self.conn.commit()
                return True
        except psycopg2.Error as e:
            logger.error(f"❌ Erreur ajout compétence: {e}")
            self.conn.rollback()
            return False
    
    def get_or_create_skill(self, skill_name, category='Technical'):
        """
        Récupère l'ID d'une compétence ou la crée si elle n'existe pas
        """
        # Chercher la compétence existante
        select_query = "SELECT id FROM skills WHERE name = %(name)s;"
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(select_query, {'name': skill_name})
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                
                # Créer la compétence
                insert_query = """
                INSERT INTO skills (name, category) 
                VALUES (%(name)s, %(category)s) 
                RETURNING id;
                """
                cursor.execute(insert_query, {'name': skill_name, 'category': category})
                skill_id = cursor.fetchone()[0]
                self.conn.commit()
                return skill_id
                
        except psycopg2.Error as e:
            logger.error(f"❌ Erreur get/create skill: {e}")
            self.conn.rollback()
            return None
    
    def save_favorite_job(self, user_id, job_id, job_data, notes=None):
        """
        Sauvegarde une offre d'emploi en favori
        """
        insert_query = """
        INSERT INTO favorite_jobs (user_id, job_id, job_title, company_name, location, job_data, notes)
        VALUES (%(user_id)s, %(job_id)s, %(job_title)s, %(company_name)s, %(location)s, %(job_data)s, %(notes)s)
        ON CONFLICT (user_id, job_id) DO UPDATE SET
            job_data = EXCLUDED.job_data,
            notes = EXCLUDED.notes,
            updated_at = CURRENT_TIMESTAMP;
        """
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(insert_query, {
                    'user_id': user_id,
                    'job_id': job_id,
                    'job_title': job_data.get('intitule', ''),
                    'company_name': job_data.get('entreprise', {}).get('nom', ''),
                    'location': job_data.get('lieuTravail', {}).get('libelle', ''),
                    'job_data': json.dumps(job_data),
                    'notes': notes
                })
                self.conn.commit()
                return True
        except psycopg2.Error as e:
            logger.error(f"❌ Erreur sauvegarde favori: {e}")
            self.conn.rollback()
            return False
    
    def get_user_stats(self, user_id):
        """
        Récupère les statistiques d'un utilisateur
        """
        stats_query = """
        SELECT 
            (SELECT COUNT(*) FROM favorite_jobs WHERE user_id = %(user_id)s) as favorite_jobs_count,
            (SELECT COUNT(*) FROM job_applications WHERE user_id = %(user_id)s) as applications_count,
            (SELECT COUNT(*) FROM saved_searches WHERE user_id = %(user_id)s) as saved_searches_count,
            (SELECT COUNT(*) FROM user_skills WHERE user_id = %(user_id)s) as skills_count,
            (SELECT COUNT(*) FROM user_experiences WHERE user_id = %(user_id)s) as experiences_count,
            (SELECT COUNT(*) FROM user_educations WHERE user_id = %(user_id)s) as educations_count;
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(stats_query, {'user_id': user_id})
                return cursor.fetchone()
        except psycopg2.Error as e:
            logger.error(f"❌ Erreur récupération stats: {e}")
            return None

# Le code d'exemple a été déplacé dans le dossier examples/