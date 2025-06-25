import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from dotenv import load_dotenv

# Charger les variables d'environnement du fichier .env
load_dotenv()

# Importer notre module de base de données
from database.user_database import UserDatabase

# --- Modèles Pydantic pour la validation des données ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None # Format YYYY-MM-DD
    gender: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- Initialisation de l'application FastAPI ---

app = FastAPI(
    title="Job Search API",
    description="API for managing users and job searches.",
    version="1.0.0"
)

# --- Configuration CORS ---
# Autoriser les requêtes depuis n'importe quelle origine (à ajuster pour la production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Attention: Pour le développement uniquement
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Connexion à la base de données ---

def get_db():
    """Fonction de dépendance pour obtenir une instance de la base de données."""
    db = UserDatabase(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5433)),
        database=os.getenv("DB_NAME", "job_search_app"),
        user=os.getenv("DB_USER", "davidravin"),
        password=os.getenv("DB_PASSWORD", "")
    )
    if not db.connect():
        raise HTTPException(status_code=503, detail="Could not connect to the database.")
    try:
        yield db
    finally:
        db.disconnect()

# --- Points de terminaison (Endpoints) ---

@app.get("/", tags=["Root"])
def read_root():
    """Point de terminaison racine pour vérifier que l'API est en ligne."""
    return {"message": "Welcome to the Job Search API!"}

@app.post("/register", status_code=201, tags=["Authentication"])
def register_user(user_data: UserCreate, db: UserDatabase = Depends(get_db)):
    """
    Crée un nouvel utilisateur dans la base de données.
    """
    try:
        user_dict = user_data.dict()
        user_id, token = db.create_user(user_dict)
        return {
            "message": "User created successfully. Please check your email to verify your account.",
            "user_id": user_id,
            "verification_token": token # Pour le développement/test
        }
    except ValueError as e:
        # Capture les e-mails en double
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.post("/login", tags=["Authentication"])
def login_user(login_data: UserLogin, db: UserDatabase = Depends(get_db)):
    """
    Authentifie un utilisateur et retourne un jeton de session.
    """
    try:
        user, message = db.authenticate_user(login_data.email, login_data.password)

        if not user:
            # Distinguer les différents types d'échecs
            if "verrouillé" in message:
                raise HTTPException(status_code=403, detail=message)
            else:
                raise HTTPException(status_code=401, detail=message)

        # Si l'authentification réussit, user est un dictionnaire
        # Dans une application réelle, vous généreriez un jeton JWT ici
        session_token = f"fake-session-token-for-{user['id']}"  # Placeholder
        return {
            "message": "Login successful",
            "user_id": user['id'],
            "session_token": session_token
        }
    except Exception as e:
        # Capturer toute autre erreur inattendue pour la sécurité
        raise HTTPException(status_code=500, detail=f"An internal server error occurred.")
