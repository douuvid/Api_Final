"""
France Travail API Client

A Python client for interacting with the France Travail API client.
Inclut le support des APIs ROME 4.0 pour le matching de compétences.
"""


from .utils import afficher_offres, format_offre
from .rome4_api import FranceTravailROME4API

__version__ = "0.2.0"
__all__ = [
    'FranceTravailAPI',
    'FranceTravailROME4API',
    'afficher_offres',
    'format_offre'
]
