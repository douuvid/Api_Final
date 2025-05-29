"""
France Travail API Client

A Python client for interacting with the France Travail API client.
"""

from .client import FranceTravailAPI
from .romeo import RomeoAPI
from .utils import afficher_offres, format_offre

__version__ = "0.2.0"
__all__ = [
    'FranceTravailAPI',
    'RomeoAPI',
    'afficher_offres',
    'format_offre'
]
