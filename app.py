from flask import Flask, request, jsonify, Response
from france_travail.client import FranceTravailAPI
from france_travail.cv_parser import CVParser
from dotenv import load_dotenv
import os
import sys
import argparse

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)

# Initialiser le client API corrigé
try:
    api = FranceTravailAPI(
        client_id=os.getenv("FRANCE_TRAVAIL_CLIENT_ID"),
        client_secret=os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET"),
        simulation=False # S'assurer que le mode simulation est désactivé
    )
except ValueError as e:
    # Gérer le cas où les identifiants ne sont pas configurés
    api = None
    print(f"ERREUR: Impossible d'initialiser l'API France Travail. {e}")


# L'endpoint 'match_skills' a été temporairement retiré car
# la méthode correspondante n'existe pas dans le client API actuel.
# Il faudra le réintégrer une fois la fonctionnalité implémentée.

@app.route('/api/job_details/<job_id>', methods=['GET'])
def job_details(job_id):
    """Récupère les détails d'une offre d'emploi par son ID."""
    if not api:
        return jsonify({"error": "L'API n'est pas configurée correctement."}), 503

    try:
        details = api.get_job_details(job_id)
        if details:
            return jsonify(details)
        else:
            return jsonify({"error": "Offre d'emploi non trouvée ou erreur API"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def perform_and_print_search(params):
    """
    Fonction partagée pour effectuer une recherche et formater le résultat pour l'affichage.
    """
    if not api:
        print("ERREUR: L'API n'est pas initialisée.")
        return

    results = api.search_jobs(params)
    
    if results and results.get('resultats'):
        output = []
        total_results = len(results.get('resultats', []))
        output.append(f"\n{total_results} OFFRES TROUVÉES POUR : {params}")
        output.append("=" * 50)
        
        for i, offre in enumerate(results.get('resultats', [])):
            output.append(f"\n--- Offre n°{i+1} ---")
            output.append(f"ID          : {offre.get('id', 'N/A')}")
            output.append(f"Titre       : {offre.get('intitule', 'N/A')}")
            entreprise_nom = offre.get('entreprise', {}).get('nom', 'N/A')
            output.append(f"Entreprise  : {entreprise_nom}")
            lieu = offre.get('lieuTravail', {}).get('libelle', 'N/A')
            output.append(f"Lieu        : {lieu}")
            contrat = offre.get('typeContratLibelle', 'N/A')
            output.append(f"Contrat     : {contrat}")
            salaire = offre.get('salaire', {}).get('libelle', 'N/A')
            if salaire != 'N/A':
                output.append(f"Salaire     : {salaire}")
            description = offre.get('description', 'N/A').replace('\n', ' ')
            output.append(f"Description : {description[:250]}...")
        
        output.append("\n" + "=" * 50)
        print("\n".join(output))
    else:
        print("\nAucun résultat trouvé ou une erreur est survenue avec l'API.")

@app.route('/api/search', methods=['GET'])
def search_jobs_endpoint():
    """
    Recherche des offres d'emploi via l'endpoint web.
    """
    if not api:
        return jsonify({"error": "L'API n'est pas configurée correctement."}), 503

    params = request.args.to_dict()
    if not params:
        return Response("Erreur: Au moins un paramètre de recherche est requis.", mimetype='text/plain', status=400)

    # La logique de recherche et d'affichage est maintenant dans la console du serveur
    # Pour une vraie API, on retournerait du JSON. Ici, on simule l'affichage.
    perform_and_print_search(params)
    return Response(f"Recherche effectuée pour {params}. Voir la console du serveur pour les résultats.", mimetype='text/plain')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Recherche d'offres d'emploi via l'API France Travail.")
    parser.add_argument('--motsCles', type=str, help='Mots-clés pour la recherche (ex: "développeur python").')
    parser.add_argument('--departement', type=str, help='Numéro de département (ex: "75" pour Paris).')
    parser.add_argument('--commune', type=str, help='Code INSEE de la commune.')
    parser.add_argument('--codeROME', type=str, help='Code ROME du métier.')
    parser.add_argument('--range', type=str, default='0-4', help='Plage de résultats (ex: "0-9").')

    # Arguments pour le matching de CV
    parser.add_argument('--cv', type=str, help='Chemin vers le fichier CV (format .txt).')
    parser.add_argument('--offre', type=str, help="ID de l'offre d'emploi pour le matching.")

    args = parser.parse_args()

    # Créer un dictionnaire de paramètres uniquement avec les arguments fournis
    search_params = {k: v for k, v in vars(args).items() if v is not None}

    # Si les arguments pour le matching de CV sont fournis
    if args.cv and args.offre:
        print(f"Lancement de l'analyse de matching pour le CV {args.cv} et l'offre {args.offre}...")
        parser = CVParser()
        try:
            print(f"Analyse du CV : {args.cv}")
            cv_text = parser.extract_text_from_file(args.cv)
            if not cv_text:
                print("Impossible d'extraire le contenu du CV.")
                sys.exit(1)

            print(f"Analyse de la compatibilité avec l'offre : {args.offre}")
            match_details = api.analyze_cv_match(cv_text, args.offre)

            if match_details:
                print("\n--- Résultat de l'analyse ---")
                print(f"Offre d'emploi : {match_details['job_title']}")
                print(f"Taux de compatibilité : {match_details['matching_rate']:.2f}%")
                print("\nCompétences détectées dans le CV :")
                if match_details['cv_skills']:
                    for skill, score in match_details['cv_skills'].items():
                        print(f"- {skill.capitalize()}")
                else:
                    print("Aucune compétence spécifique détectée.")
                
                print("\nCompétences requises par l'offre :")
                if match_details['job_skills']:
                    for skill, score in match_details['job_skills'].items():
                        print(f"- {skill.capitalize()}")
                else:
                    print("Aucune compétence spécifique détectée.")
                print("-----------------------------\n")
            else:
                print("L'analyse n'a pas pu être effectuée.")

        except FileNotFoundError:
            print(f"Erreur : Le fichier CV '{args.cv}' n'a pas été trouvé.")
        except Exception as e:
            print(f"Une erreur est survenue lors de l'analyse : {e}")

    # Si des paramètres de recherche ont été passés
    elif len(search_params) > 1:
        print("Lancement de la recherche en ligne de commande...")
        perform_and_print_search(search_params)
        
    # Sinon, on lance le serveur web
    else:
        if api:
            print("Aucun argument fourni. Lancement du serveur web...")
            app.run(debug=True, port=5000)
        else:
            print("L'application ne peut pas démarrer car l'API France Travail n'est pas initialisée.")
            print("Veuillez vérifier votre fichier .env et vos identifiants.")
