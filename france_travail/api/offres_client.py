# /Users/davidravin/Desktop/Api_Final/france_travail/api/offres_client.py
import logging
from collections import Counter
from typing import Dict
from .base_client import BaseClient

class OffresClient(BaseClient):
    """
    Client pour l'API Offres d'emploi v2 de France Travail.
    """
    def __init__(self, client_id=None, client_secret=None, simulation=False):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            base_url="https://api.emploi-store.fr/partenaire/offresdemploi/v2",
            scope="api_offresdemploiv2 o2dsoffre",
            simulation=simulation
        )
        self.request_delay = 1.0 / 10
        
        self.soft_skills_db = {
            'communication': {'weight': 0.2, 'keywords': ['communication', 'présentation', 'écoute', 'expression', 'dialogue', 'rédaction', 'oral', 'écrit', 'relationnel', 'contact']},
            'leadership': {'weight': 0.18, 'keywords': ['leadership', 'management', 'encadrement', 'direction', 'guide', 'chef', 'responsable', 'manager', 'animateur', 'coordinateur']},
            'travail_equipe': {'weight': 0.16, 'keywords': ['équipe', 'collaboration', 'coopération', 'collectif', 'partenariat', 'groupe', 'team', 'collaboratif', 'ensemble', 'solidaire']},
            'adaptabilite': {'weight': 0.14, 'keywords': ['adaptation', 'flexibilité', 'polyvalence', 'évolution', 'changement', 'flexible', 'polyvalent', 'évolutif', 'mobile', 'agile']},
            'creativite': {'weight': 0.12, 'keywords': ['créativité', 'innovation', 'imagination', 'original', 'inventif', 'créatif', 'innovant', 'créatrice', 'inspiration', 'artistique']},
            'resolution_problemes': {'weight': 0.1, 'keywords': ['résolution', 'problème', 'solution', 'analyse', 'diagnostic', 'résoudre', 'analyser', 'diagnostiquer', 'investiguer', 'dépannage']},
            'organisation': {'weight': 0.1, 'keywords': ['organisation', 'planification', 'gestion', 'structure', 'méthode', 'organisé', 'planifier', 'gérer', 'structurer', 'méthodique']}
        }

    def search_jobs(self, params):
        if self.simulation:
            logging.info("Mode simulation: retourne des données de recherche fictives.")
            return {"resultats": [{"id": "sim-123", "intitule": "Développeur Python (simulé)"}]}
        logging.info(f"Recherche d'offres avec les paramètres: {params}")
        return self._make_request('get', '/offres/search', params=params)

    def get_job_details(self, job_id):
        if self.simulation:
            logging.info(f"Mode simulation: retourne des détails fictifs pour l'offre {job_id}.")
            return {"id": job_id, "intitule": "Titre (simulé)", "description": "Description simulée."}
        logging.info(f"Récupération des détails pour l'offre: {job_id}")
        return self._make_request('get', f'/offres/{job_id}')

    def extract_soft_skills(self, text: str) -> Dict[str, float]:
        if not isinstance(text, str):
            return {}
        text_lower = text.lower()
        detected_skills = Counter()
        for skill, data in self.soft_skills_db.items():
            for keyword in data['keywords']:
                if keyword in text_lower:
                    detected_skills[skill] += 1
        total_mentions = sum(detected_skills.values())
        if total_mentions == 0:
            return {}
        return {skill: (count / total_mentions) * 100 for skill, count in detected_skills.items()}

    def calculate_matching_rate(self, cv_skills: Dict[str, float], job_skills: Dict[str, float]) -> float:
        if not job_skills:
            return 0.0
        total_score = 0
        total_weight = 0
        for skill, job_score in job_skills.items():
            cv_score = cv_skills.get(skill, 0)
            weight = self.soft_skills_db.get(skill, {}).get('weight', 0.1)
            match_ratio = min(cv_score / job_score, 1.0) if job_score > 0 else 0
            total_score += match_ratio * weight
            total_weight += weight
        return (total_score / total_weight) * 100 if total_weight > 0 else 0.0

    def analyze_cv_match(self, cv_text: str, job_id: str):
        job_details = self.get_job_details(job_id)
        if not job_details:
            raise ValueError(f"Impossible de récupérer les détails de l'offre {job_id}.")
        job_text = f"{job_details.get('intitule', '')} {job_details.get('description', '')}"
        cv_skills = self.extract_soft_skills(cv_text)
        job_skills = self.extract_soft_skills(job_text)
        matching_rate = self.calculate_matching_rate(cv_skills, job_skills)
        return {
            'matching_rate': round(matching_rate, 2),
            'cv_skills': cv_skills,
            'job_skills': job_skills,
            'job_title': job_details.get('intitule', 'N/A')
        }
