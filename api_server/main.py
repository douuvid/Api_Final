import sys
import os
from fastapi import FastAPI
from pydantic import BaseModel

# Ajouter le répertoire racine du projet au chemin de recherche des modules
# pour permettre les importations depuis 'france_travail' et 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer les clients API initialisés depuis le module app
# C'est une bonne pratique pour ne pas dupliquer l'initialisation
from app import offres_client, lbb_client, romeo_client, soft_skills_client, contexte_client, cv_parser

app = FastAPI(
    title="France Travail API Wrapper",
    description="Une API qui encapsule et étend les services de France Travail.",
    version="1.0.0"
)

@app.get("/", tags=["Général"])
def read_root():
    """Endpoint racine pour vérifier que l'API est en ligne."""
    return {"message": "Bienvenue sur l'API du wrapper France Travail"}

# --- Endpoints pour les Offres d'Emploi --- #

@app.get("/search", tags=["Offres d'emploi"])
def search_jobs(keywords: str, range: str = "0-19"):
    """
    Recherche des offres d'emploi en utilisant des mots-clés.

    - **keywords**: Le ou les mots-clés à rechercher.
    - **range**: La plage de résultats à retourner (ex: "0-19").
    """
    try:
        params = {
            'motsCles': keywords,
            'range': range
        }
        result = offres_client.search_jobs(params=params)
        return result
    except Exception as e:
        # Idéalement, nous devrions gérer les erreurs HTTP plus spécifiquement
        return {"error": str(e)}


@app.get("/details/{job_id}", tags=["Offres d'emploi"])
def get_job_details(job_id: str):
    """
    Récupère les détails d'une offre d'emploi spécifique par son ID.

    - **job_id**: L'identifiant de l'offre (ex: "194DZZT").
    """
    try:
        result = offres_client.get_job_details(job_id=job_id)
        return result
    except Exception as e:
        return {"error": str(e)}


# --- Modèles de Données (Pydantic) --- #

class CVData(BaseModel):
    cv_text: str
    class Config:
        schema_extra = {
            "example": {
                "cv_text": "Je suis un développeur expérimenté avec des compétences en Python, analyse de données et communication."
            }
        }

# --- Endpoint pour l'analyse de CV --- #

@app.post("/match/{job_id}", tags=["Matching CV"])
def match_cv_to_job(job_id: str, cv_data: CVData):
    """
    Analyse la compatibilité entre le texte d'un CV et une offre d'emploi.

    - **job_id**: L'identifiant de l'offre.
    - **Request Body**: Doit contenir le texte brut du CV.
    """
    try:
        result = offres_client.analyze_cv_match(cv_text=cv_data.cv_text, job_id=job_id)
        return result
    except Exception as e:
        return {"error": str(e)}


# --- Futurs Endpoints --- #
# Ici, nous ajouterons les endpoints pour la recherche, le matching, etc.


if __name__ == '__main__':
    import uvicorn
    # Pour lancer l'API, exécutez la commande suivante depuis le dossier racine :
    # uvicorn api_server.main:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
