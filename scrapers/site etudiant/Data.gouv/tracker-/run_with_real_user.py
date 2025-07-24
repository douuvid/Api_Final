#!/usr/bin/env python3
"""
Script pour lancer le scraper avec les données d'un utilisateur réel depuis la base de données
"""

import sys
import os
import json
import time
import argparse
import logging
import shutil
import traceback
from datetime import datetime

# Importer le module d'intégration de base de données qui gère le chemin racine
try:
    from db_integration import import_user_database
    UserDatabase = import_user_database()
    print("✅ Module UserDatabase importé avec succès via db_integration")
except ImportError as e:
    print(f"❌ Erreur lors de l'importation via db_integration: {e}")
    # Fallback: essai avec le chemin direct
    try:
        # Détection dynamique du chemin racine du projet
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        sys.path.insert(0, base_dir)
        print(f"Tentative directe avec répertoire racine: {base_dir}")
        from database.user_database import UserDatabase
        print("✅ Module UserDatabase importé avec succès via chemin direct")
    except ImportError as e2:
        print(f"❌ Toutes les tentatives d'importation ont échoué: {e2}")
        print(f"Chemin Python actuel: {sys.path}")
        sys.exit(1)

# Configurer le logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/real_user_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ajouter le répertoire attached_assets au chemin Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'attached_assets'))

# Importer le script de scraping
try:
    from alternance_gouv_1751543361694 import run_scraper
    print("✅ Module alternance_gouv importé avec succès")
except ImportError as e:
    print(f"❌ Erreur lors de l'importation du scraper: {e}")
    sys.exit(1)

def get_user_data(user_id=None, user_email=None):
    """
    Récupère les données d'un utilisateur depuis la base de données
    
    Args:
        user_id: ID de l'utilisateur à récupérer
        user_email: Email de l'utilisateur à récupérer (si None et user_id None, prend le dernier utilisateur)
        
    Returns:
        dict: Les données utilisateur formatées pour le scraper
    """
    try:
        # Créer une instance de UserDatabase
        user_db = UserDatabase()
        print("✅ Connexion à la base de données établie")
        
        # Récupérer l'utilisateur
        if user_id:
            query = "SELECT * FROM users WHERE id = %s"
            user = user_db._execute_query(query, (user_id,), fetch='one')
            if not user:
                print(f"❌ Aucun utilisateur trouvé avec l'ID {user_id}")
                return None
        elif user_email:
            query = "SELECT * FROM users WHERE email = %s"
            user = user_db._execute_query(query, (user_email,), fetch='one')
            if not user:
                print(f"❌ Aucun utilisateur trouvé avec l'email {user_email}")
                return None
        else:
            # Récupérer le dernier utilisateur inscrit
            query = "SELECT * FROM users ORDER BY id DESC LIMIT 1"
            user = user_db._execute_query(query, fetch='one')
            if not user:
                print("❌ Aucun utilisateur trouvé dans la base de données")
                return None
        
        print(f"✅ Utilisateur récupéré: {user['email']}")
        
        # Afficher les préférences de recherche directement depuis les colonnes
        search_query = user.get('search_query', '')
        location = user.get('location', '')
        contract_type = user.get('contract_type', 'Alternance')
        
        if search_query:
            print(f"✅ Métier recherché: {search_query}")
        else:
            print("⚠️ Aucun métier recherché spécifié")
            
        if location:
            print(f"✅ Localisation: {location}")
        else:
            print("⚠️ Aucune localisation spécifiée")
        
        # Vérification obligatoire du numéro de téléphone
        if not user.get('phone'):
            print("❌ ERREUR: Aucun numéro de téléphone trouvé pour cet utilisateur")
            print("Le téléphone est obligatoire pour les candidatures. Veuillez mettre à jour le profil utilisateur.")
            return None
            
        # Récupérer le numéro de téléphone de l'utilisateur (sans valeur par défaut)
        phone_value = user.get('phone')
        
        user_data = {
            "email": user['email'],
            "firstName": user['first_name'],  # Utilise first_name comme dans la BDD
            "lastName": user['last_name'],   # Utilise last_name comme dans la BDD
            "phone": phone_value,            # Champ utilisé par le scraper
            "telephone": phone_value,         # Ajout d'un alias pour compatibilité avec d'autres parties du code
            "phoneNumber": phone_value,       # Autre alias possible - obligatoire d'avoir une valeur
            "cv_path": user.get('cv_path', ''),  # Chemin du CV
            "lm_path": user.get('lm_path', ''),  # Chemin de la lettre de motivation
            "message": "Je suis intéressé(e) par cette offre d'alternance et souhaite postuler.",
            "search_query": search_query or "développeur",  # Métier recherché - champ 'metier' sur le site
            "location": location or "Paris",  # Localisation - champ 'lieu' sur le site
            "contractType": contract_type,  # Type de contrat (Alternance par défaut)
            "settings": {
                "delayBetweenApplications": 5,
                "maxApplicationsPerSession": 2,
                "autoFillForm": True,
                "autoSendApplication": True,
                "pauseBeforeSend": True,  # Pause avant envoi pour vérification
                "captureScreenshots": True
            }
        }
        
        print(f"✅ Données utilisateur préparées pour: {user_data['firstName']} {user_data['lastName']}")
        print(f"📧 Email: {user_data['email']}")
        print(f"📱 Téléphone: {user_data['phone']}")
        print(f"📄 CV: {user_data['cv_path']}")
        print(f"🔍 Recherche: {user_data['search_query']} à {user_data['location']}")
        
        return user_data
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des données utilisateur: {str(e)}")
        traceback.print_exc()
        return None

