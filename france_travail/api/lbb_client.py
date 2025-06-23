# /Users/davidravin/Desktop/Api_Final/france_travail/api/lbb_client.py
import logging
import os
from dotenv import load_dotenv
from .base_client import BaseClient

class LBBClient(BaseClient):
    """
    Client pour l'API La Bonne Boite v1 de France Travail.
    """
    def __init__(self, client_id=None, client_secret=None, simulation=False):
        load_dotenv()
        resolved_client_id = client_id or os.getenv('FRANCE_TRAVAIL_CLIENT_ID')

        super().__init__(
            client_id=resolved_client_id,
            client_secret=client_secret,
            base_url="https://api.emploi-store.fr/partenaire/labonneboite/v1",
            scope=f"api_labonneboitev1 application_{resolved_client_id}",
            simulation=simulation
        )
        self.request_delay = 1.0

    def search_la_bonne_boite(self, rome_codes: str, latitude: float, longitude: float, distance: int = 10, naf_codes: str = None):
        """
        Recherche les entreprises à fort potentiel d'embauche.
        
        :param rome_codes: Code(s) ROME (séparés par des virgules).
        :param latitude: Latitude du point de recherche.
        :param longitude: Longitude du point de recherche.
        :param distance: Rayon de recherche en km (défaut: 10).
        :param naf_codes: Code(s) NAF (séparés par des virgules, optionnel).
        :return: Liste des entreprises.
        """
        if self.simulation:
            logging.info("Mode simulation: retourne des données LBB fictives.")
            return {"entreprises": [{"nom": "Super Boite (simulée)", "siret": "12345678901234"}]}

        endpoint = "/entreprises"
        params = {
            "rome_codes": rome_codes,
            "latitude": latitude,
            "longitude": longitude,
            "distance": distance,
        }
        if naf_codes:
            params["naf_codes"] = naf_codes
            
        logging.info(f"Recherche La Bonne Boite avec les paramètres: {params}")
        return self._make_request('get', endpoint, params=params)
