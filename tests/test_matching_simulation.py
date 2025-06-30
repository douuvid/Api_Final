"""
Test de simulation du matching CV-offre

Ce script simule le comportement attendu de l'API de matching avec des données factices.
"""

import json
import random
from typing import Dict, List, Optional

class MockFranceTravailAPI:
    """Classe simulée pour tester le matching CV-offre"""
    
    def __init__(self):
        # Compétences communes recherchées pour un développeur
        self.common_skills = {
            'developpeur': [
                'programmation', 'algorithmes', 'résolution de problèmes',
                'travail d\'équipe', 'communication', 'autonomie', 'adaptabilité',
                'veille technologique', 'anglais technique'
            ],
            'designer': [
                'créativité', 'sens esthétique', 'maîtrise des outils graphiques',
                'travail d\'équipe', 'communication', 'gestion de projet',
                'veille tendance', 'anglais technique'
            ]
        }
    
    def match_soft_skills(self, rome_code: str, skills: List[str]) -> Optional[Dict]:
        """Simule le matching de compétences"""
        # Validation du code ROME
        if not rome_code or not rome_code[0].isalpha() or len(rome_code) != 5:
            raise ValueError("Code ROME invalide")
        
        # Déterminer le métier cible basé sur le code ROME
        job_type = 'developpeur' if rome_code.startswith('M18') else 'designer'
        
        # Nettoyer les compétences en entrée
        skills = [s.lower().strip() for s in skills if s.strip()]
        
        # Calculer les correspondances
        matching_skills = [s for s in skills if s in self.common_skills[job_type]]
        missing_skills = [s for s in self.common_skills[job_type] if s not in skills]
        
        # Calculer un score de matching (entre 0 et 1)
        score = len(matching_skills) / len(self.common_skills[job_type])
        
        # Générer des recommandations
        recommendations = []
        if missing_skills:
            recommendations.append({
                'skill': random.choice(missing_skills),
                'suggestion': f"Cette compétence est très demandée pour les postes de {job_type}",
                'importance': 'haute'
            })
        
        return {
            'match_score': round(score, 2),
            'matching_skills': matching_skills,
            'missing_skills': missing_skills[:3],  # Limiter à 3 compétences manquantes
            'recommendations': recommendations,
            'job_type': job_type,
            'status': 'simulation'
        }

def main():
    # Initialiser le client simulé
    api = MockFranceTravailAPI()
    
    # Exemple de compétences d'un candidat
    candidat_skills = [
        'programmation', 'algorithmes', 'travail d\'équipe',
        'gestion de projet', 'méthodes agiles', 'git'
    ]
    
    # Tester le matching pour un poste de développeur (code ROME M1805)
    print("🔍 Test de matching pour un développeur (M1805)")
    resultat = api.match_soft_skills('M1805', candidat_skills)
    
    # Afficher les résultats
    print(f"\n📊 Score de matching: {resultat['match_score']:.0%}")
    
    print("\n✅ Compétences correspondantes:")
    for comp in resultat['matching_skills']:
        print(f"- {comp}")
    
    if resultat['missing_skills']:
        print("\n⚠️  Compétences manquantes recommandées:")
        for comp in resultat['missing_skills']:
            print(f"- {comp}")
    
    if resultat['recommendations']:
        print("\n💡 Recommandation:")
        for rec in resultat['recommendations']:
            print(f"- {rec['suggestion']} ({rec['skill']})")
    
    # Afficher les données brutes pour analyse
    print("\n📋 Données complètes:")
    print(json.dumps(resultat, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
