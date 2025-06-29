import argparse
import sys
import logging
import os
import shutil
import uuid
import subprocess

# Importer le module de base de données
from database.user_database import UserDatabase
from auth import get_password_hash
from utils.data_exporter import export_to_csv

# --- Fonctions d'aide pour l'affichage en console ---

def print_search_results(params, results):
    """Formate et affiche les résultats de recherche d'offres."""
    if results and results.get('resultats'):
        output = []
        total_results = len(results['resultats'])
        limit = params.get('range', 'inconnu').split('-')[1]
        output.append(f"\n{total_results} OFFRES TROUVÉES (sur {limit} demandées)")
        output.append(f"Paramètres: {params}")
        output.append("=" * 50)
        for i, offre in enumerate(results['resultats']):
            output.append(f"\n--- Offre n°{i+1} ---")
            output.append(f"Titre       : {offre.get('intitule', 'N/A')}")
            output.append(f"ID          : {offre.get('id', 'N/A')}")
            output.append(f"Entreprise  : {offre.get('entreprise', {}).get('nom', 'N/A')}")
            output.append(f"Lieu        : {offre.get('lieuTravail', {}).get('libelle', 'N/A')}")
            output.append(f"Contrat     : {offre.get('typeContratLibelle', 'N/A')}")
            output.append(f"ROME        : {offre.get('romeLibelle', 'N/A')} (Code: {offre.get('romeCode', 'N/A')})")
        output.append("\n" + "=" * 50)
        print("\n".join(output))
    else:
        print("\nAucune offre trouvée ou une erreur est survenue.")

def print_match_results(match_data):
    """Formate et affiche les résultats de l'analyse de compatibilité."""
    if not match_data:
        print("L'analyse de compatibilité a échoué.")
        return

    output = []
    output.append("\n--- ANALYSE DE COMPATIBILITÉ CV / OFFRE ---")
    output.append("=" * 50)
    output.append(f"Offre: {match_data['job_title']}")
    output.append(f"Taux de compatibilité : {match_data['matching_rate']:.2f}%")
    output.append("\n--- Compétences comportementales requises ---")
    for skill, present in match_data['required_skills'].items():
        icon = "✅" if present else "❌"
        output.append(f"  [{icon}] {skill}")
    output.append("\n--- Compétences détectées dans le CV ---")
    if match_data['detected_skills']:
        for skill in match_data['detected_skills']:
            output.append(f"  - {skill}")
    else:
        output.append("  Aucune compétence comportementale spécifique détectée.")
    output.append("\n" + "=" * 50)
    print("\n".join(output))

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

# --- Gestionnaires de commandes CLI ---

def handle_search(args):
    """Gère la commande 'search'."""
    print(f"Recherche d'offres pour le mot-clé : '{args.keyword}'...")
    params = {
        'motsCles': args.keyword,
        'range': f"0-{args.limit-1}"
    }
    try:
        results = offres_client.search_jobs(params)
        print_search_results(params, results)
    except Exception as e:
        logging.error(f"Une erreur est survenue lors de la recherche: {e}")
        print(f"Une erreur est survenue : {e}")

def handle_match(args):
    """Gère la commande 'match'."""
    print(f"Analyse du CV '{args.cv_path}' pour l'offre '{args.job_id}'...")
    try:
        cv_text = cv_parser.extract_text_from_file(args.cv_path)
        match_data = offres_client.analyze_cv_match(cv_text, args.job_id)
        print_match_results(match_data)
    except FileNotFoundError:
        logging.error(f"Le fichier CV '{args.cv_path}' n'a pas été trouvé.")
        print(f"Erreur: Le fichier CV '{args.cv_path}' est introuvable.")
    except Exception as e:
        logging.error(f"Une erreur est survenue lors de l'analyse: {e}")
        print(f"Une erreur est survenue : {e}")

def handle_lbb(args):
    """Gère la commande 'lbb'."""
    params = {
        'rome_codes': args.rome_code,
        'latitude': args.latitude,
        'longitude': args.longitude,
        'distance': args.distance
    }
    print(f"Recherche d'entreprises (La Bonne Boîte) avec les paramètres: {params}")
    try:
        results = lbb_client.search_companies(params)
        print_lbb_results(params, results)
    except Exception as e:
        logging.error(f"Une erreur est survenue lors de l'appel à l'API LBB: {e}")
        print(f"Une erreur est survenue : {e}")