def setup_directories():
    """Crée les répertoires nécessaires s'ils n'existent pas déjà"""
    dirs = ["uploads", "debug_screenshots", "logs"]
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
    print("📁 Répertoires créés/vérifiés")

def verify_files_exist(user_data):
    """Vérifie que les fichiers CV et LM existent et sont accessibles"""
    files_ok = True
    
    # Obtenir le répertoire racine du projet de manière fiable
    # Essayer plusieurs chemins potentiels pour trouver les fichiers
    potential_base_dirs = [
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),  # /Users/davidravin/Desktop/Api_Final
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))),  # Un niveau plus haut si nécessaire
    ]
    
    # Vérifier le CV
    if user_data.get('cv_path'):
        cv_path = user_data['cv_path']
        cv_found = False
        
        # Essayer tous les chemins base potentiels
        for base_dir in potential_base_dirs:
            if not os.path.isabs(cv_path):
                full_path = os.path.join(base_dir, cv_path)
                
                if os.path.exists(full_path):
                    cv_found = True
                    print(f"✅ CV trouvé: {full_path}")
                    user_data['cv_path'] = full_path  # Mettre à jour avec le chemin absolu
                    break
        
        if not cv_found:
            # Vérifier aussi le chemin direct si c'est un chemin absolu ou s'il existe dans le répertoire courant
            if os.path.isabs(cv_path) and os.path.exists(cv_path):
                print(f"✅ CV trouvé: {cv_path}")
                cv_found = True
            else:
                print(f"❌ CV introuvable dans les chemins testés. Dernier essai: {full_path}")
                # Affichons les répertoires pour debug
                print(f"Répertoires testés: {potential_base_dirs}")
                files_ok = False
    else:
        print("⚠️ Pas de CV défini pour cet utilisateur")
        files_ok = False
    
    # Vérifier la lettre de motivation - même logique
    if user_data.get('lm_path'):
        lm_path = user_data['lm_path']
        lm_found = False
        
        # Essayer tous les chemins base potentiels
        for base_dir in potential_base_dirs:
            if not os.path.isabs(lm_path):
                full_path = os.path.join(base_dir, lm_path)
                
                if os.path.exists(full_path):
                    lm_found = True
                    print(f"✅ Lettre de motivation trouvée: {full_path}")
                    user_data['lm_path'] = full_path  # Mettre à jour avec le chemin absolu
                    break
        
        if not lm_found:
            # Vérifier aussi le chemin direct
            if os.path.isabs(lm_path) and os.path.exists(lm_path):
                print(f"✅ Lettre de motivation trouvée: {lm_path}")
                lm_found = True
            else:
                print(f"❌ Lettre de motivation introuvable dans les chemins testés")
                files_ok = False
    else:
        print("⚠️ Pas de lettre de motivation définie pour cet utilisateur")
    
    return files_ok

def main():
    """Fonction principale du script"""
    print("🚀 Lancement du test avec un utilisateur réel")
    
    # Parser les arguments de ligne de commande
    parser = argparse.ArgumentParser(description="Lance le scraper avec un utilisateur réel")
    parser.add_argument('--user_id', type=int, help="ID de l'utilisateur à utiliser")
    parser.add_argument('--user_email', type=str, help="Email de l'utilisateur à utiliser")
    args = parser.parse_args()
    
    # Créer les répertoires nécessaires
    setup_directories()
    
    # Récupérer les données d'un utilisateur spécifique ou du dernier utilisateur
    user_data = get_user_data(args.user_id, args.user_email)
    
    if not user_data:
        print("❌ Impossible de continuer sans données utilisateur")
        return
    
    print("\n📋 Résumé des données utilisateur:")
    print(json.dumps({k: v for k, v in user_data.items() if k != 'settings'}, indent=2))
    
    # Vérifier l'existence des fichiers CV et LM
    print("\n🔍 Vérification des fichiers...")
    files_ok = verify_files_exist(user_data)
    
    # Lancer le scraper avec les données utilisateur récupérées
    print("\n🤖 Lancement du scraper...")
    try:
        # Créer une copie des données pour masquer le mot de passe dans les logs
        safe_user_data = user_data.copy()
        if 'password' in safe_user_data:
            safe_user_data['password'] = '********'
        
        # Log des informations importantes pour le scraper
        logger.info(f"Lancement du scraper avec les données de {safe_user_data['email']}")
        logger.info(f"Métier recherché: {safe_user_data['search_query']}")
        logger.info(f"Localisation: {safe_user_data['location']}")
        
        # Vérifier que les informations essentielles pour le scraper sont disponibles
        if not user_data.get('search_query'):
            print("⚠️ Attention: Aucun métier de recherche spécifié. Le formulaire de recherche ne sera pas rempli correctement.")
        
        if not user_data.get('location'):
            print("⚠️ Attention: Aucune localisation spécifiée. Le formulaire de recherche ne sera pas rempli correctement.")
        
        # Appeler la fonction run_scraper
        if not files_ok:
            print("⚠️ Attention: Certains fichiers sont manquants. Le scraper peut rencontrer des erreurs.")
            proceed = input("Voulez-vous continuer quand même ? (o/n): ")
            if proceed.lower() != 'o':
                print("Opération annulée par l'utilisateur")
                return
        
        # Lancer le scraper
        print("Démarrage du scraper pour le site alternance.emploi.gouv.fr...")
        run_scraper(user_data)
        
        print("✅ Scraper terminé avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution du scraper: {str(e)}")
        logger.error(f"Erreur: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
