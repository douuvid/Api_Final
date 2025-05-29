"""
Configuration des tests pour l'API ROMEO.

Ce fichier contient les fixtures et configurations communes pour les tests.
"""
import os
import pytest
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


@pytest.fixture(scope="module")
def romeo_credentials():
    """Fixture pour les identifiants ROMEO."""
    client_id = os.getenv("ROMEO_CLIENT_ID")
    client_secret = os.getenv("ROMEO_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        pytest.skip("Identifiants ROMEO non configurés dans le .env")
    
    return {
        "client_id": client_id,
        "client_secret": client_secret
    }


@pytest.fixture(scope="module")
def romeo_client(romeo_credentials):
    """Fixture pour un client ROMEO configuré."""
    from france_travail.romeo import RomeoAPI
    
    return RomeoAPI(
        client_id=romeo_credentials["client_id"],
        client_secret=romeo_credentials["client_secret"]
    )
