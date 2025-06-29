import os
import sys
import logging
import shutil
import uuid
from typing import Optional

# Ajoute la racine du projet au chemin Python pour résoudre les problèmes d'importation
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
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

# --- Constantes ---
UPLOAD_DIR = "upload_cv_lm_utilisateur"

# --- Initialisation de FastAPI ---
app = FastAPI(
    title="Job Search API",
    description="API pour gérer les utilisateurs et les recherches d'emploi.",
    version="1.0.0"
)

# --- Configuration CORS ---
origins = [
    "http://localhost:5176",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5177",
    "http://127.0.0.1:5173",
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
    cv_path: Optional[str] = None
    lm_path: Optional[str] = None

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
def read_users_me(current_user: dict = Depends(get_current_user)):
    """Récupère les informations de l'utilisateur actuellement connecté."""
    return current_user

@app.post("/users/me/upload-document", response_model=UserInDB, tags=["Users"])
def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...), # 'cv' ou 'lm'
    current_user: dict = Depends(get_current_user),
    db: UserDatabase = Depends(get_db)
):
    print("\n\n!!!!!!!!!!!!!! POINT DE CONTRÔLE : DÉBUT DE L'UPLOAD !!!!!!!!!!!!!!\n\n")
    """Permet à un utilisateur d'uploader son CV ou sa lettre de motivation."""
    if doc_type not in ["cv", "lm"]:
        raise HTTPException(status_code=400, detail="Le type de document doit être 'cv' ou 'lm'.")

    # Crée un nom de fichier unique pour éviter les conflits
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{current_user['id']}_{doc_type}_{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        logger.info("--- Début de l'upload de document ---")
        logger.info(f"Étape 1: Tentative de sauvegarde du fichier sur le disque à l'emplacement : {file_path}")
        
        # S'assurer que le répertoire d'upload existe
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Sauvegarde le fichier sur le disque
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Étape 2: Fichier '{file.filename}' sauvegardé avec succès.")

        # Met à jour le chemin dans la base de données
        update_data = {}
        if doc_type == "cv":
            update_data['cv_path'] = file_path
        else:
            update_data['lm_path'] = file_path
        
        logger.info(f"Étape 3: Tentative de mise à jour de la base de données avec les informations : {update_data}")
        updated_user = db.update_user_document_paths(user_id=current_user['id'], **update_data)
        
        if not updated_user:
            raise Exception("La mise à jour de la base de données n'a retourné aucun utilisateur.")

        logger.info("Étape 4: Mise à jour de la base de données réussie.")
        return updated_user

    except Exception as e:
        logger.error(f"Erreur lors de l'upload du fichier pour {current_user['email']}: {e}", exc_info=True)
        # Optionnel: supprimer le fichier si l'update DB échoue
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde du fichier.")
