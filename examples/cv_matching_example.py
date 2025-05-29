"""
Exemple d'utilisation du service de matching CV avec l'API France Travail c'est ici que le texte cv doit etre mis
"""

import os
from dotenv import load_dotenv
from france_travail.cv_matching import CVMatchingService

def main():
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
    
    # Initialisation du service
    print("🔍 Initialisation du service de matching CV...")
    matching_service = CVMatchingService(client_id, client_secret)
    
    # Exemples de textes le cv doit etre mis ici
    cv_text = """
    Développeur Full Stack avec 5 ans d'expérience. 
    Excellentes compétences en communication et capacité à travailler en équipe.
    Leadership d'équipes techniques, résolution créative de problèmes complexes.
    Très organisé et capable de s'adapter rapidement aux nouvelles technologies.
    Expérience en management de projets agiles et formation d'équipes.
    """
    
    job_text = """
    Nous recherchons un Développeur Senior pour rejoindre notre équipe.
    Compétences requises : leadership technique, excellente communication,
    capacité à travailler en équipe, résolution de problèmes,
    adaptabilité aux changements technologiques, créativité dans les solutions,
    organisation et gestion de projets.
    """
    
    # Recherche d'offres similaires
    print("\n🔍 Recherche d'offres similaires...")
    similar_jobs = matching_service.search_similar_jobs(job_text, limit=2)  # Limité à 2 offres 
    
    # Affichage des offres similaires
    if similar_jobs:
        print(f"\n📋 {len(similar_jobs)} OFFRES SIMILAIRES TROUVÉES:")
        for i, job in enumerate(similar_jobs, 1):
            print(f"\n   📌 OFFRE {i}:")
            print(f"   • Titre: {job.get('intitule', 'Non spécifié')}")
            print(f"   • Entreprise: {job.get('entreprise', {}).get('nom', 'Non spécifié')}")
            print(f"   • Lieu: {job.get('lieuTravail', {}).get('libelle', 'Non spécifié')}")
            print(f"   • Type de contrat: {job.get('typeContratLibelle', 'Non spécifié')}")
            print(f"   • Description: {job.get('description', 'Non disponible')[:150]}...")
    else:
        print("\n⚠️ Aucune offre similaire trouvée.")
    
    # Analyse du matching
    print("\n🔄 Analyse du matching CV-Offre en cours...")
    result = matching_service.analyze_cv_job_match(cv_text, job_text)
    
    # Affichage des résultats
    print(f"\n📊 TAUX DE MATCHING: {result['matching_rate']}%")
    
    # Détails des compétences
    print("\n💼 COMPÉTENCES DU CV:")
    for skill, score in result['cv_skills'].items():
        if score > 0:  # Afficher uniquement les compétences détectées
            print(f"  - {skill.replace('_', ' ').title()}: {score:.0f}%")
    
    print("\n🎯 COMPÉTENCES REQUISES (enrichies marché):")
    for skill, score in result['job_skills'].items():
        if score > 0:  # Afficher uniquement les compétences pertinentes
            print(f"  - {skill.replace('_', ' ').title()}: {score:.0f}%")
    
    # Insights marché
    print(f"\n📈 INSIGHTS MARCHÉ:")
    insights = result['market_insights']
    print(f"  • Offres similaires analysées: {insights['similar_jobs_found']}")
    if insights['top_demanded_skills']:
        print(f"  • Compétences les + demandées: {', '.join(insights['top_demanded_skills'])}")
    
    # Recommandations
    if result['recommendations']:
        print("\n💡 RECOMMANDATIONS D'AMÉLIORATION:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"  {i}. {rec['skill']} (Écart: {rec['gap_percentage']:.0f}%)")
            print(f"     {rec['suggestion']}")
    
    print(f"\n✅ Analyse terminée à {result['analysis_timestamp']}")

if __name__ == "__main__":
    main()
