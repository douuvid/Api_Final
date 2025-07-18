#!/usr/bin/env python3
"""
Script temporaire pour vérifier quels utilisateurs ont déjà des CV/LM dans la base de données
"""

import sys
import os
import json
from database.user_database import UserDatabase

def main():
    print("🔍 Vérification des utilisateurs avec CV/LM")
    
    # Créer une instance de UserDatabase
    user_db = UserDatabase()
    print("✅ Connexion à la base de données établie")
    
    # Récupérer tous les utilisateurs
    query = "SELECT id, email, first_name, last_name, cv_path, lm_path, phone FROM users ORDER BY id DESC"
    users = user_db._execute_query(query)
    
    if not users:
        print("❌ Aucun utilisateur trouvé dans la base de données")
        return
    
    print(f"📊 Total d'utilisateurs: {len(users)}")
    print("\n📋 Utilisateurs avec CV/LM:")
    print("=" * 80)
    print(f"{'ID':5} | {'Email':30} | {'Nom':20} | {'Téléphone':15} | {'CV':15} | {'LM':15}")
    print("-" * 80)
    
    # Afficher les utilisateurs avec leurs infos
    users_with_cv = 0
    users_with_lm = 0
    users_with_phone = 0
    
    for user in users:
        has_cv = bool(user.get('cv_path'))
        has_lm = bool(user.get('lm_path'))
        has_phone = bool(user.get('phone'))
        
        if has_cv:
            users_with_cv += 1
        if has_lm:
            users_with_lm += 1
        if has_phone:
            users_with_phone += 1
            
        cv_status = "✅" if has_cv else "❌"
        lm_status = "✅" if has_lm else "❌"
        phone_status = user.get('phone', '❌')
            
        print(f"{user['id']:5} | {user['email']:30} | {user['first_name']} {user['last_name']:16} | {phone_status:15} | {cv_status:15} | {lm_status:15}")
    
    print("=" * 80)
    print(f"📊 Résumé: {users_with_cv}/{len(users)} ont un CV, {users_with_lm}/{len(users)} ont une LM, {users_with_phone}/{len(users)} ont un téléphone")
    
    # Afficher plus de détails sur le premier utilisateur avec CV
    user_with_cv = next((user for user in users if user.get('cv_path')), None)
    if user_with_cv:
        print("\n📄 Exemple de chemin CV:", user_with_cv['cv_path'])
        
        # Vérifier si le fichier existe
        cv_path = user_with_cv['cv_path']
        if not os.path.isabs(cv_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cv_path = os.path.join(base_dir, cv_path)
            
        if os.path.exists(cv_path):
            print(f"✅ Le fichier existe: {cv_path}")
            print(f"   Taille: {os.path.getsize(cv_path)} octets")
        else:
            print(f"❌ Le fichier n'existe pas: {cv_path}")

if __name__ == "__main__":
    main()
