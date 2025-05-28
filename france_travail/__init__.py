"""
France Travail API Client

A Python client for interacting with the France Travail API client.
"""

from .client import FranceTravailAPI
from .utils import afficher_offres, format_offre

__version__ = "0.1.0"
__all__ = ['FranceTravailAPI', 'afficher_offres', 'format_offre']
