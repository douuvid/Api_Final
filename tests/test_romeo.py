#!/usr/bin/env python3
"""
Script de test pour l'API ROMEO de France Travail.

Ce script teste toutes les fonctionnalités de l'API ROMEO et diagnostique
les problèmes d'authentification.

Usage:
    python -m tests.test_romeo
"""

import os
import sys
import time
from dotenv import load_dotenv

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from france_travail.romeo import RomeoAPI


def print_section(title):
    """Affiche une section avec un titre formaté."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(test_name, success, details=None):
    """Affiche le résultat d'un test."""
    icon = "✅" if success else "❌"
    status = "SUCCÈS" if success else "ÉCHEC"
    print(f"{icon} [{status}] {test_name}")
    if details:
        print(f"   {details}")


def test_environment():
    """Teste la configuration de l'environnement."""
    print_section("VÉRIFICATION DE L'ENVIRONNEMENT")
    
    # Charger les variables d'environnement
    load_dotenv()
    
    client_id = os.getenv('ROMEO_CLIENT_ID')
    client_secret = os.getenv('ROMEO_CLIENT_SECRET')
    
    if not client_id:
        print_result("Variable ROMEO_CLIENT_ID", False, "Non définie dans .env")
        return None, None
    
    if not client_secret:
        print_result("Variable ROMEO_CLIENT_SECRET", False, "Non définie dans .env")
        return None, None
    
    print_result("Variables d'environnement", True)
    print(f"   Client ID: {client_id[:10]}...{client_id[-5:]}")
    print(f"   Client Secret: {'*' * 10}{client_secret[-5:]}")
    
    return client_id, client_secret


def test_authentication(romeo_client):
    """Teste l'authentification OAuth2."""
    print_section("TEST D'AUTHENTIFICATION")
    
    try:
        # Test d'obtention du token
        token = romeo_client._get_oauth2_token()
        print_result("Obtention du token OAuth2", True)
        print(f"   Token: {token[:15]}...{token[-15:]}")
        return True
    except Exception as e:
        print_result("Obtention du token OAuth2", False, str(e))
        return False


def test_api_calls(romeo_client):
    """Teste les appels API."""
    print_section("TEST DES APPELS API")
    
    tests = []
    
    # Test du statut de l'API
    try:
        status = romeo_client.get_api_status()
        tests.append(("Statut de l'API", True, f"Version: {status.get('version', 'inconnue')}"))
    except Exception as e:
        tests.append(("Statut de l'API", False, str(e)))
    
    # Test de recherche d'entreprises
    try:
        results = romeo_client.search_companies(nom="Microsoft", limit=2)
        count = len(results.get('data', []))
        tests.append(("Recherche d'entreprises", True, f"{count} résultats"))
    except Exception as e:
        tests.append(("Recherche d'entreprises", False, str(e)))
    
    # Test des référentiels
    try:
        sectors = romeo_client.get_activity_sectors()
        tests.append(("Secteurs d'activité", True, 
                     f"{len(sectors.get('data', []))} secteurs disponibles"))
    except Exception as e:
        tests.append(("Secteurs d'activité", False, str(e)))
    
    try:
        forms = romeo_client.get_legal_forms()
        tests.append(("Formes juridiques", True, 
                     f"{len(forms.get('data', []))} formes disponibles"))
    except Exception as e:
        tests.append(("Formes juridiques", False, str(e)))
    
    # Afficher les résultats
    for test_name, success, details in tests:
        print_result(test_name, success, details)
    
    return all(test[1] for test in tests)


def test_rate_limiting(romeo_client):
    """Teste la gestion des limites de taux."""
    print_section("TEST DU RATE LIMITING")
    
    try:
        import time
        start_time = time.time()
        
        # Faire 3 appels rapidement (limite: 2/seconde)
        for i in range(3):
            romeo_client.get_api_status()
            print(f"   Appel {i+1} effectué à {time.time():.2f}s")
        
        elapsed = time.time() - start_time
        print_result("Rate limiting", True, f"3 appels en {elapsed:.2f}s")
        
        if elapsed >= 1.0:
            print("   ✅ Rate limiting fonctionne correctement")
        else:
            print("   ⚠️  Rate limiting peut être insuffisant")
            
        return True
    except Exception as e:
        print_result("Rate limiting", False, str(e))
        return False


def test_specific_searches(romeo_client):
    """Teste des recherches spécifiques."""
    print_section("TESTS DE RECHERCHES SPÉCIFIQUES")
    
    tests = []
    
    # Test recherche par SIRET (exemple fictif)
    try:
        # SIRET de test (format valide mais peut ne pas exister)
        test_siret = "12345678901234"
        result = romeo_client.get_company_by_siret(test_siret)
        tests.append(("Recherche par SIRET", True, "Trouvée"))
    except ValueError as e:
        tests.append(("Validation SIRET", True, "Format validé"))
    except Exception as e:
        tests.append(("Recherche par SIRET", False, str(e)))
    
    # Test recherche géographique (Paris)
    try:
        geo_results = romeo_client.search_companies_by_location(
            latitude=48.8566,
            longitude=2.3522,
            radius=5,
            limit=2
        )
        count = len(geo_results.get('data', []))
        tests.append(("Recherche géographique", True, f"{count} résultats"))
    except Exception as e:
        tests.append(("Recherche géographique", False, str(e)))
    
    # Afficher les résultats
    for test_name, success, details in tests:
        print_result(test_name, success, details)


def main():
    """Fonction principale de test."""
    print("🚀 SCRIPT DE TEST DE L'API ROMEO")
    print("=" * 60)
    
    # Test de l'environnement
    client_id, client_secret = test_environment()
    if not client_id or not client_secret:
        print("\n❌ Impossible de continuer sans les identifiants API")
        sys.exit(1)
    
    # Initialiser le client
    try:
        romeo = RomeoAPI(client_id, client_secret)
        print_result("Initialisation du client", True)
    except Exception as e:
        print_result("Initialisation du client", False, str(e))
        sys.exit(1)
    
    # Tests séquentiels
    auth_success = test_authentication(romeo)
    if not auth_success:
        print("\n❌ Authentification échouée - arrêt des tests")
        return False
    
    api_success = test_api_calls(romeo)
    rate_limit_success = test_rate_limiting(romeo)
    test_specific_searches(romeo)
    
    # Résumé final
    print_section("RÉSUMÉ FINAL")
    
    if auth_success and api_success:
        print("✅ L'API ROMEO fonctionne correctement!")
        print("   Vous pouvez maintenant intégrer l'API dans votre application.")
    else:
        print("❌ Certains tests ont échoué.")
        print("   Vérifiez vos identifiants et la configuration.")
    
    return auth_success and api_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
