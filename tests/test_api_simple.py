"""
Test simple de l'API France Travail
"""

import os
import json
from dotenv import load_dotenv
from france_travail.client import FranceTravailAPI

def test_authentication():
    """Teste la connexion à l'API"""
    print("🔍 Test d'authentification...")
    api = FranceTravailAPI(
        client_id=os.getenv("FRANCE_TRAVAIL_CLIENT_ID"),
        client_secret=os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")
    )
    
    if api.authenticate():
        print("✅ Authentification réussie!")
        return True
    else:
        print("❌ Échec de l'authentification")
        return False

def test_job_search():
    """Teste la recherche d'offres d'emploi"""
    print("\n🔍 Test de recherche d'offres d'emploi...")
    api = FranceTravailAPI(
        client_id=os.getenv("FRANCE_TRAVAIL_CLIENT_ID"),
        client_secret=os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")
    )
    
    # Recherche simple d'offres de développeur
    params = {
        'motsCles': 'développeur',
        'range': '0-4'  # 5 premiers résultats
    }
    
    result = api.search_jobs(params)
    
    if result and 'resultats' in result:
        print(f"✅ {len(result['resultats'])} offres trouvées :")
        for i, offre in enumerate(result['resultats'], 1):
            print(f"\n📌 Offre #{i}:")
            print(f"   Poste: {offre.get('intitule', 'Non spécifié')}")
            print(f"   Entreprise: {offre.get('entreprise', {}).get('nom', 'Non spécifié')}")
            print(f"   Lieu: {offre.get('lieuTravail', {}).get('libelle', 'Non spécifié')}")
            print(f"   Type de contrat: {offre.get('typeContratLibelle', 'Non spécifié')}")
        return True
    else:
        print("❌ Aucune offre trouvée ou erreur lors de la recherche")
        return False

def main():
    """Fonction principale"""
    load_dotenv()
    
    if not os.getenv("FRANCE_TRAVAIL_CLIENT_ID") or not os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET"):
        print("❌ Veuillez configurer vos identifiants dans le fichier .env")
        print("   FRANCE_TRAVAIL_CLIENT_ID=votre_id")
        print("   FRANCE_TRAVAIL_CLIENT_SECRET=votre_secret")
        return
    
    print("=== Test de l'API France Travail ===\n")
    
    # Test d'authentification
    if not test_authentication():
        return
    
    # Test de recherche d'offres
    test_job_search()
    
    print("\n=== Fin des tests ===")

if __name__ == "__main__":
    main()
