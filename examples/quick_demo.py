"""
Démonstration rapide des fonctionnalités de la base de données utilisateur
"""
import sys
from pathlib import Path
import uuid

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from database.user_database import UserDatabase
from database.config import DatabaseConfig

def print_step(step):
    print(f"\n{'='*10} {step} {'='*10}")

def main():
    # Initialiser la connexion à la base de données
    db = UserDatabase(
        host=DatabaseConfig.HOST,
        database=DatabaseConfig.DATABASE,
        user=DatabaseConfig.USER,
        password=DatabaseConfig.PASSWORD,
        port=DatabaseConfig.PORT
    )
    
    if not db.connect():
        print("❌ Impossible de se connecter à la base de données")
        return
    
    try:
        # Générer un email unique pour le test
        test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        test_password = "MotDePasse123!"
        
        # 1. Création d'un nouvel utilisateur
        print_step("1. Création d'un nouvel utilisateur")
        user_data = {
            'email': test_email,
            'password': test_password,
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'phone': '0123456789'
        }
        user_id = db.create_user(user_data)
        
        if user_id:
            print(f"✅ Utilisateur créé avec l'ID: {user_id}")
            print(f"   Email: {test_email}")
            print(f"   Mot de passe: {test_password}")
            
            # 2. Connexion
            print_step("2. Connexion")
            user, message = db.authenticate_user(test_email, test_password)
            if user:
                print(f"✅ {message}")
                print(f"   Bienvenue {user['first_name']} {user['last_name']} !")
                
                # 3. Affichage du profil utilisateur
                print_step("3. Affichage du profil utilisateur")
                profile = db.get_user_profile(user['id'])
                if profile:
                    print("\n=== PROFIL UTILISATEUR ===")
                    print(f"ID: {profile.get('id')}")
                    print(f"Nom: {profile.get('first_name')} {profile.get('last_name')}")
                    print(f"Email: {profile.get('email')}")
                    print(f"Téléphone: {profile.get('phone', 'Non renseigné')}")
                    print(f"Dernière connexion: {profile.get('last_login', 'Jamais')}")
                else:
                    print("❌ Impossible de récupérer le profil utilisateur")
                
                # 4. Ajout de compétences
                print_step("4. Ajout de compétences")
                skills = [
                    ("Python", "Advanced"),
                    ("Gestion de projet", "Intermediate"),
                    ("SQL", "Intermediate")
                ]
                for skill, level in skills:
                    try:
                        skill_id = db.get_or_create_skill(skill)
                        if db.add_user_skill(user['id'], skill, level):
                            print(f"✅ Compétence ajoutée: {skill} ({level})")
                        else:
                            print(f"❌ Impossible d'ajouter la compétence: {skill}")
                    except Exception as e:
                        print(f"❌ Erreur avec la compétence {skill}: {e}")
                
                # 5. Affichage des statistiques
                print_step("5. Statistiques de l'utilisateur")
                stats = db.get_user_stats(user['id'])
                if stats:
                    print("\n=== STATISTIQUES ===")
                    print(f"Nombre de compétences: {stats.get('skills_count', 0)}")
                    print(f"Dernière connexion: {stats.get('last_login', 'Jamais')}")
                    print(f"Tentatives de connexion: {stats.get('login_attempts', 0)}")
                else:
                    print("❌ Impossible de récupérer les statistiques")
                
                print("\n✅ Démonstration terminée avec succès !")
                
    except Exception as e:
        print(f"❌ Une erreur est survenue: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    main()
