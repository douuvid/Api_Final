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
    if not api.authenticate():
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
    reponse = api.search_jobs(params)
    
    # Vérifier et traiter les résultats
    if not reponse or 'resultats' not in reponse:
        print("Aucune offre trouvée ou erreur lors de la récupération des données.")
        if reponse:
            print(f"Réponse de l'API: {reponse}")
        return
    
    resultats = reponse.get('resultats', [])
    
    if not resultats:
        print("Aucune offre ne correspond à vos critères de recherche.")
        return
    
    # Afficher les offres de manière lisible
    print(f"\n{len(resultats)} offres trouvées. Affichage des 5 premières :\n")
    afficher_offres(resultats, limit=5, show_details=True)

    # Exemple de récupération des détails d'une offre spécifique
    if resultats:
        try:
            while True:
                try:
                    print("\n" + "="*80)
                    choix = input("Entrez le numéro d'une offre pour voir ses détails, ou 'n' pour quitter : ")
                    
                    if not choix:  # Gestion du cas où l'utilisateur appuie juste sur Entrée
                        continue
                        
                    if choix.lower() == 'n':
                        break
                        
                    if not choix.isdigit() or not (1 <= int(choix) <= len(resultats)):
                        print(f"Veuillez entrer un nombre entre 1 et {len(resultats)}, ou 'n' pour quitter.")
                        continue
                        
                    offre_id = resultats[int(choix)-1].get('id')
                    if offre_id:
                        print(f"\nRécupération des détails de l'offre {offre_id}...")
                        details = api.get_job_details(offre_id)
                        if details:
                            print("\n" + "="*80)
                            print(format_offre(details, show_details=True))
                            print("="*80)
                    else:
                        print("ID d'offre non trouvé dans les résultats.")
                        
                except KeyboardInterrupt:
                    print("\n\nInterruption par l'utilisateur.")
                    break
                except EOFError:
                    print("\nFin de l'entrée détectée.")
                    break
                except Exception as e:
                    print(f"\nUne erreur s'est produite : {str(e)}")
                    continue
            
            print("\nMerci d'avoir utilisé le service de recherche d'offres d'emploi.")
            
        except Exception as e:
            print(f"\nUne erreur inattendue s'est produite : {str(e)}")
    else:
        print("\nAucune offre à afficher.")

def afficher_offres(offres, limit=5, show_details=False):
    """Affiche la liste des offres de manière formatée"""
    for i, offre in enumerate(offres[:limit], 1):
        print(f"\n--- Offre {i} ---")
        print(f"Titre: {offre.get('intitule', 'Non spécifié')}")
        print(f"Entreprise: {offre.get('entreprise', {}).get('nom', 'Non spécifié')}")
        print(f"Lieu: {offre.get('lieuTravail', {}).get('libelle', 'Non spécifié')}")
        if show_details:
            print(f"Description: {offre.get('description', 'Non disponible')}")

def format_offre(offre, show_details=False):
    """Formate une offre pour l'affichage"""
    result = []
    result.append(f"Titre: {offre.get('intitule', 'Non spécifié')}")
    result.append(f"Entreprise: {offre.get('entreprise', {}).get('nom', 'Non spécifié')}")
    result.append(f"Lieu: {offre.get('lieuTravail', {}).get('libelle', 'Non spécifié')}")
    result.append(f"Type de contrat: {offre.get('typeContrat', 'Non spécifié')}")
    if show_details:
        result.append(f"\nDescription:\n{offre.get('description', 'Non disponible')}")
    return "\n".join(result)

def main():
    """Fonction principale"""
    try:
        rechercher_offres_emploi()
    except Exception as e:
        print(f"Une erreur s'est produite: {str(e)}")

if __name__ == "__main__":
    main()
