import logging
from .base_client import BaseClient

class ContexteTravailClient(BaseClient):
    """
    Client pour l'API ROME V4.0 - Situations de travail.
    Permet de récupérer des informations sur les contextes et conditions de travail.
    """
    def __init__(self, client_id: str, client_secret: str, simulation: bool = False):
        base_url = "https://api.francetravail.io/partenaire/rome-contextes-travail"
        # Les scopes requis par l'API
        scope = "api_rome-contextes-travailv1,nomenclatureRome"
        super().__init__(base_url, client_id, client_secret, scope, simulation)

    def lister_contextes(self, champs: str = None):
        """
        Récupère la liste de tous les contextes de travail.
        
        Args:
            champs (str, optional): Liste des champs à retourner, séparés par des virgules 
                                  (ex: "libelle,code,categorie"). Par défaut, tous les champs sont retournés.
        
        Returns:
            list: Une liste de dictionnaires, chaque dictionnaire représentant un contexte de travail.
        """
        endpoint = "/v1/situations-travail/contexte-travail"
        params = {}
        if champs:
            params['champs'] = champs
        
        logging.info("Récupération de la liste des contextes de travail.")
        return self._make_request("GET", endpoint, params=params)

    def lire_contexte(self, code: str, champs: str = None):
        """
        Récupère les détails d'un contexte de travail par son code.
        
        Args:
            code (str): Le code du contexte de travail.
            champs (str, optional): Liste des champs à retourner.
        
        Returns:
            dict: Un dictionnaire contenant les détails du contexte de travail.
        """
        endpoint = f"/v1/situations-travail/contexte-travail/{code}"
        params = {}
        if champs:
            params['champs'] = champs

        logging.info(f"Récupération du contexte de travail pour le code: {code}")
        return self._make_request("GET", endpoint, params=params)

    def lire_version(self):
        """
        Récupère la version actuelle du référentiel ROME.
        
        Returns:
            dict: Un dictionnaire avec la version et la date de modification.
        """
        endpoint = "/v1/situations-travail/version"
        logging.info("Récupération de la version du ROME.")
        return self._make_request("GET", endpoint)