def handle_romeo(args):
    """Gère la commande 'romeo'."""
    print(f"Recherche du code ROME pour l'intitulé : \"{args.intitule}\"...")
    try:
        results = romeo_client.predict_metiers(
            job_title=args.intitule,
            context=args.contexte,
            nb_results=args.nb
        )
        
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

def handle_db(args):
    """Gère les commandes liées à la base de données."""
    if args.subcommand == 'init':
        print("Initialisation de la base de données...")
        db = UserDatabase(
            host=DatabaseConfig.HOST,
            database=DatabaseConfig.DATABASE,
            user=DatabaseConfig.USER,
            password=DatabaseConfig.PASSWORD,
            port=DatabaseConfig.PORT
        )
        if db.connect():
            print("Création des tables...")
            db.create_tables()
            db.disconnect()
            print("\n✅ Base de données initialisée avec succès.")
        else:
            print("\n❌ Échec de l'initialisation de la base de données. Vérifiez votre configuration .env et que PostgreSQL est en cours d'exécution.")

def handle_user_command(args):
    """Gère les commandes liées aux utilisateurs."""
    db = UserDatabase()
    try:
        if args.subcommand == 'create':
            hashed_password = get_password_hash(args.password)
            user_data = {
                'email': args.email,
                'first_name': args.first_name,
                'last_name': args.last_name,
                'search_query': args.search_query,
                'contract_type': args.contract_type,
                'location': args.location
            }
            new_user = db.create_user(user_data, hashed_password)
            print(f"Utilisateur '{new_user['email']}' créé avec succès avec l'ID {new_user['id']}.")

        elif args.subcommand == 'update-docs':
            user = db.get_user_by_email(args.email)
            if not user:
                print(f"Erreur : Utilisateur avec l'email '{args.email}' non trouvé.")
                return

            user_id = user['id']
            upload_dir = os.path.join(os.path.dirname(__file__), 'upload_cv_lm_utilisateur')
            os.makedirs(upload_dir, exist_ok=True)

            new_cv_path = None
            if args.cv_path:
                if not os.path.exists(args.cv_path):
                    print(f"Fichier CV non trouvé à l'emplacement : {args.cv_path}")
                    return
                cv_filename = f"{user_id}_cv_{uuid.uuid4().hex}.pdf"
                new_cv_path = os.path.join(upload_dir, cv_filename)
                shutil.copy(args.cv_path, new_cv_path)
                print(f"CV copié vers : {new_cv_path}")

            new_lm_path = None
            if args.lm_path:
                if not os.path.exists(args.lm_path):
                    print(f"Fichier LM non trouvé à l'emplacement : {args.lm_path}")
                    return
                lm_filename = f"{user_id}_lm_{uuid.uuid4().hex}.pdf"
                new_lm_path = os.path.join(upload_dir, lm_filename)
                shutil.copy(args.lm_path, new_lm_path)
                print(f"LM copiée vers : {new_lm_path}")

            db.update_user_document_paths(user_id, cv_path=new_cv_path, lm_path=new_lm_path)
            print(f"Chemins des documents mis à jour pour l'utilisateur '{args.email}'.")

            if args.lancer_scraper:
                print(f"\nLancement du scraper iQuesta pour l'utilisateur {args.email}...")
                # Construire le chemin absolu vers le scraper
                base_dir = os.path.dirname(__file__)
                scraper_path = os.path.join(base_dir, 'scrapers', 'site etudiant', 'iquestra', 'iquestra.py')
                
                try:
                    # Lancer le scraper. La sortie s'affichera directement dans le terminal
                    # car stdout/stderr ne sont pas redirigés.
                    process = subprocess.Popen(['python3', scraper_path, '--email', args.email], text=True)
                    
                    # Attendre la fin du processus
                    process.wait()
                    
                    # Vérifier le code de retour après la fin du processus
                    if process.returncode == 0:
                        print("\n--- Scraper terminé ---")
                    else:
                        print(f"\n--- Le scraper s'est terminé avec une erreur (code {process.returncode}) ---")

                except FileNotFoundError:
                    print(f"ERREUR CRITIQUE : Le script du scraper est introuvable à l'emplacement '{scraper_path}'")
                except Exception as e:
                    print(f"ERREUR CRITIQUE : Une erreur inattendue est survenue lors du lancement du scraper : {e}")

        elif args.subcommand == 'reset-apps':
            user = db.get_user_by_email(args.email)
            if not user:
                print(f"Utilisateur {args.email} non trouvé.")
                return

            user_id = user['id']
            print(f"Réinitialisation des candidatures pour {args.email}...")
            if db.reset_user_applications(user_id):
                print(f"Candidatures pour {args.email} réinitialisées avec succès.")
            else:
                print(f"Échec de la réinitialisation des candidatures pour {args.email}.")

        elif args.subcommand == 'download-report':
            user = db.get_user_by_email(args.email)
            if not user:
                print(f"Utilisateur {args.email} non trouvé.")
                return
            
            user_id = user['id']
            print(f"Génération du rapport de candidatures pour {args.email}...")
            applications = db.get_user_applications(user_id)

            if not applications:
                print("Aucune candidature trouvée pour cet utilisateur.")
                return

            # Renommer les clés pour des en-têtes plus clairs en français
            report_data = []
            for app in applications:
                report_data.append({
                    'Titre': app.get('title'),
                    'Entreprise': app.get('company'),
                    'Lieu': app.get('location'),
                    'Statut': app.get('status'),
                    'Date': app.get('applied_at').strftime('%Y-%m-%d %H:%M'),
                    'Lien': app.get('offer_url'),
                    'Description': app.get('description')
                })
            
            export_to_csv(args.email, report_data, report_type='candidatures', subdirectory='report_iquestra')
            
        elif args.subcommand == 'update-prefs':
            user = db.get_user_by_email(args.email)
            if not user:
                print(f"Utilisateur {args.email} non trouvé.")
                return

            prefs_to_update = {}
            if args.search_query:
                prefs_to_update['search_query'] = args.search_query
            if args.location:
                prefs_to_update['location'] = args.location
            if args.contract_type:
                prefs_to_update['contract_type'] = args.contract_type

            if not prefs_to_update:
                print("Aucune préférence à mettre à jour n'a été spécifiée.")
                return

            if db.update_user_prefs(user['id'], prefs_to_update):
                print(f"Préférences mises à jour pour {args.email}.")
            else:
                print(f"Échec de la mise à jour des préférences pour {args.email}.")

    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        db.close()

