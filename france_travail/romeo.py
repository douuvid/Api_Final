"""
Client pour l'API ROMEO v2 de France Travail

Ce module fournit une interface pour interagir avec l'API ROMEO qui permet
de rechercher et de récupérer des informations sur les entreprises.
"""

import base64
import json
import time
from typing import Dict, Optional, Any, List, Union
import requests
from datetime import datetime, timedelta


class RomeoAPI:
    """
    Client pour l'API ROMEO v2 de France Travail.
    
    Cette classe permet d'interagir avec l'API ROMEO qui fournit des informations
    sur les entreprises en France. L'API est limitée à 2 appels par seconde.
    
    Args:
        client_id (str): Identifiant client de l'API ROMEO
        client_secret (str): Clé secrète de l'API ROMEO
    """
    
    def __init__(self, client_id: str, client_secret: str):
        """Initialise le client API ROMEO avec les identifiants fournis."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api.romeo.fr/v2"
        self.rate_limit = 2  # 2 appels par seconde
        self.rate_limit_interval = 1.0  # en secondes
        self.last_calls: List[float] = []
        
        # Headers par défaut
        self.default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'FranceTravail-API-Client/1.0'
        }
        
        # Gestion du token d'authentification
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    def _generate_auth_token(self) -> str:
        """Génère un token d'authentification pour l'API ROMEO."""
        timestamp = int(time.time())
        payload = {
            'client_id': self.client_id,
            'timestamp': timestamp
        }
        return base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Retourne les en-têtes d'authentification."""
        return {
            **self.default_headers,
            'Authorization': f'Bearer {self._generate_auth_token()}',
            'X-Client-ID': self.client_id
        }
    
    def _check_rate_limit(self):
        """Vérifie et applique la limite de taux d'appel (2 appels/seconde)."""
        now = time.time()
        
        # Supprime les appels plus vieux que l'intervalle
        self.last_calls = [t for t in self.last_calls if now - t < self.rate_limit_interval]
        
        # Si on a atteint la limite, on attend
        if len(self.last_calls) >= self.rate_limit:
            sleep_time = self.rate_limit_interval - (now - self.last_calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # On enregistre l'appel actuel
        self.last_calls.append(time.time())
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Effectue une requête à l'API ROMEO avec gestion des erreurs et du rate limiting.
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            endpoint: Point de terminaison de l'API
            **kwargs: Arguments supplémentaires pour requests.request()
            
        Returns:
            La réponse JSON de l'API
            
        Raises:
            requests.HTTPError: Si la requête échoue
        """
        self._check_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        headers = {**self._get_auth_headers(), **kwargs.pop('headers', {})}
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Erreur lors de l'appel à l'API ROMEO: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" - {e.response.status_code} - {e.response.text}"
            raise requests.HTTPError(error_msg) from e

    # ===== MÉTHODES DE L'API =====
    
    def search_companies(self, **criteria) -> Dict[str, Any]:
        """
        Recherche des entreprises selon des critères donnés.
        
        Args:
            **criteria: Critères de recherche (nom, siret, siren, ville, etc.)
            
        Returns:
            Un dictionnaire contenant les résultats de la recherche
        """
        params = {k: v for k, v in criteria.items() if v is not None}
        return self._make_request('GET', '/entreprises/search', params=params)
    
    def get_company_by_siret(self, siret: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une entreprise par son SIRET.
        
        Args:
            siret: Numéro SIRET de l'entreprise
            
        Returns:
            Les détails de l'entreprise
        """
        if not siret:
            raise ValueError("Le SIRET est obligatoire")
        return self._make_request('GET', f'/entreprises/{siret}')
    
    def get_company_by_siren(self, siren: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une entreprise par son SIREN.
        
        Args:
            siren: Numéro SIREN de l'entreprise
            
        Returns:
            Les détails de l'entreprise
        """
        if not siren:
            raise ValueError("Le SIREN est obligatoire")
        return self._make_request('GET', f'/entreprises/siren/{siren}')
    
    def search_companies_by_location(
        self,
        latitude: float,
        longitude: float,
        radius: int = 10,
        activity_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recherche des entreprises à proximité de coordonnées géographiques.
        
        Args:
            latitude: Latitude du point de recherche
            longitude: Longitude du point de recherche
            radius: Rayon de recherche en kilomètres (défaut: 10)
            activity_code: Code d'activité pour filtrer les résultats (optionnel)
            
        Returns:
            Les entreprises trouvées à proximité
        """
        params = {
            'lat': str(latitude),
            'lng': str(longitude),
            'radius': str(radius)
        }
        if activity_code:
            params['code_activite'] = activity_code
            
        return self._make_request('GET', '/entreprises/geo', params=params)
    
    def get_activity_sectors(self) -> Dict[str, Any]:
        """
        Récupère la liste des secteurs d'activité.
        
        Returns:
            La liste des secteurs d'activité disponibles
        """
        return self._make_request('GET', '/referentiels/secteurs')
    
    def get_legal_forms(self) -> Dict[str, Any]:
        """
        Récupère la liste des formes juridiques.
        
        Returns:
            La liste des formes juridiques disponibles
        """
        return self._make_request('GET', '/referentiels/formes-juridiques')
    
    def get_api_status(self) -> Dict[str, Any]:
        """
        Vérifie le statut de l'API.
        
        Returns:
            Le statut actuel de l'API
        """
        return self._make_request('GET', '/status')
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques d'utilisation de l'API.
        
        Returns:
            Les statistiques d'utilisation
        """
        return self._make_request('GET', '/compte/statistiques')
