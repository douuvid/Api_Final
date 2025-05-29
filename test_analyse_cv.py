"""
Script de test pour l'analyse de CV
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent))

from france_travail.cv_analyzer import CVAnalyzer
from france_travail.client import FranceTravailAPI

def analyser_et_matcher(chemin_cv: str, code_rome: str = "M1805"):
    """Analyse un CV et le match avec des offres d'emploi"""
    # 1. Charger le CV
    with open(chemin_cv, 'r', encoding='utf-8') as f:
        contenu_cv = f.read()
    
    print("📄 CV analysé avec succès!")
    
    # 2. Analyser le CV
    print("\n🔍 Extraction des compétences...")
    analyseur = CVAnalyzer()
    resultats = analyseur.analyze(contenu_cv, 'text')
    
    print("\n✅ Compétences identifiées :")
    print("\n💻 Techniques :")
    for comp in resultats['competences_techniques']:
        print(f"- {comp}")
    
    print("\n🤝 Douces :")
    for comp in resultats['competences_douces']:
        print(f"- {comp}")
    
    # 3. Initialiser l'API France Travail
    print("\n🔌 Connexion à l'API France Travail...")
    load_dotenv()
    api = FranceTravailAPI(
        client_id=os.getenv("FRANCE_TRAVAIL_CLIENT_ID"),
        client_secret=os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")
    )
    
    # 4. Faire le matching
    print(f"\n🎯 Recherche de correspondances pour le code ROME: {code_rome}")
    resultat_matching = api.match_soft_skills(
        rome_code=code_rome,
        skills=resultats['competences_toutes']
    )
    
    # 5. Afficher les résultats
    print(f"\n📊 Score de matching: {resultat_matching['match_score']:.0%}")
    
    print("\n✅ Vos points forts:")
    for comp in resultat_matching['matching_skills']:
        print(f"- {comp}")
    
    if resultat_matching.get('missing_skills'):
        print("\n📈 Compétences à développer:")
        for comp in resultat_matching['missing_skills'][:3]:
            print(f"- {comp}")
    
    if resultat_matching.get('recommendations'):
        print("\n💡 Conseil:")
        print(f"- {resultat_matching['recommendations'][0]['suggestion']}")

if __name__ == "__main__":
    # Chemin vers le CV exemple
    chemin_cv = "exemples/cv_exemple.txt"
    
    # Code ROME pour développeur (M1805) par défaut
    code_rome = "M1805"
    
    # Si un argument est fourni, l'utiliser comme chemin de CV
    if len(sys.argv) > 1:
        chemin_cv = sys.argv[1]
    if len(sys.argv) > 2:
        code_rome = sys.argv[2]
    
    analyser_et_matcher(chemin_cv, code_rome)
