"""
Script de test pour vérifier la connexion à l'API France Travail
et le bon fonctionnement du matching par soft skills.
"""
import os
import sys
from dotenv import load_dotenv

# Ajouter le répertoire parent au chemin d'import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from france_travail import FranceTravailAPI

def test_connection(client_id: str, client_secret: str):
    """Teste la connexion à l'API et le matching par soft skills."""
    print("\n" + "="*50)
    print("TEST DE CONNEXION À L'API FRANCE TRAVAIL")
    print("="*50)
    
    # Initialisation du client
    print("\n1. Initialisation du client API...")
    api = FranceTravailAPI(client_id, client_secret)
    
    # Test d'authentification
    print("\n2. Test d'authentification...")
    if not api.authenticate():
        print("❌ Échec de l'authentification. Vérifiez vos identifiants.")
        return False
    
    print("✅ Authentification réussie")
    
    # Test du matching par soft skills
    print("\n3. Test du matching par soft skills...")
    rome_code = "M1805"  # Code ROME pour les développeurs
    skills = ["communication", "travail d'équipe", "résolution de problèmes"]
    
    print(f"   - Code ROME: {rome_code}")
    print(f"   - Compétences testées: {', '.join(skills)}")
    
    try:
        result = api.match_soft_skills(rome_code, skills)
        
        if result is None:
            print("❌ Aucun résultat ou erreur lors du matching")
            return False
            
        print("✅ Matching réussi !")
        print("\nRésultats du matching :")
        print(f"- Score de correspondance: {result.get('match_score', 0):.0%}")
        
        if 'matching_skills' in result and result['matching_skills']:
            print("\nCompétences pertinentes :")
            for skill in result['matching_skills']:
                print(f"  - {skill}")
                
        if 'missing_skills' in result and result['missing_skills']:
            print("\nCompétences à améliorer :")
            for skill in result['missing_skills']:
                print(f"  - {skill}")
                
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du matching: {str(e)}")
        return False

def main():
    """Fonction principale."""
    # Charger les variables d'environnement
    load_dotenv()
    
    # Récupérer les identifiants
    client_id = os.getenv("FRANCE_TRAVAIL_CLIENT_ID")
    client_secret = os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("ERREUR: Veuillez configurer les variables d'environnement suivantes :")
        print("  - FRANCE_TRAVAIL_CLIENT_ID")
        print("  - FRANCE_TRAVAIL_CLIENT_SECRET")
        print("\nCréez un fichier .env à la racine du projet avec ces variables.")
        return
    
    # Exécuter le test
    success = test_connection(client_id, client_secret)
    
    # Afficher le résultat final
    print("\n" + "="*50)
    print("RÉSULTAT DU TEST :", "✅ RÉUSSI" if success else "❌ ÉCHEC")
    print("="*50)

if __name__ == "__main__":
    main()
