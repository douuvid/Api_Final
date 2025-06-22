"""
Test de l'API de matching CV-Offre
"""

import os
import json
from dotenv import load_dotenv
from france_travail.client import FranceTravailAPI

def main():
    # Charger les identifiants
    load_dotenv()
    
    # Initialisation du client API
    print("🔌 Connexion à l'API France Travail...")
    api = FranceTravailAPI(
        client_id=os.getenv("FRANCE_TRAVAIL_CLIENT_ID"),
        client_secret=os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")
    )
    
    # Exemple de compétences à évaluer
    skills = ["communication", "leadership", "travail d'équipe", "résolution de problèmes"]
    rome_code = "M1805"  # Code ROME pour un développeur
    
    print(f"\n🔄 Test de l'API de matching avec le code ROME {rome_code}...")
    
    try:
        # Appel à l'API de matching
        result = api.match_soft_skills(rome_code, skills)
        
        # Affichage formaté des résultats
        print("\n✅ RÉSULTATS DU MATCHING :")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ ERREUR : {str(e)}")
        if hasattr(e, 'response'):
            print(f"Statut HTTP : {e.response.status_code}")
            print(f"Réponse : {e.response.text}")

if __name__ == "__main__":
    main()
