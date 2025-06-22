"""
Test d'intégration du matching CV-offre
"""

import os
from dotenv import load_dotenv
from france_travail.client import FranceTravailAPI

def test_matching():
    # Charger les identifiants
    load_dotenv()
    
    # Initialiser l'API
    print("🔍 Initialisation de l'API France Travail...")
    api = FranceTravailAPI(
        client_id=os.getenv("FRANCE_TRAVAIL_CLIENT_ID"),
        client_secret=os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")
    )
    
    # Compétences du candidat
    competences = [
        "python", "javascript", "travail d'équipe",
        "gestion de projet", "méthodes agiles", "git"
    ]
    
    # Tester avec le code ROME pour développeur (M1805)
    print("\n🔄 Test de matching pour un développeur (M1805)...")
    resultat = api.match_soft_skills("M1805", competences)
    
    # Afficher les résultats
    print(f"\n✅ Résultats ({resultat.get('source', 'source inconnue')}):")
    print(f"📊 Score de matching: {resultat['match_score']:.0%}")
    
    print("\n🎯 Compétences correspondantes:")
    for comp in resultat['matching_skills']:
        print(f"- {comp}")
    
    if resultat.get('missing_skills'):
        print("\n🔍 Compétences recommandées:")
        for comp in resultat['missing_skills'][:3]:  # Afficher max 3 compétences
            print(f"- {comp}")
    
    if resultat.get('recommendations'):
        print("\n💡 Conseil:")
        print(f"- {resultat['recommendations'][0]['suggestion']}")
    
    return resultat

if __name__ == "__main__":
    test_matching()
