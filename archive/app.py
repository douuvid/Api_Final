from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from scrapers.france_travail_original import lancer_scraping
from france_travail.api import OffresClient, LBBClient, RomeoClient, SoftSkillsClient, ContexteTravailClient
from france_travail.cv_parser import CVParser
from dotenv import load_dotenv
import os
import logging

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
CORS(app)  # Activer CORS pour toutes les routes

# Initialiser le parser de CV (utilisé par l'API et le CLI)
cv_parser = CVParser()

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


# --- Endpoints Flask (pour une utilisation web future) ---

@app.route('/')
def home():
    return "Bienvenue sur le serveur de l'application France Travail !"

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

@app.route('/api/match', methods=['POST'])
def api_match_cv():
    if not offres_client or not cv_parser:
        return jsonify({'error': 'Les clients API ou le parser de CV ne sont pas initialisés'}), 503

    data = request.json
    if not data or 'cv_text' not in data or 'job_id' not in data:
        return jsonify({'error': 'Les champs cv_text et job_id sont requis'}), 400
    
    cv_text = data.get('cv_text')
    job_id = data.get('job_id')

    try:
        match_data = offres_client.analyze_cv_match(cv_text, job_id)
        return jsonify(match_data)
    except Exception as e:
        logging.error(f"Erreur lors de l'analyse de compatibilité via API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/lancer-scraping', methods=['POST'])
def lancer_scraping_endpoint():
    data = request.get_json()
    if not data:
        return jsonify({"erreur": "Aucune donnée fournie"}), 400

    identifiant = data.get('identifiant')
    mot_de_passe = data.get('mot_de_passe')
    mots_cles = data.get('mots_cles')
    localisation = data.get('localisation')

    if not all([identifiant, mot_de_passe, mots_cles, localisation]):
        return jsonify({"erreur": "Paramètres manquants"}), 400

    def generate_logs():
        """Appelle le générateur du scraper et formate sa sortie pour SSE."""
        scraper_generator = lancer_scraping(identifiant, mot_de_passe, mots_cles, localisation, headless=True)
        for log_message in scraper_generator:
            # Formatage pour Server-Sent Events (SSE)
            yield f"data: {log_message}\n\n"
    
    # Retourne une réponse en streaming
    return Response(generate_logs(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
