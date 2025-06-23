# /Users/davidravin/Desktop/Api_Final/france_travail/api/offres_client.py
import logging
from collections import Counter
from typing import Dict
from .base_client import BaseClient

class OffresClient(BaseClient):
    """
    Client pour l'API Offres d'emploi v2 de France Travail.
    """
    def __init__(self, soft_skills_client, client_id=None, client_secret=None, simulation=False):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            base_url="https://api.emploi-store.fr/partenaire/offresdemploi/v2",
            scope="api_offresdemploiv2 o2dsoffre",
            simulation=simulation
        )
        self.request_delay = 1.0 / 10
        self.soft_skills_client = soft_skills_client

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

    def analyze_cv_match(self, cv_text: str, job_id: str):
        job_details = self.get_job_details(job_id)
        if not job_details or not job_details.get('romeCode'):
            raise ValueError(f"Impossible de récupérer le code ROME pour l'offre {job_id}.")

        rome_code = job_details['romeCode']
        job_skills_data = self.soft_skills_client.get_skills_for_job(rome_code)

        if not job_skills_data or 'skills' not in job_skills_data:
            raise ValueError(f"Impossible de récupérer les soft skills pour le code ROME {rome_code}.")

        job_skills = job_skills_data['skills']
        cv_text_lower = cv_text.lower()
        
        detected_skills = {}
        
        # Calculer le poids total des compétences requises
        total_weight = sum(s_data.get('score', 0) for s_key, s_data in job_skills.items())

        # Détecter les compétences du CV
        for skill_key, skill_data in job_skills.items():
            skill_summary = skill_data.get('summary')
            if skill_summary and skill_summary.lower() in cv_text_lower:
                detected_skills[skill_summary] = skill_data.get('score')

        # Calculer le taux de matching
        if total_weight > 0:
            # Mode pondéré: basé sur les scores de l'API
            logging.info("Calcul du matching en mode pondéré (scores API > 0).")
            weighted_score = sum(detected_skills.values())
            matching_rate = (weighted_score / total_weight) * 100
        else:
            # Mode non-pondéré: si l'API retourne des scores nuls, on fait un simple ratio
            logging.info("Calcul du matching en mode non-pondéré (scores API nuls).")
            num_required_skills = len(job_skills)
            num_found_skills = len(detected_skills)
            matching_rate = (num_found_skills / num_required_skills) * 100 if num_required_skills > 0 else 0

        return {
            'matching_rate': round(matching_rate, 2),
            'cv_skills': detected_skills,
            'job_skills': {s_data.get('summary'): s_data.get('score') for s_key, s_data in job_skills.items()},
            'job_title': job_details.get('intitule', 'N/A'),
            'rome_code': rome_code
        }
