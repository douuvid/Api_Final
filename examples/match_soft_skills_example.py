"""
Exemple d'utilisation de l'API de matching par soft skills de France Travail.

Ce script montre comment utiliser la méthode match_soft_skills pour évaluer
la correspondance entre des compétences douces et un métier spécifique.
"""
import os
import sys
from dotenv import load_dotenv

# Ajouter le répertoire parent au chemin d'import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from france_travail import FranceTravailAPI

def match_skills_example():
    # Charger les variables d'environnement
    load_dotenv()
    
    # Récupérer les identifiants
    client_id = os.getenv("FRANCE_TRAVAIL_CLIENT_ID")
    client_secret = os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("ERREUR: Veuillez configurer FRANCE_TRAVAIL_CLIENT_ID et FRANCE_TRAVAIL_CLIENT_SECRET dans le fichier .env")
        print("Créez un fichier .env à la racine du projet avec ces variables d'environnement.")
        return
    
    # Initialiser le client API
    print("Connexion à l'API France Travail...")
    api = FranceTravailAPI(client_id, client_secret)
    
    # S'authentifier
    if not api.authenticate():
        print("Échec de l'authentification")
        return

    # Exemple de code ROME pour un métier (ici: Développeur informatique)
    rome_code = "M1805"
    
    # Compétences douces à évaluer
    soft_skills = [
        "communication",
        "travail d'équipe",
        "résolution de problèmes",
        "autonomie",
        "créativité",
        "gestion du temps",
        "adaptabilité"
    ]
    
    print(f"\nÉvaluation des compétences pour le métier avec le code ROME: {rome_code}")
    print("Compétences évaluées:", ", ".join(soft_skills))
    
    # Effectuer le matching
    print("\nRecherche de correspondances en cours...")
    result = api.match_soft_skills(rome_code, soft_skills)
    
    # Afficher les résultats
    if not result:
        print("Aucun résultat trouvé ou erreur lors de la requête.")
        return
    
    print("\n=== RÉSULTATS DU MATCHING ===")
    
    # Afficher les compétences pertinentes
    if 'matching_skills' in result and result['matching_skills']:
        print("\nCompétences pertinentes pour ce métier:")
        for skill in result['matching_skills']:
            print(f"- {skill['name']} (pertinence: {skill.get('relevance', 'N/A')})")
    
    # Afficher le score global de correspondance
    if 'match_score' in result:
        print(f"\nScore global de correspondance: {result['match_score']:.1%}")
    
    # Afficher les compétences manquantes
    if 'missing_skills' in result and result['missing_skills']:
        print("\nCompétences importantes manquantes:")
        for skill in result['missing_skills']:
            print(f"- {skill['name']} (importance: {skill.get('importance', 'N/A')})")
    
    # Afficher des recommandations
    if 'recommendations' in result and result['recommendations']:
        print("\nRecommandations:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"{i}. {rec}")

if __name__ == "__main__":
    match_skills_example()
