from flask import Flask, request, jsonify, Response
from france_travail.api import OffresClient, LBBClient, RomeoClient, SoftSkillsClient, ContexteTravailClient
from france_travail.cv_parser import CVParser
from dotenv import load_dotenv
import os
import sys
import argparse
import logging

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)

# Initialiser les clients API
try:
    client_id = os.getenv("FRANCE_TRAVAIL_CLIENT_ID")
    client_secret = os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("Les variables d'environnement FRANCE_TRAVAIL_CLIENT_ID et FRANCE_TRAVAIL_CLIENT_SECRET doivent être définies.")

    soft_skills_client = SoftSkillsClient(
        client_id=client_id,
        client_secret=client_secret,
        simulation=False
    )
    offres_client = OffresClient(
        soft_skills_client=soft_skills_client,
        client_id=client_id,
        client_secret=client_secret,
        simulation=False
    )
    lbb_client = LBBClient(
        client_id=client_id,
        client_secret=client_secret,
        simulation=False
    )
    romeo_client = RomeoClient(
        client_id=client_id,
        client_secret=client_secret,
        simulation=False
    )
    contexte_client = ContexteTravailClient(
        client_id=client_id,
        client_secret=client_secret,
        simulation=False
    )
except ValueError as e:
    print(f"ERREUR: Impossible d'initialiser les clients API. {e}")
    offres_client = None
    lbb_client = None
    romeo_client = None
    soft_skills_client = None
    contexte_client = None


# --- Fonctions d'aide pour l'affichage en console ---

def print_search_results(params, results):
    """Formate et affiche les résultats de recherche d'offres."""
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

def print_cv_match_results(details):
    """Formate et affiche les résultats du matching de CV."""
    if details:
        print("\n--- Résultat de l'analyse de compatibilité ---")
        print(f"Offre d'emploi : {details['job_title']} (Code ROME: {details.get('rome_code', 'N/A')})")
        print(f"Taux de compatibilité : {details['matching_rate']:.2f}%")
        
        print("\nCompétences requises par l'offre (et présence dans le CV) :")
        if details['job_skills']:
            # Trie les compétences par score, du plus élevé au plus bas
            sorted_skills = sorted(details['job_skills'].items(), key=lambda item: item[1], reverse=True)
            for skill, score in sorted_skills:
                # Ajoute un marqueur pour indiquer si la compétence a été trouvée dans le CV
                found_in_cv_marker = "✅" if skill in details['cv_skills'] else "❌"
                print(f"- {skill.capitalize()} (Score: {score:.2f}) {found_in_cv_marker}")
        else:
            print("Aucune compétence requise n'a été trouvée pour ce métier.")
            
        print("\nCompétences détectées dans le CV :")
        if details['cv_skills']:
            for skill in details['cv_skills']:
                print(f"- {skill.capitalize()}")
        else:
            print("Aucune des compétences requises n'a été détectée dans le CV.")
        print("\nLégende: ✅ = Compétence présente dans le CV, ❌ = Compétence absente du CV")
        print("---------------------------------------------\n")
    else:
        print("L'analyse n'a pas pu être effectuée.")

def print_lbb_results(params, results):
    """Formate et affiche les résultats de La Bonne Boite."""
    if results and results.get('companies'):
        output = []
        total_results = len(results.get('companies', []))
        output.append(f"\n{total_results} ENTREPRISES TROUVÉES POUR : {params}")
        output.append("=" * 50)
        for i, entreprise in enumerate(results.get('companies', [])):
            output.append(f"\n--- Entreprise n°{i+1} ---")
            output.append(f"Nom         : {entreprise.get('name', 'N/A')}")
            output.append(f"Adresse     : {entreprise.get('address', 'N/A')}")
            output.append(f"SIRET       : {entreprise.get('siret', 'N/A')}")
            output.append(f"Score       : {entreprise.get('score', 'N/A')}")
            output.append(f"Contact     : {entreprise.get('contactMode', 'N/A')}")
        output.append("\n" + "=" * 50)
        print("\n".join(output))
    else:
        print("\nAucune entreprise trouvée ou une erreur est survenue avec l'API LBB.")

def print_contexte_list(contextes):
    """Affiche une liste de contextes de travail."""
    if not contextes:
        print("Aucun contexte de travail trouvé.")
        return
    print(f"\n--- {len(contextes)} Contextes de travail trouvés ---")
    for ctx in contextes:
        print(f"- {ctx.get('libelle')} (Code: {ctx.get('code')}, Catégorie: {ctx.get('categorie')})")
    print("------------------------------------------")

