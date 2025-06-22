"""
Exemple d'utilisation de l'API ROME 4.0 de France Travail.

Ce script montre comment utiliser le client FranceTravailROME4API pour :
- Récupérer les détails d'un métier
- Extraire les compétences structurées
- Effectuer un matching de compétences
"""

import os
from dotenv import load_dotenv
from france_travail import FranceTravailROME4API

def main():
    # Charger les variables d'environnement
    load_dotenv()
    
    # Récupérer les identifiants
    client_id = os.getenv('FRANCE_TRAVAIL_CLIENT_ID')
    client_secret = os.getenv('FRANCE_TRAVAIL_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Erreur: FRANCE_TRAVAIL_CLIENT_ID et FRANCE_TRAVAIL_CLIENT_SECRET doivent être définis dans le .env")
        return
    
    # Initialiser le client
    api = FranceTravailROME4API(client_id=client_id, client_secret=client_secret)
    
    # Exemple de code ROME (Développeur web)
    rome_code = "M1805"
    
    # Compétences utilisateur à matcher
    user_skills = [
        "Python", "Développement web", "Base de données",
        "Travail en équipe", "Git", "API REST", "Tests unitaires"
    ]
    
    print(f"🔍 Début du matching pour le code ROME: {rome_code}")
    print(f"📋 Compétences utilisateur: {', '.join(user_skills)}\n")
    
    # 1. Récupérer les détails du métier
    print("=== DÉTAILS DU MÉTIER ===")
    metier = api.get_metier_details(rome_code)
    if metier:
        print(f"🏷  Métier: {metier.get('libelle', 'Inconnu')}")
        print(f"📝 Description: {metier.get('description', 'Non disponible')[:150]}...\n")
    
    # 2. Extraire les compétences structurées
    print("=== COMPÉTENCES STRUCTURÉES ===")
    competences = api.extract_competences_from_metier(rome_code)
    for categorie, items in competences.items():
        if items:
            print(f"\n🔹 {categorie.upper()}:")
            for i, item in enumerate(items[:5], 1):  # Afficher les 5 premiers de chaque catégorie
                print(f"   {i}. {item}")
            if len(items) > 5:
                print(f"   ... et {len(items) - 5} de plus")
    
    # 3. Effectuer le matching
    print("\n=== RÉSULTATS DU MATCHING ===")
    result = api.match_competences_rome4(rome_code, user_skills)
    
    print(f"\n🎯 Score de matching: {result['match_score'] * 100:.1f}%")
    
    # Afficher les compétences correspondantes par catégorie
    print("\n✅ Compétences correspondantes:")
    for categorie, matches in result['matches_by_category'].items():
        if matches:
            print(f"\n🔹 {categorie.replace('_', ' ').title()}:")
            for match in matches:
                print(f"   ✓ {match}")
    
    # Afficher les compétences manquantes
    if result.get('missing_skills'):
        print("\n❌ Compétences clés manquantes:")
        for skill in result['missing_skills']:
            print(f"   • {skill}")
    
    # Afficher les contextes de travail
    if result.get('contextes_travail'):
        print("\n🏢 Contextes de travail:")
        for i, contexte in enumerate(result['contextes_travail'][:3], 1):
            print(f"   {i}. {contexte}")

if __name__ == "__main__":
    main()
