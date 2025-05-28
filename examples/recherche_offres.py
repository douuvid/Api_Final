"""
Exemple de recherche d'offres d'emploi avec affichage lisible.
"""
from datetime import datetime, timedelta
from france_travail import FranceTravailAPI, afficher_offres, format_offre
import os
from dotenv import load_dotenv

def main():
    # Charger les variables d'environnement
    load_dotenv()

    # Initialiser le client
    client = FranceTravailAPI(
        client_id=os.getenv("FRANCE_TRAVAIL_CLIENT_ID"),
        client_secret=os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")
    )

    # S'authentifier
    print("Authentification en cours...")
    if not client.authenticate():
        print("❌ Échec de l'authentification")
        return
    print("✅ Authentification réussie\n")

    while True:
        # Valeurs par défaut pour le test
        if '--test' in os.sys.argv:
            mots_cles = "développeur"
            lieu = ""  # On ne spécifie pas de lieu pour le test
            contrat = ""  # On ne filtre pas par type de contrat pour le test
            print("\n🔧 Mode test activé avec les paramètres :")
            print(f"- Mots-clés: {mots_cles}")
            print("\nFiltres automatiques appliqués :")
            print("- Offres du dernier mois")
            print("- Niveau bac+2 minimum")
        else:
            # Demander les critères de recherche
            print("\n" + "="*50)
            print("  RECHERCHE D'OFFRES D'EMPLOI")
            print("="*50)
            print("\nEntrez vos critères de recherche :")
            
            mots_cles = input("- Mots-clés (ex: développeur python) : ").strip()
            lieu = input("- Lieu (code postal ou ville, laisser vide si non pertinent) : ").strip()
            contrat = input("- Type de contrat (CDI, CDD, etc., laisser vide pour tous) : ").strip()
        
        # Paramètres de recherche avec filtres progressifs
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        params = {
            'motsCles': mots_cles,
            'range': '0-4',  # 5 premiers résultats
            'minCreationDate': start_date.strftime('%Y-%m-%dT00:00:00Z'),  # Début de la période
            'maxCreationDate': end_date.strftime('%Y-%m-%dT23:59:59Z')  # Fin de la période (maintenant)
        }

        # Effectuer la recherche
        print("\n🔍 Recherche d'offres en cours...")
        try:
            resultats = client.search_jobs(params)
            
            if not resultats or not isinstance(resultats, list):
                if isinstance(resultats, dict) and 'message' in resultats:
                    print(f"\n❌ Erreur API: {resultats.get('message')}")
                else:
                    print("\n❌ Aucune offre trouvée ou erreur lors de la recherche.")
                continue
                
            if len(resultats) == 0:
                print("\nℹ️ Aucune offre ne correspond à vos critères.")
                print("Conseils :")
                print("- Élargissez votre recherche géographique")
                print("- Utilisez des mots-clés plus généraux")
                print("- Vérifiez l'orthographe des termes de recherche")
                continue
                
            # Afficher les résultats
            print(f"\n✅ {len(resultats)} offres trouvées (affichage des 5 premières) :")
            afficher_offres(resultats, limit=5, show_details=True)
            
            # Proposer de voir plus de résultats si disponibles
            if len(resultats) > 5:
                voir_plus = input("\nVoulez-vous voir les 5 résultats suivants ? (o/n) ").lower()
                if voir_plus == 'o':
                    # Récupérer les 5 résultats suivants
                    params['range'] = '5-9'
                    resultats_suivants = client.search_jobs(params)
                    if resultats_suivants and len(resultats_suivants) > 0:
                        print(f"\n📋 5 résultats supplémentaires :")
                        afficher_offres(resultats_suivants, limit=5, show_details=True)
                        resultats.extend(resultats_suivants)  # Ajouter aux résultats totaux
            
            # Option pour voir les détails d'une offre spécifique
            if resultats:
                while True:
                    print("\n" + "-"*50)
                    choix = input("\nEntrez le numéro d'une offre pour plus de détails, 'r' pour une nouvelle recherche, ou 'q' pour quitter : ").strip().lower()
                    
                    if choix == 'q':
                        print("\nMerci d'avoir utilisé le service. Au revoir ! 👋")
                        return
                    elif choix == 'r':
                        break
                    elif choix.isdigit() and 1 <= int(choix) <= len(resultats):
                        offre = resultats[int(choix)-1]
                        offre_id = offre.get('id')
                        
                        if offre_id:
                            print(f"\n🔄 Récupération des détails de l'offre {choix}...")
                            details = client.get_job_details(offre_id)
                            
                            if details:
                                print("\n" + "="*80)
                                print(format_offre(details, show_details=True))
                                print("="*80)
                                
                                # Afficher le lien pour postuler
                                print("\n💡 Pour postuler ou voir l'offre en ligne :")
                                print(f"https://candidat.pole-emploi.fr/offres/emploi/detail/{offre_id}")
                                print("="*80)
                            else:
                                print("❌ Impossible de récupérer les détails de cette offre.")
                    else:
                        print("❌ Choix invalide. Veuillez réessayer.")
            
        except Exception as e:
            print(f"\n❌ Une erreur est survenue : {str(e)}")

if __name__ == "__main__":
    print("=== Client API France Travail ===\n")
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nRecherche interrompue. Au revoir ! 👋")
    except Exception as e:
        print(f"\n❌ Une erreur inattendue est survenue : {str(e)}")