def print_contexte_details(contexte):
    """Affiche les détails d'un contexte de travail."""
    if not contexte:
        print("Contexte de travail non trouvé.")
        return
    print("\n--- Détails du contexte de travail ---")
    print(f"  Libellé   : {contexte.get('libelle')}")
    print(f"  Code      : {contexte.get('code')}")
    print(f"  Catégorie : {contexte.get('categorie')}")
    print("------------------------------------")

def print_version(version_data):
    """Affiche les informations de version du ROME."""
    if not version_data:
        print("Impossible de récupérer les informations de version.")
        return
    print("\n--- Version du référentiel ROME ---")
    print(f"  Version            : {version_data.get('version')}")
    print(f"  Date de modification : {version_data.get('lastModifiedDate')}")
    print("------------------------------------")


# --- Endpoints Flask (pour une utilisation web future) ---

@app.route('/api/search', methods=['GET'])
def search_jobs_endpoint():
    if not offres_client:
        return jsonify({"error": "L'API n'est pas configurée correctement."}), 503
    params = request.args.to_dict()
    results = offres_client.search_jobs(params)
    return jsonify(results or {"error": "Aucun résultat"})

@app.route('/api/job_details/<job_id>', methods=['GET'])
def job_details(job_id):
    if not offres_client:
        return jsonify({"error": "L'API n'est pas configurée correctement."}), 503
    details = offres_client.get_job_details(job_id)
    return jsonify(details or {"error": "Offre non trouvée"})


# --- Logique pour l'exécution en ligne de commande ---

def handle_search(args):
    """Gère la commande 'search'."""
    params = {}
    if args.keyword:
        params['motsCles'] = args.keyword
    if args.departement:
        params['departement'] = args.departement
    if args.commune:
        params['commune'] = args.commune
    if args.codeROME:
        params['codeROME'] = args.codeROME

    # Utiliser --limit pour définir la plage de résultats, qui est 'range' pour l'API
    params['range'] = f"0-{args.limit - 1}"

    logging.info(f"Recherche d'offres avec les paramètres: {params}")
    results = offres_client.search_jobs(params)
    print_search_results(params, results)

def handle_match(args):
    """Gère la commande 'match'."""
    print(f"Lancement de l'analyse de matching pour le CV {args.cv} et l'offre {args.id_offre}...")
    cv_parser = CVParser()
    try:
        cv_text = cv_parser.extract_text_from_file(args.cv)
        if not cv_text:
            print("Impossible d'extraire le contenu du CV.")
            sys.exit(1)
        
        match_details = offres_client.analyze_cv_match(cv_text, args.id_offre)
        print_cv_match_results(match_details)

    except FileNotFoundError:
        print(f"Erreur: Le fichier CV '{args.cv}' n'a pas été trouvé.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Une erreur est survenue lors de l'analyse du CV: {e}")
        print(f"Une erreur est survenue : {e}")
        sys.exit(1)

def handle_lbb(args):
    """Gère la commande 'lbb'."""
    lbb_params = {
        "rome_codes": args.rome,
        "latitude": args.lat,
        "longitude": args.lon,
        "distance": args.dist,
    }
    if args.naf:
        lbb_params["naf_codes"] = args.naf
    
    logging.info(f"Recherche La Bonne Boite avec les paramètres: {lbb_params}")
    results = lbb_client.search_la_bonne_boite(**lbb_params)
    print_lbb_results(lbb_params, results)

def handle_romeo(args):
    """Gère la commande 'romeo'."""
    print(f"Recherche des codes ROME pour l'intitulé : '{args.intitule}'...")
    try:
        results = romeo_client.predict_metiers(args.intitule, contexte=args.contexte, nb_results=args.nb)
        
        if results and results[0].get('metiersRome'):
            print("\n--- Résultats de la prédiction ROMEO ---")
            predictions = results[0]['metiersRome']
            for i, pred in enumerate(predictions):
                print(f"\n--- Prédiction n°{i+1} ---")
                print(f"  Libellé ROME        : {pred.get('libelleRome')}")
                print(f"  Code ROME           : {pred.get('codeRome')}")
                print(f"  Libellé Appellation : {pred.get('libelleAppellation')}")
                print(f"  Code Appellation    : {pred.get('codeAppellation')}")
                print(f"  Score de confiance  : {pred.get('scorePrediction'):.2f}")
            print("\n------------------------------------")
        else:
            print("Aucune prédiction ROME trouvée pour cet intitulé.")
            if results:
                logging.warning("Réponse inattendue de l'API ROMEO: %s", results)

    except Exception as e:
        logging.error(f"Une erreur est survenue lors de l'appel à l'API ROMEO: {e}")
        print(f"Une erreur est survenue : {e}")

