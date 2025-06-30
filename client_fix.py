"""
Client France Travail API - Version corrigée
"""
import requests
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional, Union

class FranceTravailAPI:
    """Client pour l'API France Travail."""
    
    def __init__(self, client_id: str, client_secret: str):
        """Initialise le client avec les identifiants."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = None
        self.base_url = "https://api.emploi-store.fr/partenaire"

    def authenticate(self) -> bool:
        """Authentifie le client et stocke le token d'accès."""
        try:
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'api_offresdemploiv2 o2dsoffre'
            }
            response = requests.post(
                'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token',
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)  # 1 minute de marge
            return True
            
        except Exception as e:
            print(f"❌ Erreur d'authentification: {e}")
            return False

    def _ensure_authenticated(self) -> bool:
        """Vérifie et renouvelle l'authentification si nécessaire."""
        if not self.access_token or (self.token_expiry and datetime.now() >= self.token_expiry):
            return self.authenticate()
        return True

    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """Récupère les détails d'une offre d'emploi par son ID."""
        if not self._ensure_authenticated():
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/offresdemploi/v2/offres/{job_id}",
                headers={'Authorization': f'Bearer {self.access_token}'}
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la récupération de l'offre: {e}")
            return None

    def search_jobs(self, params: Dict) -> Optional[Dict]:
        """Recherche des offres d'emploi avec les paramètres donnés."""
        if not self._ensure_authenticated():
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/offresdemploi/v2/offres/search",
                params=params,
                headers={'Authorization': f'Bearer {self.access_token}'}
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la recherche d'offres: {e}")
            return None

    def match_soft_skills(self, rome_code: str, skills: List[str]) -> Optional[Dict]:
        """Fait correspondre des compétences avec un code ROME."""
        # Validation des entrées
        if not rome_code or not isinstance(rome_code, str) or len(rome_code) != 5:
            raise ValueError("Le code ROME doit être une chaîne de 5 caractères")
        
        if not skills or not isinstance(skills, list) or not all(isinstance(s, str) for s in skills):
            raise ValueError("Les compétences doivent être fournies sous forme de liste de chaînes")
        
        # Récupération des offres pour ce code ROME
        job_offers = self.search_jobs({"rome": rome_code, "range": "0-9"})
        
        # Si pas de résultats ou erreur API, on utilise une simulation
        if not job_offers or 'resultats' not in job_offers or not job_offers['resultats']:
            return self._simulate_soft_skills_match(rome_code, skills)
        
        # Logique de matching réelle ici...
        # (simplifiée pour l'exemple)
        matched_skills = [s for s in skills if len(s) > 3]  # Exemple simpliste
        
        return {
            'match_score': len(matched_skills) / max(len(skills), 1),
            'matching_skills': [{'name': s, 'relevance': 0.9} for s in matched_skills],
            'missing_skills': [],
            'recommendations': []
        }
    
    def _simulate_soft_skills_match(self, rome_code: str, skills: List[str]) -> Dict:
        """Simule un matching de compétences pour les tests."""
        print("⚠️ Pas de données d'offres, utilisation de la simulation")
        
        # Compétences attendues pour ce code ROME (simulé)
        expected_skills = {
            'M1805': ['python', 'java', 'sql', 'javascript', 'git', 'travail d\'équipe', 'analyse']
        }.get(rome_code, ['programmation', 'analyse', 'travail en équipe'])
        
        # Calcul du score de correspondance
        matched = [s for s in skills if any(es.lower() in s.lower() for es in expected_skills)]
        score = len(matched) / max(len(expected_skills), 1)
        
        return {
            'match_score': min(score, 1.0),  # S'assurer que le score ne dépasse pas 1.0
            'matching_skills': [{'name': s, 'relevance': 0.9} for s in matched],
            'missing_skills': [s for s in expected_skills if not any(s in m for m in matched)],
            'recommendations': [
                f"Développez vos compétences en {s}" 
                for s in expected_skills 
                if not any(s in m for m in matched)
            ][:3],  # Limiter à 3 recommandations
            'rome_code': rome_code,
            'expected_skills': expected_skills,
            'source': 'simulation_enrichie',
            'timestamp': datetime.now().isoformat()
        }

# Exemple d'utilisation
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    client = FranceTravailAPI(
        client_id=os.getenv("FRANCE_TRAVAIL_CLIENT_ID"),
        client_secret=os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")
    )
    
    # Test de recherche d'offres
    print("🔍 Recherche d'offres pour 'développeur' à Paris...")
    jobs = client.search_jobs({"motsCles": "développeur", "commune": "75056"})
    print(f"📊 {len(jobs.get('resultats', []))} offres trouvées" if jobs else "❌ Aucune offre trouvée")
    
    # Test de matching de compétences
    print("\n🔍 Test de matching de compétences...")
    match = client.match_soft_skills(
        "M1805", 
        ["Python", "Travail d'équipe", "Gestion de projet"]
    )
    if match:
        print(f"✅ Score de correspondance: {match['match_score']*100:.1f}%")
        print(f"📌 Compétences correspondantes: {[m['name'] for m in match['matching_skills']]}")
        if match['recommendations']:
            print("💡 Recommandations:", "\n   - ".join([""] + match['recommendations']))
