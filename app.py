from flask import Flask, request, jsonify
from france_travail.alternative_client import FranceTravailAlternativeAPI
from dotenv import load_dotenv
import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)

# Initialiser le client API
api = FranceTravailAlternativeAPI(
    client_id=os.getenv("FRANCE_TRAVAIL_CLIENT_ID"),
    client_secret=os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")
)

@app.route('/api/match_skills', methods=['POST'])
def match_skills():
    """
    Endpoint pour le matching de compétences
    Exemple de payload:
    {
        "rome_code": "M1805",
        "skills": ["python", "travail d'équipe", "javascript"]
    }
    """
    data = request.get_json()
    
    if not data or 'rome_code' not in data or 'skills' not in data:
        return jsonify({"error": "Paramètres manquants: rome_code et skills requis"}), 400
    
    try:
        result = api.match_soft_skills(data['rome_code'], data['skills'])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/job_details/<rome_code>', methods=['GET'])
def job_details(rome_code):
    """Récupère les détails d'un métier par son code ROME"""
    try:
        details = api.get_job_details_by_rome(rome_code)
        return jsonify(details)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def search_jobs(keyword: str, location: str = '75056', radius: int = 10, max_results: int = 10) -> Dict:
    """Recherche des offres d'emploi par mot-clé et localisation"""
    if not api.authenticate():
        return {"error": "Échec de l'authentification"}
    
    search_url = f"{api.base_url}/offresdemploi/v2/offres/search"
    headers = {
        'Authorization': f'Bearer {api.access_token}',
        'Content-Type': 'application/json'
    }
    
    params = {
        'motsCles': keyword,
        'commune': location,
        'rayon': str(radius),
        'range': f'0-{max_results-1}',
        'minCreationDate': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    
    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=15)
        if response.status_code in (200, 206):
            return response.json()
        return {"error": f"Erreur {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": str(e)}

@app.route('/api/search_jobs', methods=['GET'])
def search_jobs_endpoint():
    """
    Recherche des offres d'emploi par mot-clé
    Paramètres GET :
    - q : mot-clé de recherche (obligatoire)
    - location : code INSEE (défaut: 75056 pour Paris)
    - radius : rayon en km (défaut: 10)
    - max_results : nombre max de résultats (défaut: 10)
    """
    keyword = request.args.get('q')
    if not keyword:
        return jsonify({"error": "Le paramètre 'q' est requis"}), 400
        
    location = request.args.get('location', '75056')  # Paris par défaut
    radius = int(request.args.get('radius', 10))
    max_results = min(int(request.args.get('max_results', 10)), 50)  # Max 50 résultats
    
    result = search_jobs(keyword, location, radius, max_results)
    return jsonify(result)

@app.route('/api/paris_jobs/<keyword>', methods=['GET'])
def paris_jobs(keyword: str):
    """Recherche des offres d'emploi à Paris par mot-clé (rétrocompatibilité)"""
    result = search_jobs(keyword, '75056', 10, 10)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