def handle_contexte(args):
    """Gère la commande 'contexte' et ses sous-commandes."""
    if args.subcommand == 'list':
        try:
            results = contexte_client.lister_contextes(champs=args.champs)
            print_contexte_list(results)
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des contextes: {e}")
            print(f"Une erreur est survenue: {e}")
    elif args.subcommand == 'get':
        try:
            results = contexte_client.lire_contexte(code=args.code, champs=args.champs)
            print_contexte_details(results)
        except Exception as e:
            logging.error(f"Erreur lors de la récupération du contexte {args.code}: {e}")
            print(f"Une erreur est survenue: {e}")
    elif args.subcommand == 'version':
        try:
            results = contexte_client.lire_version()
            print_version(results)
        except Exception as e:
            logging.error(f"Erreur lors de la récupération de la version: {e}")
            print(f"Une erreur est survenue: {e}")

def main():
    """Point d'entrée principal pour l'application CLI."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    if not offres_client or not lbb_client or not romeo_client or not soft_skills_client or not contexte_client:
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Client pour les API de France Travail.")
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles', required=True)

    # Commande 'search'
    parser_search = subparsers.add_parser('search', help="Rechercher des offres d'emploi.")
    parser_search.add_argument('keyword', type=str, help='Mot-clé pour la recherche (ex: "développeur python").')
    parser_search.add_argument('--limit', type=int, default=5, help='Nombre de résultats à retourner.')
    parser_search.add_argument('--departement', type=str, help='Numéro de département (ex: "75").')
    parser_search.add_argument('--commune', type=str, help='Code INSEE de la commune.')
    parser_search.add_argument('--codeROME', type=str, help='Code ROME du métier.')
    parser_search.add_argument('--range', type=str, default='0-9', help='Plage de résultats (ex: 0-14).')
    parser_search.set_defaults(func=handle_search)

    # Commande 'match'
    parser_match = subparsers.add_parser('match', help="Analyser la compatibilité d'un CV avec une offre.")
    parser_match.add_argument('cv', type=str, help='Chemin vers le fichier CV (.txt, .pdf, .docx).')
    parser_match.add_argument('id_offre', type=str, help="L'ID de l'offre d'emploi.")
    parser_match.set_defaults(func=handle_match)

    # Commande 'lbb'
    parser_lbb = subparsers.add_parser('lbb', help="Trouver des entreprises à fort potentiel d'embauche.")
    parser_lbb.add_argument('--rome', required=True, type=str, help='Code(s) ROME (séparés par virgule).')
    parser_lbb.add_argument('--lat', required=True, type=float, help='Latitude du point de recherche.')
    parser_lbb.add_argument('--lon', required=True, type=float, help='Longitude du point de recherche.')
    parser_lbb.add_argument('--dist', type=int, default=10, help='Rayon de recherche en km (défaut: 10).')
    parser_lbb.add_argument('--naf', type=str, help='Code(s) NAF (séparés par virgule, optionnel).')
    parser_lbb.set_defaults(func=handle_lbb)

    # Commande 'romeo'
    parser_romeo = subparsers.add_parser('romeo', help="Obtenir des codes ROME pour un intitulé de poste.")
    parser_romeo.add_argument('intitule', type=str, help="L'intitulé de poste à analyser (ex: 'boulanger').")
    parser_romeo.add_argument('--contexte', type=str, help="Contexte optionnel pour affiner la recherche (ex: 'artisanat').")
    parser_romeo.add_argument('--nb', type=int, default=3, help="Nombre de résultats à afficher (défaut: 3).")
    parser_romeo.set_defaults(func=handle_romeo)

    # Commande 'contexte'
    parser_contexte = subparsers.add_parser('contexte', help="Interagir avec l'API Contexte de Travail.")
    contexte_subparsers = parser_contexte.add_subparsers(dest='subcommand', help='Sous-commandes pour contexte', required=True)

    # Sous-commande 'contexte list'
    parser_contexte_list = contexte_subparsers.add_parser('list', help='Lister tous les contextes de travail.')
    parser_contexte_list.add_argument('--champs', type=str, help='Champs à retourner (ex: "libelle,code").')
    parser_contexte_list.set_defaults(func=handle_contexte)

    # Sous-commande 'contexte get'
    parser_contexte_get = contexte_subparsers.add_parser('get', help='Lire un contexte de travail par son code.')
    parser_contexte_get.add_argument('code', type=str, help='Code du contexte de travail.')
    parser_contexte_get.add_argument('--champs', type=str, help='Champs à retourner (ex: "libelle,code").')
    parser_contexte_get.set_defaults(func=handle_contexte)

    # Sous-commande 'contexte version'
    parser_contexte_version = contexte_subparsers.add_parser('version', help='Lire la version actuelle du ROME.')
    parser_contexte_version.set_defaults(func=handle_contexte)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
