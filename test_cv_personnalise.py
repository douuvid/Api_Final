"""
Test de matching avec un CV et une offre personnalisés
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

    # ===== VOTRE CV PERSONNALISÉ =====
    cv_text = """
    MARIE DUPONT
    marie.dupont@email.com | 06 12 34 56 78 | linkedin.com/in/mariedupont
    
    DÉVELOPPEUSE FULL STACK - 4 ANS D'EXPÉRIENCE
    
    COMPÉTENCES TECHNIQUES :
    - Langages : JavaScript, Python, HTML5, CSS3
    - Frameworks : React, Node.js, Express, Django
    - Bases de données : MongoDB, PostgreSQL
    - Outils : Git, Docker, AWS, Jest
    - Méthodologies : Agile/Scrum, TDD
    
    EXPÉRIENCE PROFESSIONNELLE :
    
    Développeuse Full Stack - TechSolutions (2021-Présent)
    - Développement d'applications web avec React et Node.js
    - Refonte de l'interface utilisateur améliorant l'expérience client de 40%
    - Collaboration avec une équipe de 6 développeurs en méthode agile
    - Formation de 3 développeurs juniors
    
    Développeuse Frontend - WebAgency (2019-2021)
    - Création d'interfaces utilisateur réactives
    - Optimisation des performances réduisant le temps de chargement de 30%
    - Participation aux revues de code hebdomadaires
    
    FORMATION :
    - Diplôme d'ingénieur en informatique - EPITECH (2019)
    - Certification AWS Certified Developer (2022)
    
    PROJETS PERSONNELS :
    - Application de gestion de tâches avec authentification
    - Site e-commerce avec système de paiement
    
    LANGUES :
    - Français : Langue maternelle
    - Anglais : Courant (TOEIC 920)
    
    CENTRES D'INTÉRÊT :
    - Veille technologique
    - Participation à des hackathons
    - Mentorat en développement web
    """

    # ===== OFFRE D'EMPLOI CIBLÉE =====
    offre_emploi = """
    DÉVELOPPEUR FULL STACK SENIOR (H/F)
    
    Notre entreprise innovante dans le secteur de la FinTech recherche un Développeur Full Stack Senior pour renforcer son équipe technique.
    
    MISSIONS PRINCIPALES :
    - Développer des fonctionnalités frontend et backend
    - Participer à l'architecture technique des applications
    - Collaborer avec les équipes produit et design
    - Mener des revues de code et assurer la qualité du code
    - Encadrer les développeurs juniors
    
    COMPÉTENCES REQUISES :
    - Formation supérieure en informatique (Bac+5)
    - 5 ans d'expérience en développement full stack
    - Maîtrise de JavaScript/TypeScript et Python
    - Expérience avec React et Node.js
    - Connaissance des bases de données relationnelles et NoSQL
    - Expérience avec les services cloud (AWS de préférence)
    - Bonnes pratiques de développement (tests, intégration continue)
    
    PROFIL RECHERCHÉ :
    - Capacité à travailler en équipe
    - Excellentes compétences en communication
    - Leadership et esprit d'initiative
    - Capacité à former et encadrer
    - Créativité et résolution de problèmes
    - Organisation et gestion des priorités
    - Autonomie et sens des responsabilités
    
    CONDITIONS :
    - CDI basé à Paris (télétravail partiel possible)
    - Rémunération attractive selon profil
    - Tickets restaurant
    - Mutuelle d'entreprise
    """

    # Analyse du matching
    print("\n🔄 Analyse du matching en cours...")
    resultat = service.analyze_cv_job_match(cv_text, offre_emploi)
    
    # Affichage des résultats
    print(f"\n📊 TAUX DE MATCHING: {resultat['matching_rate']}%")
    
    # Détails des compétences
    print("\n💼 VOS POINTS FORTS :")
    for competence, score in sorted(resultat['cv_skills'].items(), key=lambda x: x[1], reverse=True):
        if score >= 50:  # Afficher uniquement les compétences bien représentées
            print(f"  ✓ {competence.replace('_', ' ').title()} ({score:.0f}%)")
    
    print("\n🎯 POINTS À AMÉLIORER :")
    for competence, score in sorted(resultat['job_skills'].items(), key=lambda x: x[1], reverse=True):
        cv_score = resultat['cv_skills'].get(competence, 0)
        if score > cv_score and score > 30:  # Compétences importantes manquantes
            print(f"  ➔ {competence.replace('_', ' ').title()} (Vous: {cv_score:.0f}% | Requis: {score:.0f}%)")
    
    # Recommandations
    if resultat['recommendations']:
        print("\n💡 CONSEILS POUR AMÉLIORER VOTRE CANDIDATURE :")
        for i, rec in enumerate(resultat['recommendations'], 1):
            print(f"\n  {i}. {rec['skill'].upper()} (écart: {rec['gap_percentage']:.0f}%)")
            print(f"     {rec['suggestion']}")
    
    print(f"\n✅ Analyse terminée à {resultat['analysis_timestamp']}")

if __name__ == "__main__":
    main()
