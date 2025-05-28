"""
France Travail API Client Implementation

This module provides a client for interacting with the France Travail (Pôle Emploi) API.
"""

import requests
import time
from typing import Optional, Dict, Any, Callable, TypeVar, cast
from functools import wraps
from datetime import datetime, timedelta

# Définition du type générique pour les fonctions décorées
F = TypeVar('F', bound=Callable[..., Any])


class FranceTravailAPI:
    """Client for the France Travail (Pôle Emploi) API.
    
    This class provides methods to authenticate and interact with the France Travail API.
    It handles OAuth2 authentication and provides methods to search and retrieve job offers.
    
    Args:
        client_id (str): Your France Travail API client ID
        client_secret (str): Your France Travail API client secret
    """
    
    def __init__(self, client_id: str, client_secret: str):
        """
        Initialise le client API France Travail.
        
        Args:
            client_id: Identifiant client de l'application
            client_secret: Clé secrète de l'application
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://api.francetravail.io/partenaire"
        self.auth_url = "https://francetravail.io/connexion/oauth2/access_token?realm=%2Fpartenaire"
        
        # Gestion des limites de taux d'appel
        self._rate_limits = {
            'offres': {
                'limit': 10,  # appels par seconde
                'last_call': 0,
                'calls': []
            },
            'romeo': {
                'limit': 2,
                'last_call': 0,
                'calls': []
            },
            'bonne_boite': {
                'limit': 2,
                'last_call': 0,
                'calls': []
            },
            'soft_skills': {
                'limit': 1,
                'last_call': 0,
                'calls': []
            }
        }
    
    def _rate_limit(self, api_type: str = 'offres') -> Callable[[F], F]:
        """
        Décoreur pour gérer les limites de taux d'appel.
        
        Args:
            api_type: Type d'API ('offres', 'romeo', 'bonne_boite', 'soft_skills')
            
        Returns:
            Le décorateur à appliquer aux méthodes de l'API
        """
        def decorator(func: F) -> F:
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                # Vérifier et attendre si nécessaire
                self._check_rate_limit(api_type)
                # Appeler la fonction
                return func(self, *args, **kwargs)
            return cast(F, wrapper)
        return decorator
    
    def _check_rate_limit(self, api_type: str):
        """
        Vérifie et applique les limites de taux d'appel.
        
        Args:
            api_type: Type d'API ('offres', 'romeo', 'bonne_boite', 'soft_skills')
        """
        if api_type not in self._rate_limits:
            return
            
        now = time.time()
        limit_info = self._rate_limits[api_type]
        
        # Nettoyer les appaux plus vieux qu'une seconde
        limit_info['calls'] = [t for t in limit_info['calls'] if now - t < 1.0]
        
        # Attendre si nécessaire
        if len(limit_info['calls']) >= limit_info['limit']:
            # Calculer le temps d'attente nécessaire
            oldest_call = limit_info['calls'][0]
            wait_time = 1.0 - (now - oldest_call)
            if wait_time > 0:
                time.sleep(wait_time)
            
            # Nettoyer après l'attente
            now = time.time()
            limit_info['calls'] = [t for t in limit_info['calls'] if now - t < 1.0]
        
        # Enregistrer l'appel
        limit_info['calls'].append(time.time())
        limit_info['last_call'] = now
    
    def authenticate(self) -> bool:
        """Authenticate with the France Travail API using OAuth2 client credentials.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'scope': 'o2dsoffre api_offresdemploiv2'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Convert payload to URL-encoded format
        payload_str = '&'.join([f"{k}={v}" for k, v in payload.items()])
        
        try:
            response = requests.post(self.auth_url, headers=headers, data=payload_str)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                return True
            else:
                print(f"Authentication error: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"Error during authentication: {e}")
            return False
    
    @_rate_limit('offres')
    def search_jobs(self, params: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
        """Search for job offers.
        
        Args:
            params: Optional dictionary containing search parameters.
                - motsCles: Search keywords
                - commune: INSEE city code
                - distance: Search radius in km
                - typeContrat: Contract type (CDI, CDD, etc.)
                - experience: Required experience level
                - qualification: Qualification level
                - secteurActivite: Business sector
                - entrepriseAdaptee: Adapted company (true/false)
                - range: Pagination (e.g., "0-9" for first 10 results)
                
        Returns:
            Optional[Dict]: Dictionary containing search results or None if an error occurred
        """
        if not self.access_token:
            if not self.authenticate():
                return None
        
        url = f"{self.base_url}/offresdemploi/v2/offres/search"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code in [200, 206]:  # 206 = partial content
                print(f"Réponse API (premiers 500 caractères): {response.text[:500]}...")  # Debug
                return response.json()
            elif response.status_code == 401:  # Token might be expired
                # Try to reauthenticate and retry once
                if self.authenticate():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    response = requests.get(url, headers=headers, params=params)
                    if response.status_code in [200, 206]:
                        print(f"Réponse API après réauthentification: {response.text[:500]}...")  # Debug
                        return response.json()
            
            print(f"Error in job search: {response.status_code}")
            print(f"Headers: {response.headers}")
            print(f"Response: {response.text}")
            return None
                
        except Exception as e:
            print(f"Error during job search: {e}")
            return None
    
    @_rate_limit('offres')
    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """Get details for a specific job offer.
        
        Args:
            job_id: The ID of the job offer to retrieve
            
        Returns:
            Optional[Dict]: Dictionary containing job details or None if an error occurred
        """
        if not self.access_token:
            if not self.authenticate():
                return None
        
        url = f"{self.base_url}/offresdemploi/v2/offres/{job_id}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:  # Token might be expired
                # Try to reauthenticate and retry once
                if self.authenticate():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        return response.json()
            
            print(f"Error getting job details: {response.status_code}")
            print(response.text)
            return None
                
        except Exception as e:
            print(f"Error getting job details: {e}")
            return None
