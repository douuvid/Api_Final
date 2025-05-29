#!/usr/bin/env python3
"""
Script de test progressif pour l'API ROMEO.
Teste d'abord la connexion, puis progressivement les fonctionnalités.
"""

import os
import sys
from dotenv import load_dotenv

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from france_travail.romeo import RomeoAPI
import requests  # Pour la gestion des erreurs HTTP


def test_step_1_connection():
    """Étape 1: Test de base - connexion et authentification"""
    print("🔐 ÉTAPE 1: Test de connexion et authentification")
    print("-" * 50)
    
    # Charger les variables d'environnement
    load_dotenv()
    client_id = os.getenv('ROMEO_CLIENT_ID')
    client_secret = os.getenv('ROMEO_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Variables d'environnement manquantes")
        print("   Assurez-vous d'avoir défini ROMEO_CLIENT_ID et ROMEO_CLIENT_SECRET dans .env")
        return False, None
    
    print(f"✅ Identifiants chargés")
    print(f"   Client ID: {client_id[:10]}...{client_id[-5:]}")
    
    # Initialiser le client
    try:
        romeo = RomeoAPI(client_id, client_secret)
        print("✅ Client API initialisé")
        
        # Test d'authentification OAuth2
        print("🔑 Test d'obtention du token OAuth2...")
        token = romeo._get_oauth2_token()
        print(f"✅ Token obtenu: {token[:15]}...{token[-15:]}")
        return True, romeo
    except Exception as e:
        print(f"❌ Erreur d'authentification: {str(e)}")
        return False, None


def test_step_2_basic_calls(romeo):
    """Étape 2: Appels API de base (sans données spécifiques)"""
    print("\n📡 ÉTAPE 2: Test des appels API de base")
    print("-" * 50)
    
    # Test du statut de l'API
    try:
        print("🏥 Test du statut de l'API...")
        status = romeo.get_api_status()
        print(f"✅ Statut API: {status}")
    except Exception as e:
        print(f"❌ Erreur statut API: {str(e)}")
        return False
    
    # Test des référentiels (ne nécessitent pas de données spécifiques)
    try:
        print("📚 Test des secteurs d'activité...")
        sectors = romeo.get_activity_sectors()
        print(f"✅ Secteurs récupérés: {len(sectors.get('data', []))} éléments")
    except Exception as e:
        print(f"⚠️ Erreur secteurs: {str(e)}")
        # Ce n'est pas bloquant, continuer
    
    try:
        print("🏛️ Test des formes juridiques...")
        forms = romeo.get_legal_forms()
        print(f"✅ Formes juridiques récupérées: {len(forms.get('data', []))} éléments")
    except Exception as e:
        print(f"⚠️ Erreur formes juridiques: {str(e)}")
        # Ce n'est pas bloquant, continuer
    
    return True


def test_step_3_search_validation(romeo):
    """Étape 3: Test de validation des recherches (formats)"""
    print("\n🔍 ÉTAPE 3: Test de validation des formats")
    print("-" * 50)
    
    # Test validation SIRET avec format invalide
    try:
        print("🧪 Test validation SIRET invalide...")
        romeo.get_company_by_siret("123")  # Trop court
        print("❌ La validation SIRET ne fonctionne pas")
        return False
    except ValueError as e:
        print(f"✅ Validation SIRET fonctionne: {str(e)}")
    except Exception as e:
        print(f"⚠️ Erreur inattendue: {str(e)}")
    
    # Test validation SIREN avec format invalide
    try:
        print("🧪 Test validation SIREN invalide...")
        romeo.get_company_by_siren("123")  # Trop court
        print("❌ La validation SIREN ne fonctionne pas")
        return False
    except ValueError as e:
        print(f"✅ Validation SIREN fonctionne: {str(e)}")
    except Exception as e:
        print(f"⚠️ Erreur inattendue: {str(e)}")
    
    return True


def test_step_4_fictitious_searches(romeo):
    """Étape 4: Recherches avec données fictives (test format mais pas existence)"""
    print("\n🎭 ÉTAPE 4: Test avec données fictives")
    print("-" * 50)
    
    # Test SIRET fictif mais format valide
    try:
        print("🔢 Test SIRET fictif (format valide)...")
        result = romeo.get_company_by_siret("12345678901234")
        print(f"⚠️ Résultat inattendu: {result}")
    except requests.HTTPError as e:
        if "404" in str(e):
            print("✅ SIRET fictif correctement rejeté (404 Not Found)")
        else:
            print(f"❌ Erreur inattendue: {str(e)}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False
    
    # Test recherche générale
    try:
        print("🔍 Test recherche par nom fictif...")
        results = romeo.search_companies(nom="EntrepriseInexistante123456", limit=2)
        result_count = len(results.get('data', []))
        print(f"✅ Recherche effectuée: {result_count} résultats")
    except Exception as e:
        print(f"❌ Erreur recherche: {str(e)}")
        return False
    
    return True


def test_step_5_real_searches(romeo):
    """Étape 5: Recherches avec vraies données"""
    print("\n🏢 ÉTAPE 5: Test avec vraies entreprises")
    print("-" * 50)
    
    # Vrais SIRET d'entreprises connues
    real_companies = {
        "Google France": "44323664400026",
        "Microsoft France": "32733889800058",
        "Orange SA": "38012986000081"
    }
    
    for company_name, siret in real_companies.items():
        try:
            print(f"🔍 Test {company_name} (SIRET: {siret})...")
            result = romeo.get_company_by_siret(siret)
            
            # Vérifier qu'on a bien des données
            if result and 'data' in result:
                print(f"✅ {company_name} trouvée!")
                # Afficher quelques infos si disponibles
                data = result['data']
                if isinstance(data, dict):
                    nom = data.get('nom', 'N/A')
                    ville = data.get('ville', 'N/A')
                    print(f"   Nom: {nom}")
                    print(f"   Ville: {ville}")
                break  # Un succès suffit pour valider
            else:
                print(f"⚠️ {company_name}: réponse vide")
                
        except Exception as e:
            print(f"⚠️ {company_name}: {str(e)}")
            continue
    
    # Test recherche géographique (Paris)
    try:
        print("🗺️ Test recherche géographique (Paris)...")
        geo_results = romeo.search_companies_by_location(
            latitude=48.8566,
            longitude=2.3522,
            radius=5,
            limit=3
        )
        count = len(geo_results.get('data', []))
        print(f"✅ Recherche géographique: {count} entreprises trouvées")
    except Exception as e:
        print(f"⚠️ Erreur recherche géographique: {str(e)}")
    
    return True


def main():
    """Test progressif complet"""
    print("🧪 TESTS PROGRESSIFS DE L'API ROMEO")
    print("=" * 60)
    print("Ce script teste progressivement chaque fonctionnalité")
    print("pour identifier précisément où se situe le problème.\n")
    
    # Étape 1: Connexion
    success, romeo = test_step_1_connection()
    if not success:
        print("\n❌ ÉCHEC à l'étape 1 - Problème d'authentification")
        print("   Vérifiez vos identifiants ROMEO_CLIENT_ID et ROMEO_CLIENT_SECRET")
        return False
    
    # Étape 2: Appels de base
    if not test_step_2_basic_calls(romeo):
        print("\n❌ ÉCHEC à l'étape 2 - Problème d'accès API")
        return False
    
    # Étape 3: Validation
    if not test_step_3_search_validation(romeo):
        print("\n❌ ÉCHEC à l'étape 3 - Problème de validation")
        return False
    
    # Étape 4: Données fictives
    if not test_step_4_fictitious_searches(romeo):
        print("\n❌ ÉCHEC à l'étape 4 - Problème avec recherches fictives")
        return False
    
    # Étape 5: Vraies données (non bloquant)
    test_step_5_real_searches(romeo)
    
    print("\n" + "=" * 60)
    print("🎉 TESTS TERMINÉS AVEC SUCCÈS!")
    print("✅ L'API ROMEO fonctionne correctement")
    print("✅ Vous pouvez maintenant utiliser l'API dans votre application")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
