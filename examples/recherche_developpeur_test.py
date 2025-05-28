"""
Exemple de recherche d'offres d'emploi pour "Développeur Test" avec l'API France Travail.
"""
import os
import sys
from dotenv import load_dotenv

# Ajouter le répertoire parent au chemin d'import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from france_travail import FranceTravailAPI

def rechercher_offres_emploi():
    # Charger les variables d'environnement
    load_dotenv()
    
    # Récupérer les identifiants
    client_id = os.getenv("FRANCE_TRAVAIL_CLIENT_ID")
    client_secret = os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("ERREUR: Veuillez configurer FRANCE_TRAVAIL_CLIENT_ID et FRANCE_TRAVAIL_CLIENT_SECRET dans le fichier .env")
        print("Créez un fichier .env à la racine du projet avec ces variables d'environnement.")
        return
    
    # Initialiser le client API
    print("Connexion à l'API France Travail...")
    api = FranceTravailAPI(client_id, client_secret)
    
    # S'authentifier
    if not client.authenticate():
        print("Échec de l'authentification")
        return

    # Paramètres de recherche
    params = {
        'motsCles': 'développeur test',  # Mots-clés de recherche
        'range': '0-9',  # 10 premiers résultats
        'typeContrat': 'CDI,CDD',  # Types de contrat
    }

    # Effectuer la recherche
    print("Recherche d'offres en cours...")
    resultats = client.search_jobs(params)

    # Vérifier et traiter les résultats
    if not resultats or not isinstance(resultats, list):
        print("Aucune offre trouvée ou erreur lors de la récupération des données.")
        return

    # Afficher les offres de manière lisible
    afficher_offres(resultats, limit=5, show_details=True)

    # Exemple de récupération des détails d'une offre spécifique
    if resultats:
        print("\n" + "="*80)
        choix = input("Voulez-vous voir les détails d'une offre en particulier ? (numéro ou 'n' pour quitter) ")
        
        if choix.isdigit() and 1 <= int(choix) <= len(resultats):
            offre_id = resultats[int(choix)-1].get('id')
            if offre_id:
                print(f"\nRécupération des détails de l'offre {offre_id}...")
                details = client.get_job_details(offre_id)
                if details:
                    print("\n" + "="*80)
                    print(format_offre(details, show_details=True))
                    print("="*80)

if __name__ == "__main__":
    main()
