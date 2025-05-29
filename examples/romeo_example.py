"""
Exemple d'utilisation de l'API ROMEO v2 de France Travail

Ce script montre comment utiliser le client Python pour interagir avec l'API ROMEO
qui permet de rechercher et de récupérer des informations sur les entreprises.
"""

import os
import sys
from dotenv import load_dotenv

# Ajout du répertoire parent au chemin pour pouvoir importer le module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from france_travail.romeo import RomeoAPI

def main():
    # Charger les variables d'environnement
    load_dotenv()
    
    # Récupérer les identifiants
    client_id = os.getenv("ROMEO_CLIENT_ID")
    client_secret = os.getenv("ROMEO_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("ERREUR: Veuillez configurer les variables d'environnement suivantes :")
        print("  - ROMEO_CLIENT_ID")
        print("  - ROMEO_CLIENT_SECRET")
        print("\nCréez un fichier .env à la racine du projet avec ces variables.")
        return
    
    # Initialisation du client
    print("🔍 Initialisation du client API ROMEO...")
    romeo = RomeoAPI(client_id, client_secret)
    
    try:
        # 1. Vérification du statut de l'API
        print("\n🔄 Vérification du statut de l'API...")
        status = romeo.get_api_status()
        print(f"✅ Statut API: {status.get('status', 'inconnu')}")
        
        # 2. Recherche d'entreprises par nom
        print("\n🔍 Recherche d'entreprises...")
        search_results = romeo.search_companies(
            nom="Informatique",
            ville="Paris",
            limit=3
        )
        
        print(f"📊 {len(search_results.get('results', []))} entreprises trouvées")
        for i, company in enumerate(search_results.get('results', [])[:3], 1):
            print(f"\n   {i}. {company.get('nom')}")
            print(f"      SIRET: {company.get('siret')}")
            print(f"      Activité: {company.get('activite')}")
            print(f"      Adresse: {company.get('adresse', 'N/A')}")
        
        # 3. Détails d'une entreprise (si des résultats sont disponibles)
        if search_results.get('results'):
            first_company = search_results['results'][0]
            siret = first_company.get('siret')
            
            if siret:
                print(f"\n🔍 Récupération des détails pour SIRET: {siret}")
                try:
                    company_details = romeo.get_company_by_siret(siret)
                    print(f"🏢 {company_details.get('nom')}")
                    print(f"   📍 {company_details.get('adresse_complete')}")
                    print(f"   📞 {company_details.get('telephone', 'Non disponible')}")
                    print(f"   🌐 {company_details.get('site_web', 'Non disponible')}")
                    print(f"   👥 Effectif: {company_details.get('effectif', 'Inconnu')}")
                except Exception as e:
                    print(f"⚠️ Erreur lors de la récupération des détails: {str(e)}")
        
        # 4. Recherche géographique
        print("\n🗺️  Recherche d'entreprises autour de Paris...")
        try:
            geo_results = romeo.search_companies_by_location(
                latitude=48.8566,  # Paris
                longitude=2.3522,
                radius=1,  # 1km de rayon
                activity_code="62.02A"  # Conseil en systèmes et logiciels
            )
            
            print(f"📌 {len(geo_results.get('results', []))} entreprises trouvées dans le secteur")
            for i, company in enumerate(geo_results.get('results', [])[:3], 1):
                distance = company.get('distance_km', 0)
                print(f"   {i}. {company.get('nom')} ({distance:.2f} km)")
                
        except Exception as e:
            print(f"⚠️ Erreur lors de la recherche géographique: {str(e)}")
        
        # 5. Récupération des secteurs d'activité
        print("\n📋 Récupération des secteurs d'activité...")
        try:
            sectors = romeo.get_activity_sectors()
            print("Secteurs disponibles:")
            for sector in sectors.get('secteurs', [])[:5]:  # Afficher les 5 premiers
                print(f"- {sector.get('code')}: {sector.get('libelle')}")
            if len(sectors.get('secteurs', [])) > 5:
                print(f"... et {len(sectors['secteurs']) - 5} autres secteurs")
        except Exception as e:
            print(f"⚠️ Erreur lors de la récupération des secteurs: {str(e)}")
        
    except Exception as e:
        print(f"\n❌ Une erreur est survenue: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Détails: {e.response.text}")
    
    print("\n✅ Exécution terminée")

if __name__ == "__main__":
    main()
