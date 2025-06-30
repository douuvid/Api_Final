# /Users/davidravin/Desktop/Api_Final/france_travail/client.py

import os
import requests
import logging
import time
from dotenv import load_dotenv
from typing import Dict, List
from collections import Counter

# Configuration du logging pour voir ce qu'il se passe
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FranceTravailAPI:
    """
    Client API pour interagir avec l'API France Travail (version corrigée et fonctionnelle).
    Ce client gère l'authentification, les appels et la limitation de débit (rate limiting).
    """
    def __init__(self, client_id=None, client_secret=None, simulation=False):
        load_dotenv()
        self.client_id = client_id or os.getenv('FRANCE_TRAVAIL_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('FRANCE_TRAVAIL_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Les identifiants FRANCE_TRAVAIL_CLIENT_ID et FRANCE_TRAVAIL_CLIENT_SECRET sont requis.")

        # URLs et paramètres
        self.auth_url = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
        self.base_url = "https://api.emploi-store.fr/partenaire/offresdemploi/v2"
        self.scope = "api_offresdemploiv2 o2dsoffre"
        
        self.access_token = None
        self.simulation = simulation

        # --- Configuration du Rate Limiting ---
        # Limite pour l'API Offres d'emploi v2 : 10 appels/seconde
        self.request_delay = 1.0 / 10  # 0.1 seconde entre chaque appel
        self.last_request_time = 0

        # --- Base de données des Soft Skills (intégrée depuis cv_matching.py) ---
        self.soft_skills_db = {
            'communication': {
                'weight': 0.2,
                'keywords': ['communication', 'présentation', 'écoute', 'expression', 'dialogue', 'rédaction', 'oral', 'écrit', 'relationnel', 'contact']
            },
            'leadership': {
                'weight': 0.18,
                'keywords': ['leadership', 'management', 'encadrement', 'direction', 'guide', 'chef', 'responsable', 'manager', 'animateur', 'coordinateur']
            },
            'travail_equipe': {
                'weight': 0.16,
                'keywords': ['équipe', 'collaboration', 'coopération', 'collectif', 'partenariat', 'groupe', 'team', 'collaboratif', 'ensemble', 'solidaire']
            },
            'adaptabilite': {
                'weight': 0.14,
                'keywords': ['adaptation', 'flexibilité', 'polyvalence', 'évolution', 'changement', 'flexible', 'polyvalent', 'évolutif', 'mobile', 'agile']
            },
            'creativite': {
                'weight': 0.12,
                'keywords': ['créativité', 'innovation', 'imagination', 'original', 'inventif', 'créatif', 'innovant', 'créatrice', 'inspiration', 'artistique']
            },
            'resolution_problemes': {
                'weight': 0.1,
                'keywords': ['résolution', 'problème', 'solution', 'analyse', 'diagnostic', 'résoudre', 'analyser', 'diagnostiquer', 'investiguer', 'dépannage']
            },
            'organisation': {
                'weight': 0.1,
                'keywords': ['organisation', 'planification', 'gestion', 'structure', 'méthode', 'organisé', 'planifier', 'gérer', 'structurer', 'méthodique']
            }
        }

    def _authenticate(self):
        """
        S'authentifie auprès de l'API pour obtenir un token d'accès.
        """
        logging.info("Tentative d'authentification auprès de France Travail...")
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.scope
        }
        
        params = {
            'realm': '/partenaire'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            response = requests.post(self.auth_url, params=params, data=data, headers=headers, timeout=15)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            
            if not self.access_token:
                logging.error("Le token d'accès n'a pas été trouvé dans la réponse.")
                return False
                
            logging.info("Authentification réussie.")
            return True

        except requests.exceptions.HTTPError as e:
            logging.error(f"Erreur HTTP lors de l'authentification: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logging.error(f"Une erreur inattendue est survenue lors de l'authentification: {e}")
            return False

    def _make_request(self, method, endpoint, **kwargs):
        """
        Méthode générique pour effectuer des requêtes à l'API, avec gestion du rate limiting.
        """
        if not self.access_token and not self._authenticate():
            return None

        # --- Gestion du Rate Limiting ---
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_delay:
            sleep_time = self.request_delay - elapsed
            logging.info(f"Rate limiting: pause de {sleep_time:.2f}s pour respecter la limite de 10 appels/s.")
            time.sleep(sleep_time)
        
        # Mettre à jour le temps du dernier appel avant de faire la requête
        self.last_request_time = time.time()

        url = f"{self.base_url}{endpoint}"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers

        try:
            response = requests.request(method, url, **kwargs)
            
            if response.status_code == 401:
                logging.warning("Token expiré (401). Tentative de ré-authentification.")
                self.access_token = None
                if self._authenticate():
                    kwargs['headers']['Authorization'] = f'Bearer {self.access_token}'
                    # On ne refait pas de pause pour la nouvelle tentative
                    response = requests.request(method, url, **kwargs)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            logging.error(f"Erreur HTTP pour {method.upper()} {url}: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logging.error(f"Erreur pour {method.upper()} {url}: {e}")
            return None

    def search_jobs(self, params):
        """
        Recherche des offres d'emploi.
        """
        if self.simulation:
            logging.info("Mode simulation: retourne des données de recherche fictives.")
            return {"resultats": [{"id": "sim-123", "intitule": "Développeur Python (simulé)"}]}
            
        logging.info(f"Recherche d'offres avec les paramètres: {params}")
        return self._make_request('get', '/offres/search', params=params)

    def get_job_details(self, job_id):
        """
        Récupère les détails d'une offre d'emploi par son ID.
        """
        if self.simulation:
            logging.info(f"Mode simulation: retourne des détails fictifs pour l'offre {job_id}.")
            return {"id": job_id, "intitule": "Titre (simulé)", "description": "Description simulée."}
            
        logging.info(f"Récupération des détails pour l'offre: {job_id}")
        return self._make_request('get', f'/offres/{job_id}')

    # --- Méthodes de Matching de CV (intégrées depuis cv_matching.py) ---

    def extract_soft_skills(self, text: str) -> Dict[str, float]:
        """
        Extrait et quantifie les soft skills d'un texte.
        """
        if not isinstance(text, str):
            return {}

        text_lower = text.lower()
        detected_skills = Counter()

        for skill, data in self.soft_skills_db.items():
            for keyword in data['keywords']:
                if keyword in text_lower:
                    detected_skills[skill] += 1
        
        # Normalisation des scores
        total_mentions = sum(detected_skills.values())
        if total_mentions == 0:
            return {}

        skill_scores = {skill: (count / total_mentions) * 100 for skill, count in detected_skills.items()}
        return skill_scores

    def calculate_matching_rate(self, cv_skills: Dict[str, float], job_skills: Dict[str, float]) -> float:
        """
        Calcule le taux de matching entre les compétences d'un CV et d'une offre.
        """
        if not job_skills:
            return 0.0

        total_score = 0
        total_weight = 0

        for skill, job_score in job_skills.items():
            cv_score = cv_skills.get(skill, 0)
            weight = self.soft_skills_db.get(skill, {}).get('weight', 0.1)
            
            # Le score est la proportion de la compétence du CV par rapport à celle de l'offre
            match_ratio = min(cv_score / job_score, 1.0) if job_score > 0 else 0
            total_score += match_ratio * weight
            total_weight += weight

        return (total_score / total_weight) * 100 if total_weight > 0 else 0.0

    def analyze_cv_match(self, cv_text: str, job_id: str):
        """
        Analyse la correspondance entre un CV et une offre d'emploi.
        """
        # 1. Récupérer les détails de l'offre
        job_details = self.get_job_details(job_id)
        if not job_details:
            raise ValueError(f"Impossible de récupérer les détails de l'offre {job_id}.")

        job_text = f"{job_details.get('intitule', '')} {job_details.get('description', '')}"

        # 2. Extraire les compétences du CV et de l'offre
        cv_skills = self.extract_soft_skills(cv_text)
        job_skills = self.extract_soft_skills(job_text)

        # 3. Calculer le score de matching
        matching_rate = self.calculate_matching_rate(cv_skills, job_skills)

        return {
            'matching_rate': round(matching_rate, 2),
            'cv_skills': cv_skills,
            'job_skills': job_skills,
            'job_title': job_details.get('intitule', 'N/A')
        }
