import os
import pg8000.dbapi
from dotenv import load_dotenv

# Charger les variables d'environnement du fichier .env
# Assurez-vous que votre fichier .env est à la racine du projet
load_dotenv()

def test_connection():
    """
    Tente de se connecter à la base de données PostgreSQL en utilisant pg8000
    et affiche le statut de la connexion.
    """
    try:
        print("--- Début du test de connexion avec pg8000 ---")
        
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")

        if not all([db_user, db_password, db_host, db_port, db_name]):
            print("❌ Erreur: Toutes les variables d'environnement de la base de données ne sont pas définies.")
            print("Veuillez vérifier votre fichier .env : DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME")
            return

        print(f"Paramètres de connexion : user={db_user}, host={db_host}, port={db_port}, database={db_name}")

        # Connexion à la base de données
        conn = pg8000.dbapi.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=int(db_port),
            database=db_name
        )
        
        print("✅✅✅ Connexion réussie ! ✅✅✅")
        
        # Exécuter une requête simple pour vérifier que tout fonctionne
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"Version de PostgreSQL détectée : {version}")
        
        cursor.close()
        conn.close()
        print("--- Fin du test de connexion ---")
        
    except Exception as e:
        print("❌❌❌ Échec de la connexion. ❌❌❌")
        print(f"Erreur détaillée : {e}")
        print("--- Fin du test de connexion ---")

if __name__ == "__main__":
    test_connection()
