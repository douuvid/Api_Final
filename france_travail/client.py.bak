"""
France Travail API Client Implementation

This module provides a client for interacting with the France Travail (Pôle Emploi) API.
It uses the alternative implementation which is more reliable and provides better functionality.
"""

from typing import Dict, List, Any, Optional, Callable, TypeVar, cast
from datetime import datetime, timedelta

# Import de l'implémentation alternative
from .alternative_client import FranceTravailAlternativeAPI as AlternativeAPI

# Définition du type générique pour les fonctions décorées
F = TypeVar('F', bound=Callable[..., Any])


class FranceTravailAPI:
    """
    Client for the France Travail (Pôle Emploi) API.
    
    This class provides an interface to interact with the France Travail APIs.
    It internally uses the alternative implementation which is more reliable.
    
    Args:
        client_id (str): Your France Travail API client ID
        client_secret (str): Your France Travail API client secret
    """
    
    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize the France Travail API client.
        
        Args:
            client_id: Application client ID
            client_secret: Application client secret
        """
        # Use the alternative implementation
        self._api = AlternativeAPI(client_id, client_secret)
        
        # Keep attributes for backward compatibility
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None  # Kept for compatibility
        self.token_expiry = None  # Kept for compatibility
        
        # URLs for reference
        self.base_url = "https://api.francetravail.io/partenaire"
        self.auth_url = "https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
    
    def authenticate(self) -> bool:
        """
        Authenticate with the France Travail API.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        return self._api.authenticate()
    
    def is_token_valid(self) -> bool:
        """
        Check if the access token is still valid.
        
        Returns:
            bool: True if the token is valid, False otherwise
        """
        return self._api.is_token_valid()
    
    def match_soft_skills(self, rome_code: str, user_skills: List[str]) -> Dict[str, Any]:
        """
        Match user skills with those required for a specific job.
        
        Args:
            rome_code: ROME code of the target job
            user_skills: List of user skills
            
        Returns:
            Dictionary containing the matching results
        """
        return self._api.match_soft_skills(rome_code, user_skills)
    
    def get_job_offers(self, rome_code: str, limit: int = 10) -> List[Dict]:
        """
        Get job offers for a given ROME code.
        
        Args:
            rome_code: ROME code of the job to search for
            limit: Maximum number of offers to retrieve (max 150)
            
        Returns:
            List of job offers
        """
        print("⚠️  This method is deprecated. Use the alternative API directly for more features.")
        job_data = self._api.get_job_details_by_rome(rome_code)
        return job_data.get('offers_sample', [])
