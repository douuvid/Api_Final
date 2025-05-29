"""
Client alternatif pour l'API France Travail.

Ce module fournit une implémentation alternative qui utilise les API disponibles
de France Travail pour effectuer du matching de compétences basé sur l'analyse
des offres d'emploi.
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
import re

class FranceTravailAlternativeAPI:
    """
    Solution alternative utilisant les APIs disponibles de France Travail
    pour créer un système de matching des compétences.
    """
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = None
        
        # URLs confirmées comme fonctionnelles
        self.auth_url = "https://entreprise.pole-emploi.fr/connexion/oauth2/access_token"
        self.base_url = "https://api.francetravail.io/partenaire"
        
        # Cache pour éviter les appels répétés
        self.cache = {
            'metiers': {},
            'appellations': {},
            'competences': {}
        }
    
    def authenticate(self) -> bool:
        """Authentification avec le scope qui fonctionne."""
        import base64
        
        if self.is_token_valid():
            return True
        
        auth_string = f"{self.client_id}:{self.client_secret}"
        base64_auth = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {base64_auth}',
            'Accept': 'application/json'
        }
        
        data = {
            'grant_type': 'client_credentials',
            'scope': 'api_offresdemploiv2 o2dsoffre',
            'realm': '/partenaire'
        }
        
        try:
            response = requests.post(
                f"{self.auth_url}?realm=%2Fpartenaire",
                headers=headers,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                from datetime import datetime, timedelta
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
                print("✅ Authentification réussie")
                return True
            else:
                print(f"❌ Erreur d'authentification: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        return False
    
    def is_token_valid(self) -> bool:
        """Vérifie la validité du token."""
        if not self.access_token or not self.token_expiry:
            return False
        return datetime.now() < self.token_expiry
    
    def get_job_details_by_rome(self, rome_code: str) -> Dict:
        """
        Récupère les détails d'un métier via le code ROME.
        Utilise les APIs disponibles pour construire un profil de compétences.
        """
        if not self.authenticate():
            return {}
        
        if rome_code in self.cache['metiers']:
            return self.cache['metiers'][rome_code]
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        # Essayons plusieurs endpoints pour récupérer des infos
        job_data = {}
        
        # 1. Essai avec l'API des offres (pour récupérer des exemples)
        try:
            search_url = f"{self.base_url}/offresdemploi/v2/offres/search"
            params = {
                'codeROME': rome_code,
                'range': '0-9'  # Limite à 10 résultats
            }
            
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                offers_data = response.json()
                job_data['offers_sample'] = offers_data.get('resultats', [])
                print(f"✅ Récupéré {len(job_data['offers_sample'])} offres pour {rome_code}")
            else:
                print(f"⚠️ Offres non disponibles: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur récupération offres: {e}")
        
        # Cache le résultat
        self.cache['metiers'][rome_code] = job_data
        return job_data
    
    def extract_skills_from_offers(self, offers: List[Dict]) -> List[str]:
        """
        Extrait les compétences mentionnées dans les offres d'emploi.
        """
        skills = set()
        
        # Mots-clés techniques courants à rechercher
        tech_keywords = [
            'python', 'java', 'javascript', 'sql', 'html', 'css', 'react', 'angular',
            'node.js', 'php', 'c++', 'c#', '.net', 'spring', 'django', 'flask',
            'docker', 'kubernetes', 'aws', 'azure', 'git', 'jenkins', 'agile',
            'scrum', 'rest', 'api', 'microservices', 'mongodb', 'postgresql'
        ]
        
        # Compétences soft courantes
        soft_keywords = [
            'communication', 'leadership', 'travail d\'équipe', 'autonomie',
            'rigueur', 'organisation', 'créativité', 'adaptation', 'initiative',
            'relationnel', 'analyse', 'synthèse', 'négociation', 'pédagogie'
        ]
        
        all_keywords = tech_keywords + soft_keywords
        
        for offer in offers:
            # Recherche dans la description
            description = offer.get('description', '').lower()
            title = offer.get('intitule', '').lower()
            
            full_text = f"{description} {title}"
            
            for keyword in all_keywords:
                if keyword.lower() in full_text:
                    skills.add(keyword)
        
        return list(skills)
    
    def match_soft_skills(self, rome_code: str, user_skills: List[str]) -> Dict:
        """
        Implémentation alternative du matching des compétences.
        Utilise les données d'offres d'emploi pour déterminer les compétences requises.
        """
        
        print(f"🔍 Matching des compétences pour {rome_code}")
        
        # 1. Récupérer les données du métier
        job_data = self.get_job_details_by_rome(rome_code)
        
        if not job_data.get('offers_sample'):
            print("⚠️ Pas de données d'offres, utilisation de la simulation")
            return self._simulate_matching(rome_code, user_skills)
        
        # 2. Extraire les compétences des offres
        market_skills = self.extract_skills_from_offers(job_data['offers_sample'])
        
        if not market_skills:
            print("⚠️ Pas de compétences extraites, utilisation de la simulation")
            return self._simulate_matching(rome_code, user_skills)
        
        # 3. Calculer le matching
        user_skills_lower = [skill.lower().strip() for skill in user_skills]
        market_skills_lower = [skill.lower().strip() for skill in market_skills]
        
        # Compétences qui matchent exactement
        exact_matches = []
        for user_skill in user_skills_lower:
            for market_skill in market_skills_lower:
                if user_skill == market_skill or user_skill in market_skill or market_skill in user_skill:
                    exact_matches.append(user_skill)
                    break
        
        # Calcul du score
        match_score = len(exact_matches) / len(user_skills) if user_skills else 0
        
        # Compétences manquantes importantes
        missing_skills = [skill for skill in market_skills_lower 
                         if not any(user_skill in skill or skill in user_skill 
                                   for user_skill in user_skills_lower)]
        
        result = {
            'match_score': round(match_score, 2),
            'matching_skills': exact_matches,
            'market_skills': market_skills[:10],  # Top 10
            'missing_skills': missing_skills[:5],  # Top 5 manquantes
            'rome_code': rome_code.upper(),
            'source': 'france_travail_offers_analysis',
            'offers_analyzed': len(job_data['offers_sample']),
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Matching calculé: {match_score:.2f}")
        print(f"📊 {len(exact_matches)} compétences matchées sur {len(user_skills)}")
        
        return result
    
    def _simulate_matching(self, rome_code: str, skills: List[str]) -> Dict:
        """Simulation locale améliorée basée sur des données réelles."""
        
        # Base de données simplifiée par métier
        skills_by_rome = {
            'M1805': ['python', 'java', 'sql', 'javascript', 'git', 'travail d\'équipe', 'analyse'],
            'M1806': ['html', 'css', 'javascript', 'ux/ui', 'photoshop', 'créativité'],
            'M1810': ['project management', 'agile', 'scrum', 'leadership', 'communication'],
            'E1103': ['vente', 'relationnel', 'négociation', 'communication', 'autonomie'],
        }
        
        expected_skills = skills_by_rome.get(rome_code.upper(), 
                                           ['communication', 'travail d\'équipe', 'autonomie'])
        
        user_skills_lower = [s.lower() for s in skills]
        expected_skills_lower = [s.lower() for s in expected_skills]
        
        matches = [skill for skill in user_skills_lower 
                  if any(exp in skill or skill in exp for exp in expected_skills_lower)]
        
        score = len(matches) / len(skills) if skills else 0
        
        return {
            'match_score': round(score, 2),
            'matching_skills': matches,
            'expected_skills': expected_skills,
            'rome_code': rome_code.upper(),
            'source': 'simulation_enrichie',
            'timestamp': datetime.now().isoformat()
        }


def test_alternative_api():
    """Test de l'API alternative."""
    
    api = FranceTravailAlternativeAPI(
        client_id="PAR_cv_9137520f2b833ef0ce2913e412a819ddf8191bb97dd1b09f1a20f0e21c451deb",
        client_secret="cbc8a7310a011f18566360ce3865c7bffa995b11acc18b5ab844a61bc7954050"
    )
    
    print("=== TEST DE L'API ALTERNATIVE ===")
    
    # Test du matching
    result = api.match_soft_skills(
        rome_code="M1805",  # Développeur
        user_skills=["python", "travail d'équipe", "javascript", "communication"]
    )
    
    print("\n📊 RÉSULTAT DU MATCHING:")
    print(f"Score: {result['match_score']}")
    print(f"Compétences matchées: {result['matching_skills']}")
    print(f"Source: {result['source']}")
    
    if 'offers_analyzed' in result:
        print(f"Offres analysées: {result['offers_analyzed']}")
    
    return result


if __name__ == "__main__":
    test_alternative_api()