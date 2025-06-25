import os
import sys
import logging

# Ajoute la racine du projet au chemin Python pour résoudre les problèmes d'importation
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
from jose import jwt, JWTError

from auth import create_access_token, get_password_hash, verify_password, Token, SECRET_KEY, ALGORITHM
from database.user_database import UserDatabase

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Initialisation de FastAPI ---
app = FastAPI(title="API Simple")

# --- Configuration CORS ---
origins = [
    "http://localhost:5176",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5177",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Modèles Pydantic ---
class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

class UserInDB(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str

    class Config:
        from_attributes = True

# --- Dépendances ---
def get_db():
    """Crée une instance de UserDatabase et gère la connexion."""
    db = UserDatabase()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: UserDatabase = Depends(get_db)):
    """Valide le jeton et retourne l'utilisateur actuel."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.get_user_by_email(email=email)
    if user is None:
        raise credentials_exception
    return user

# --- Points de terminaison ---
@app.get("/", tags=["Root"])
def read_root():
    return {"message": "API fonctionnelle"}

@app.post("/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
def register_user(user_data: UserRegistration, db: UserDatabase = Depends(get_db)):
    """Inscrit un nouvel utilisateur."""
    logger.info(f"Tentative d'inscription pour l'email : {user_data.email}")
    db_user = db.get_user_by_email(user_data.email)
    if db_user:
        logger.warning(f"Conflit : L'email {user_data.email} existe déjà.")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un utilisateur avec cet email existe déjà")

    try:
        hashed_password = get_password_hash(user_data.password)
        user_info = {
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name
        }
        created_user = db.create_user(user_info, hashed_password)
        
        if not created_user:
            logger.error("Échec de la création de l'utilisateur en base de données.")
            raise HTTPException(status_code=500, detail="La création de l'utilisateur a échoué.")

        logger.info(f"Utilisateur {created_user['email']} créé avec succès.")
        return created_user
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'inscription pour {user_data.email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")

@app.post("/login", response_model=Token, tags=["Authentication"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: UserDatabase = Depends(get_db)):
    """Fournit un jeton d'accès pour un utilisateur authentifié."""
    logger.info(f"Tentative de connexion pour l'utilisateur : {form_data.username}")
    user = db.get_user_by_email(form_data.username)
    
    if not user or not verify_password(form_data.password, user['hashed_password']):
        logger.warning(f"Échec de la connexion pour {form_data.username}: utilisateur non trouvé ou mot de passe incorrect.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"Connexion réussie pour : {user['email']}")
    access_token = create_access_token(data={"sub": user['email']})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserInDB, tags=["Users"])
def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    """Récupère les informations de l'utilisateur actuellement connecté."""
    return current_user
