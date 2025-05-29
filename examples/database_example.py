"""
Exemple d'utilisation de la base de données utilisateur.

Ce script montre comment utiliser la classe UserDatabase pour gérer les utilisateurs,
crérer des profils, ajouter des compétences, etc.
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH pour les imports
root_dir = str(Path(__file__).parent.parent)
sys.path.append(root_dir)

from database import UserDatabase, DatabaseConfig

def main():
    # Initialisation de la base de données
    db = UserDatabase(
        host=DatabaseConfig.HOST,
        database=DatabaseConfig.DATABASE,
        user=DatabaseConfig.USER,
        password=DatabaseConfig.PASSWORD,
        port=DatabaseConfig.PORT
    )
    
    try:
        # Connexion à la base de données
        if not db.connect():
            print("❌ Impossible de se connecter à la base de données")
            return
        
        # Création des tables si elles n'existent pas
        print("🔄 Création des tables...")
        if db.create_tables():
            print("✅ Tables créées avec succès")
        else:
            print("⚠️  Certaines tables n'ont pas pu être créées")
        
        # Exemple: Création d'un utilisateur
        print("\n👤 Création d'un nouvel utilisateur...")
        user_data = {
            'email': 'jean.dupont@example.com',
            'password': 'MonSuperMotDePasse123!',
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'phone': '+33612345678',
            'date_of_birth': '1990-01-01',
            'gender': 'M'
        }
        
        try:
            user_id, verification_token = db.create_user(user_data)
            print(f"✅ Utilisateur créé avec l'ID: {user_id}")
            print(f"🔑 Token de vérification: {verification_token}")
            
            # Exemple: Authentification
            print("\n🔐 Authentification de l'utilisateur...")
            user, message = db.authenticate_user(
                email='jean.dupont@example.com',
                password='MonSuperMotDePasse123!'
            )
            
            if user:
                print(f"✅ {message}")
                print(f"👋 Bienvenue, {user['first_name']} {user['last_name']} !")
                
                # Exemple: Ajout d'une compétence
                print("\n➕ Ajout d'une compétence à l'utilisateur...")
                if db.add_user_skill(
                    user_id=user['id'],
                    skill_name='Python',
                    level='Advanced',
                    years_experience=5,
                    is_primary=True
                ):
                    print("✅ Compétence ajoutée avec succès")
                else:
                    print("❌ Erreur lors de l'ajout de la compétence")
                
            else:
                print(f"❌ Échec de l'authentification: {message}")
                
        except ValueError as e:
            print(f"❌ Erreur: {e}")
        
    except Exception as e:
        print(f"❌ Une erreur inattendue s'est produite: {e}")
    finally:
        # Toujours fermer la connexion
        db.disconnect()
        print("\n🔌 Connexion à la base de données fermée")

if __name__ == "__main__":
    main()
