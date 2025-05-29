"""
Test de matching CV - Offre d'emploi spécifique
"""

import os
from dotenv import load_dotenv
from france_travail.cv_matching import CVMatchingService

def main():
    # Charger les identifiants
    load_dotenv()
    
    # Initialisation du service
    print("🔍 Initialisation du service de matching...")
    service = CVMatchingService(
        os.getenv("FRANCE_TRAVAIL_CLIENT_ID"),
        os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")
    )

    # Exemple de CV (à personnaliser)
    cv_text = """
    DÉVELOPPEUR FULL STACK - 5 ANS D'EXPÉRIENCE
    
    Compétences Techniques :
    - Langages : JavaScript, Python, Java
    - Frontend : React, Angular, HTML5, CSS3
    - Backend : Node.js, Django, Spring Boot
    - Base de données : MongoDB, PostgreSQL
    - DevOps : Docker, AWS, CI/CD
    
    Expériences Professionnelles :
    
    Développeur Senior - Entreprise Tech (2020-2023)
    - Leadership d'une équipe de 4 développeurs
    - Développement d'applications web évolutives
    - Collaboration étroite avec les équipes produit et design
    - Formation des nouveaux développeurs
    
    Développeur Full Stack - Startup (2018-2020)
    - Conception et développement de nouvelles fonctionnalités
    - Optimisation des performances côté client et serveur
    - Participation aux revues de code
    
    Formation :
    - Diplôme d'ingénieur en informatique
    - Certification AWS Solutions Architect
    
    Soft Skills :
    - Excellente communication écrite et orale
    - Capacité à travailler en équipe
    - Résolution créative de problèmes
    - Gestion du temps et organisation
    - Adaptation rapide aux nouvelles technologies
    """

    # Exemple d'offre d'emploi (à personnaliser)
    offre_emploi = """
    DÉVELOPPEUR FULL STACK SENIOR
    
    Description du poste :
    Nous recherchons un Développeur Full Stack expérimenté pour rejoindre notre équipe technique.
    Vous serez responsable du développement et de la maintenance de nos applications web.
    
    Missions :
    - Développer des fonctionnalités frontend et backend
    - Participer aux revues de code
    - Collaborer avec les équipes produit et design
    - Résoudre des problèmes techniques complexes
    - Encadrer les développeurs juniors
    
    Compétences requises :
    - Maîtrise de JavaScript/TypeScript et Python
    - Expérience avec React et Node.js
    - Connaissance des bases de données relationnelles et NoSQL
    - Expérience avec les services cloud (AWS de préférence)
    - Bonnes pratiques de développement (tests, intégration continue)
    
    Profil recherché :
    - 5+ ans d'expérience en développement full stack
    - Capacité à travailler en équipe
    - Excellentes compétences en communication
    - Leadership et esprit d'initiative
    - Capacité à former et encadrer
    - Créativité et résolution de problèmes
    - Organisation et gestion des priorités
    """

    # Analyse du matching
    print("\n🔄 Analyse du matching en cours...")
    resultat = service.analyze_cv_job_match(cv_text, offre_emploi)
    
    # Affichage des résultats
    print(f"\n📊 TAUX DE MATCHING: {resultat['matching_rate']}%")
    
    # Détails des compétences
    print("\n💼 COMPÉTENCES DÉTECTÉES DANS VOTRE CV:")
    for competence, score in sorted(resultat['cv_skills'].items(), key=lambda x: x[1], reverse=True):
        if score > 0:
            print(f"  - {competence.replace('_', ' ').title()}: {score:.0f}%")
    
    print("\n🎯 COMPÉTENCES REQUISES PAR L'OFFRE:")
    for competence, score in sorted(resultat['job_skills'].items(), key=lambda x: x[1], reverse=True):
        if score > 0:
            print(f"  - {competence.replace('_', ' ').title()}: {score:.0f}%")
    
    # Insights marché
    print(f"\n📈 ANALYSE DU MARCHÉ:")
    print(f"  • Offres similaires analysées: {resultat['market_insights']['similar_jobs_found']}")
    if resultat['market_insights']['top_demanded_skills']:
        print(f"  • Compétences les + demandées: {', '.join(resultat['market_insights']['top_demanded_skills'])}")
    
    # Recommandations
    if resultat['recommendations']:
        print("\n💡 CONSEILS POUR AMÉLIORER VOTRE CV:")
        for i, rec in enumerate(resultat['recommendations'], 1):
            print(f"\n  {i}. {rec['skill'].upper()} (écart: {rec['gap_percentage']:.0f}%)")
            print(f"     {rec['suggestion']}")
    
    print(f"\n✅ Analyse terminée à {resultat['analysis_timestamp']}")

if __name__ == "__main__":
    main()
