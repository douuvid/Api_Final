#!/usr/bin/env python3
"""
Script de test pour la postulation automatique
"""

import json
import sys
import os

# Données de test - Utilisateur avec email, téléphone et chemin CV spécifiques pour le test
test_config = {
    "firstName": "Test",
    "lastName": "Utilisateur",
    "email": "test.utilisateur@example.com",  # Email spécifique pour le test
    "phone": "0712345678",  # Format téléphone français standard
    "message": "Je suis passionné par le développement web et je recherche une alternance pour approfondir mes compétences.",
    "cv_path": "uploads/mon_cv_test.pdf",  # Utilise cv_path au lieu de cvPath pour tester la détection multiple
    "coverLetterPath": "uploads/ma_lettre_test.pdf",  # Nom modifié pour les tests
    "searchKeywords": "développement web, javascript, python",  # Mots-clés pertinents
    "location": "Lyon",  # Localisation différente
    "jobTypes": "alternance, stage",
    "contractTypes": "Alternance",  # Uniquement alternance
    "educationLevel": "master",  # Niveau d'éducation différent
    "searchRadius": "30",  # Rayon de recherche différent
    "search_query": "développeur web",  # Requête de recherche spécifique
    "settings": {
        "delayBetweenApplications": 5,
        "maxApplicationsPerSession": 2,  # Limité à 2 pour les tests
        "autoFillForm": True,
        "autoSendApplication": True,
        "pauseBeforeSend": True,  # Pause ajoutée pour vérifier les formulaires
        "captureScreenshots": True
    }
}

if __name__ == "__main__":
    print("🚀 Test de postulation automatique")
    print("Configuration:", json.dumps(test_config, indent=2))
    
    # Lancer le script d'automatisation
    import subprocess
    
    try:
        # Créer les dossiers nécessaires
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("debug_screenshots", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Créer des fichiers de test avec les nouveaux noms
        cv_path = "uploads/mon_cv_test.pdf"
        cover_letter_path = "uploads/ma_lettre_test.pdf"
        
        if not os.path.exists(cv_path):
            with open(cv_path, "w") as f:
                f.write("CV de test spécifique pour tester l'intégration email/téléphone/cv")
            print(f"📄 CV de test créé à {cv_path}")
        
        if not os.path.exists(cover_letter_path):
            with open(cover_letter_path, "w") as f:
                f.write("Lettre de motivation de test spécifique")
            print(f"📄 Lettre de motivation créée à {cover_letter_path}")
        
        print("📁 Dossiers et fichiers de test créés")
        
        # Lancer le script d'automatisation
        print("🤖 Lancement de l'automatisation...")
        
        # Passer la configuration via stdin
        process = subprocess.Popen(
            ["python3", "python_scripts/automation_runner.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=json.dumps(test_config))
        
        print("📤 Sortie du script:")
        print(stdout)
        
        if stderr:
            print("❌ Erreurs:")
            print(stderr)
            
    except Exception as e:
        print(f"❌ Erreur: {e}") 