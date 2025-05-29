#!/usr/bin/env python3
"""
Script de test d'authentification ROMEO.
Vérifie spécifiquement les problèmes d'authentification.

NOTE IMPORTANTE (29/05/2025) :
- L'implémentation technique de l'authentification est prête
- Les identifiants actuels ne semblent pas actifs ou ne disposent pas des droits nécessaires
- Une validation par Pôle Emploi est requise pour activer l'accès à l'API ROMEO
- Le code est fonctionnel et sera opérationnel une fois les accès accordés
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Configuration
TEST_SIRET = "12345678901234"  # Format valide mais inexistant
TEST_SIREN = "123456789"       # Format valide mais inexistant

# Identifiants fournis
CLIENT_ID = "PAR_cv_9137520f2b833ef0ce2913e412a819ddf8191bb97dd1b09f1a20f0e21c451deb"
CLIENT_SECRET = "cbc8a7310a011f18566360ce3865c7bffa995b11acc18b5ab844a61bc7954050"

# URL de l'API
API_BASE_URL = "https://api.emploi-store.fr/partenaire/romeo/v1"
# URL d'authentification de l'API Emploi Store
TOKEN_URL = "https://api.emploi-store.fr/partenaire/oauth2/token"


def print_header(title):
    """Affiche un en-tête de section."""
    print("\n" + "=" * 70)
    print(f" {title}".upper())
    print("=" * 70)


def test_oauth2_token():
    """Teste l'obtention d'un token OAuth2 avec authentification de base."""
    print_header("1. Test d'authentification OAuth2 avec Basic Auth")
    
    # Encodage des identifiants en base64 pour l'authentification de base
    import base64
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    
    print(f"🔑 Envoi de la requête à {TOKEN_URL}")
    print(f"   Headers: {headers}")
    print("   Test de différents scopes...\n")
    
    # Essayer différents scopes
    scopes_to_try = [
        '',  # Aucun scope
        'api_romeo',
        'api_romeo_v1',
        'api_romeo_v1_entreprise',
        'api_romeo_v1_entreprises',
        'api_romeo_entreprise',
        'api_romeo_entreprises',
        'api-romeo',
        'api-entreprise',
        'api_entreprise',
        'api-entreprises',
        'api_entreprises',
        'api_romeo_v1_entreprise:read',
        'entreprise',
        'entreprises',
        'api_romeo_v1_entreprises:read',
        'api_romeo_entreprises:read',
        'application_PAR_cv_9137520f2b833ef0ce2913e412a819ddf8191bb97dd1b09f1a20f0e21c451deb',
        'default',
        'openid',
        'profile',
        'email',
        'offline_access'
    ]
    
    for scope in scopes_to_try:
        data = {
            'grant_type': 'client_credentials',
        }
        if scope:
            data['scope'] = scope
            
        print(f"🔍 Essai avec le scope: {scope if scope else '(aucun)'}")
        try:
            response = requests.post(TOKEN_URL, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            access_token = token_data.get('access_token')
            
            if access_token:
                print("✅ Authentification réussie !")
                print(f"   Scope utilisé: {scope if scope else '(aucun)'}")
                print(f"   Token: {token_data.get('token_type', 'Bearer')} {access_token[:15]}...{access_token[-15:]}")
                print(f"   Expires in: {token_data.get('expires_in')} secondes")
                return access_token
                
        except requests.exceptions.HTTPError as e:
            error_msg = str(e.response.text)[:200]
            print(f"   ❌ Erreur {e.response.status_code} avec le scope '{scope if scope else 'aucun'}'")
            
            if e.response.status_code == 400 and 'invalid_scope' in error_msg:
                print(f"   ℹ️ Le scope '{scope}' n'est pas valide")
            elif e.response.status_code == 401:
                print("   ℹ️ Échec de l'authentification avec ces identifiants")
                print(f"   Détails: {error_msg}")
            else:
                print(f"   Détails: {error_msg}")
            
        except Exception as e:
            print(f"   ❌ Erreur inattendue avec le scope '{scope if scope else 'aucun'}': {str(e)}")
    
    print("\n❌ Aucun des scopes testés n'a fonctionné")
    return None


def test_api_call_with_token(access_token):
    """Teste un appel API avec le token obtenu."""
    if not access_token:
        return False
        
    print_header("2. Test d'appel API avec le token")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Test avec un SIRET fictif
    try:
        print(f"\n🔍 Test avec SIRET fictif: {TEST_SIRET}")
        url = f"{API_BASE_URL}/entreprises/{TEST_SIRET}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            print("✅ 404 Not Found - L'authentification fonctionne !")
            print("   Le SIRET n'existe pas, mais l'API a répondu correctement.")
            return True
        elif response.status_code == 200:
            print("⚠️ 200 OK - Le SIRET existe dans la base de données (inattendu)")
            print(f"   Réponse: {response.json()}")
            return True
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'appel API: {str(e)}")
    
    return False


def main():
    """Fonction principale."""
    print("\n" + "=" * 70)
    print("  TEST D'AUTHENTIFICATION API ROMEO".center(70))
    print("  (avec identifiants fournis)".center(70))
    print("=" * 70)
    
    print(f"\n🔑 Identifiants utilisés:")
    print(f"   Client ID: {CLIENT_ID[:10]}...{CLIENT_ID[-10:]}")
    print(f"   Client Secret: {'*' * 10}{CLIENT_SECRET[-5:]}")
    
    # Test d'authentification
    access_token = test_oauth2_token()
    
    # Si l'authentification a réussi, tester un appel API
    if access_token:
        test_api_call_with_token(access_token)
    
    print("\n" + "=" * 70)
    print("  FIN DES TESTS".center(70))
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
