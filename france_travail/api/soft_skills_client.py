# /Users/davidravin/Desktop/Api_Final/france_travail/api/soft_skills_client.py
import logging
from .base_client import BaseClient

class SoftSkillsClient(BaseClient):
    """
    Client pour l'API Match via Soft Skills v1 de France Travail.
    Permet d'obtenir la liste des compétences comportementales pour un métier donné.
    """
    def __init__(self, client_id=None, client_secret=None, simulation=False):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            base_url="https://api.francetravail.io/partenaire/matchviasoftskills/v1",
            scope="api_matchviasoftskillsv1",
            simulation=simulation
        )
        self.request_delay = 1.0 / 2  # 2 appels/seconde

    def get_skills_for_job(self, rome_code: str):
        """
        Récupère la liste des soft skills pour un code ROME donné.

        Args:
            rome_code (str): Le code ROME du métier (5 caractères).

        Returns:
            dict: Un dictionnaire contenant les compétences ou None en cas d'erreur.
        """
        if not isinstance(rome_code, str) or len(rome_code) != 5:
            logging.error(f"Code ROME invalide fourni: {rome_code}")
            return None

        endpoint = "/professions/job_skills"
        params = {"code": rome_code}

        logging.info(f"Récupération des soft skills pour le code ROME: {rome_code}")
        # L'API attend un POST avec le code ROME en paramètre de requête.
        return self._make_request("POST", endpoint, params=params)
