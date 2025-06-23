import logging
from .base_client import BaseClient

class RomeoClient(BaseClient):
    """
    Client pour l'API ROMEO v2 de France Travail.
    Permet de rapprocher un texte libre (intitulé de poste) à des appellations et codes ROME.
    """
    def __init__(self, client_id=None, client_secret=None, simulation=False):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            base_url="https://api.francetravail.io/partenaire/romeo/v2",
            scope="api_romeov2",
            simulation=simulation
        )
        self.request_delay = 1.0

    def predict_metiers(self, intitule: str, contexte: str = None, nb_results: int = 3):
        """
        Prédit les appellations métier du ROME à partir d'un intitulé de poste.

        Args:
            intitule (str): L'intitulé de poste à analyser.
            contexte (str, optional): Contexte pour affiner la recherche (secteur, etc.).
            nb_results (int, optional): Nombre de résultats souhaités.

        Returns:
            list: Une liste de prédictions ou None en cas d'erreur.
        """
        endpoint = "/predictionMetiers"
        payload = {
            "appellations": [
                {
                    "intitule": intitule,
                    "identifiant": "cli_request_1"
                }
            ],
            "options": {
                "nomAppelant": "france_travail_cli",
                "nbResultats": nb_results
            }
        }
        if contexte:
            payload["appellations"][0]["contexte"] = contexte

        logging.info(f"Recherche ROMEO pour l'intitulé : '{intitule}'")
        return self._make_request("POST", endpoint, json=payload)