def handle_db(args):
    """Gère les commandes liées à la base de données."""
    if args.subcommand == 'init':
        try:
            db = UserDatabase()
            db.close()
            print("✅ Base de données initialisée avec succès.")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de la base de données : {e}")

def main():
    """Point d'entrée principal pour l'application CLI."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Client pour les API de France Travail.")
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles', required=True)

    # Commande 'search'
    parser_search = subparsers.add_parser('search', help='Rechercher des offres d_emploi.')
    parser_search.add_argument('keyword', type=str, help='Mot-clé pour la recherche.')
    parser_search.add_argument('--limit', type=int, default=5, help='Nombre de résultats à afficher.')
    parser_search.set_defaults(func=handle_search)

    # Commande 'match'
    parser_match = subparsers.add_parser('match', help='Analyser la compatibilité entre un CV et une offre.')
    parser_match.add_argument('cv_path', type=str, help='Chemin vers le fichier CV (.txt).')
    parser_match.add_argument('job_id', type=str, help='ID de l_offre d_emploi.')
    parser_match.set_defaults(func=handle_match)

    # Commande 'lbb'
    parser_lbb = subparsers.add_parser('lbb', help='Trouver des entreprises qui recrutent (La Bonne Boîte).')
    parser_lbb.add_argument('rome_code', type=str, help='Code ROME du métier recherché.')
    parser_lbb.add_argument('latitude', type=float, help='Latitude du point de recherche.')
    parser_lbb.add_argument('longitude', type=float, help='Longitude du point de recherche.')
    parser_lbb.add_argument('--distance', type=int, default=10, help='Rayon de recherche en km.')
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

    # Commande 'db'
    parser_db = subparsers.add_parser('db', help='Gérer la base de données.')
    db_subparsers = parser_db.add_subparsers(dest='subcommand', help='Sous-commandes pour la base de données', required=True)

    # Sous-commande 'db init'
    parser_db_init = db_subparsers.add_parser('init', help='Initialiser la base de données et créer les tables.')
    parser_db_init.set_defaults(func=handle_db)

    # Commande 'user'
    parser_user = subparsers.add_parser('user', help='Gérer les utilisateurs.')
    user_subparsers = parser_user.add_subparsers(dest='subcommand', required=True, help='Sous-commandes utilisateur')

    # Sous-commande 'update-prefs'
    prefs_parser = user_subparsers.add_parser('update-prefs', help='Mettre à jour les préférences de recherche d\'un utilisateur.')
    prefs_parser.add_argument('--email', type=str, required=True, help='Email de l\'utilisateur à mettre à jour.')
    prefs_parser.add_argument('--search-query', type=str, help='Nouveau poste recherché.')
    prefs_parser.add_argument('--location', type=str, help='Nouveau lieu de recherche.')
    prefs_parser.add_argument('--contract-type', type=str, help='Nouveau type de contrat.')
    prefs_parser.set_defaults(func=handle_user_command)

    # Sous-commande 'create'
    parser_user_create = user_subparsers.add_parser('create', help='Créer un nouvel utilisateur.')
    parser_user_create.add_argument('--email', required=True, help="Email de l'utilisateur.")
    parser_user_create.add_argument('--password', required=True, help="Mot de passe de l'utilisateur.")
    parser_user_create.add_argument('--first-name', required=True, help="Prénom de l'utilisateur.")
    parser_user_create.add_argument('--last-name', required=True, help="Nom de l'utilisateur.")
    parser_user_create.add_argument('--search-query', help="Poste recherché par défaut.")
    parser_user_create.add_argument('--contract-type', help="Type de contrat par défaut.")
    parser_user_create.add_argument('--location', help="Lieu de recherche par défaut.")
    parser_user_create.set_defaults(func=handle_user_command)

    # Sous-commande 'user update-docs'
    parser_user_update = user_subparsers.add_parser('update-docs', help="Mettre à jour le CV et la LM d'un utilisateur.")
    parser_user_update.add_argument('--email', required=True, help="Email de l'utilisateur à mettre à jour.")
    parser_user_update.add_argument('--cv-path', help="Chemin complet vers le nouveau fichier CV.")
    parser_user_update.add_argument('--lm-path', help="Chemin complet vers le nouveau fichier LM.")
    parser_user_update.add_argument('--lancer-scraper', action='store_true', help='Lancer le scraper iQuesta immédiatement après la mise à jour.')
    parser_user_update.set_defaults(func=handle_user_command)

    # Sous-commande 'user reset-apps'
    parser_user_reset = user_subparsers.add_parser('reset-apps', help="Réinitialise les candidatures pour un utilisateur spécifique.")
    parser_user_reset.add_argument('--email', required=True, help="Email de l'utilisateur dont les candidatures seront supprimées.")
    parser_user_reset.set_defaults(func=handle_user_command)

    # Sous-commande 'user download-report'
    parser_user_download = user_subparsers.add_parser('download-report', help="Télécharge un rapport CSV des candidatures d'un utilisateur.")
    parser_user_download.add_argument('--email', required=True, help="Email de l'utilisateur pour lequel générer le rapport.")
    parser_user_download.set_defaults(func=handle_user_command)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

def reset_apps(email: str):
    """Réinitialise (supprime) toutes les candidatures pour un utilisateur donné."""
    db = None
    try:
        db = UserDatabase()
        user = db.get_user_by_email(email)
        if not user:
            print(f"Utilisateur {email} non trouvé.")
            return
        
        user_id = user['id']
        if db.reset_user_applications(user_id):
            print(f"✅ Toutes les candidatures pour {email} ont été supprimées.")
        else:
            print(f"❌ Échec de la suppression des candidatures pour {email}.")

    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    # Check if a typer command is being invoked
    import sys
    if len(sys.argv) > 1 and sys.argv[1] in ["reset-apps"]:
        app()
    else:
        main()
