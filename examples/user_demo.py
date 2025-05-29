"""
Démonstration des fonctionnalités de la base de données utilisateur
"""
import sys
from pathlib import Path
from getpass import getpass

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from database.user_database import UserDatabase
from database.config import DatabaseConfig

def print_header(title):
    """Affiche un en-tête stylisé"""
    print("\n" + "="*50)
    print(f" {title.upper()} ".center(50, "="))
    print("="*50)

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
        # 1. Création d'un nouvel utilisateur
        print_header("Création d'un nouvel utilisateur")
        user_data = {
            "email": input("Email: "),
            "password": getpass("Mot de passe: "),
            "first_name": input("Prénom: "),
            "last_name": input("Nom: "),
            "phone": input("Téléphone (facultatif): ") or None,
            "address": input("Adresse (facultatif): ") or None,
            "city": input("Ville (facultatif): ") or None,
            "postal_code": input("Code postal (facultatif): ") or None,
            "country": input("Pays (facultatif): ") or None
        }
        
        user_id = db.create_user(**user_data)
        if user_id:
            print(f"✅ Utilisateur créé avec l'ID: {user_id}")
            
            # 2. Connexion
            print_header("Connexion")
            email = input("Email: ")
            password = getpass("Mot de passe: ")
            
            user = db.authenticate_user(email, password)
            if user:
                print(f"✅ Connexion réussie. Bienvenue {user['first_name']} {user['last_name']} !")
                
                # 3. Mise à jour du profil
                print_header("Mise à jour du profil")
                print("Laissez vide pour conserver la valeur actuelle.")
                
                updates = {}
                if new_first_name := input(f"Prénom [{user['first_name']}]: ").strip():
                    updates['first_name'] = new_first_name
                if new_last_name := input(f"Nom [{user['last_name']}]: ").strip():
                    updates['last_name'] = new_last_name
                if new_phone := input(f"Téléphone [{user.get('phone', '')}]: ").strip() or None:
                    updates['phone'] = new_phone
                
                if updates:
                    if db.update_user(user['user_id'], **updates):
                        print("✅ Profil mis à jour avec succès")
                    else:
                        print("❌ Échec de la mise à jour du profil")
                
                # 4. Ajout de compétences
                print_header("Ajout de compétences")
                while True:
                    skill = input("Ajouter une compétence (ou 'fin' pour terminer): ").strip()
                    if skill.lower() == 'fin':
                        break
                    if skill:
                        if db.add_skill_to_user(user['user_id'], skill, "Intermédiaire"):
                            print(f"✅ Compétence '{skill}' ajoutée")
                        else:
                            print(f"❌ Échec de l'ajout de la compétence")
                
                # Affichage du profil complet
                print_header("Profil complet")
                full_profile = db.get_user_by_id(user['user_id'])
                skills = db.get_user_skills(user['user_id'])
                
                print(f"\n=== INFORMATIONS PERSONNELLES ===")
                print(f"Nom complet: {full_profile['first_name']} {full_profile['last_name']}")
                print(f"Email: {full_profile['email']}")
                print(f"Téléphone: {full_profile.get('phone', 'Non renseigné')}")
                
                if skills:
                    print("\n=== COMPÉTENCES ===")
                    for skill in skills:
                        print(f"- {skill['skill_name']} ({skill['proficiency_level']})")
            else:
                print("❌ Identifiants incorrects")
        else:
            print("❌ Échec de la création de l'utilisateur")
            
    except Exception as e:
        print(f"❌ Une erreur est survenue: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    main()
