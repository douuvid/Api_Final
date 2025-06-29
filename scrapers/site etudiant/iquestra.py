import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Ajout du chemin racine pour les imports locaux
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.user_database import UserDatabase
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Construire le chemin absolu vers le fichier .env à la racine du projet
# Cela garantit que le bon utilisateur est toujours chargé.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path, override=True)

# --- CONFIGURATION ---
# L'email de l'utilisateur pour lequel lancer le scraper est récupéré depuis .env
USER_EMAIL = os.getenv("USER_EMAIL")

# Ajout d'un print de débogage pour vérifier l'email chargé
print(f"--- DEBUG: Email chargé depuis .env pour le scraping : {USER_EMAIL} ---")
# ---------------------

# Vérification de la variable d'environnement essentielle
if not USER_EMAIL:
    print("❌ ERREUR: La variable d'environnement USER_EMAIL est manquante dans votre fichier .env.")
    sys.exit(1)

URL_ACCUEIL = "https://www.iquesta.com/"

def initialiser_driver():
    """Initialise et retourne le driver Chrome."""
    print("🚀 Initialisation du driver Chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ Driver initialisé.")
        return driver
    except Exception as e:
        print(f"❌ Erreur Driver: {e}")
        return None

def gerer_cookies(driver):
    """Gère le bandeau des cookies."""
    print("🍪 Tentative de gestion des cookies...")
    try:
        bouton_cookies = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
        )
        bouton_cookies.click()
        print("✅ Cookies acceptés.")
    except TimeoutException:
        print("ℹ️ Pas de bannière de cookies détectée.")

def rechercher_offres(driver, metier, region_text):
    """Remplit le formulaire de recherche en utilisant les ID du HTML fourni.
    Priorité à la fonctionnalité directe.
    """
    print(f"\n🔍 Lancement de la recherche pour '{metier}' en '{region_text}' (méthode directe)..." )
    try:
        # 1. Champ métier (ID: controlTerm)
        champ_metier = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "controlTerm"))
        )
        champ_metier.clear()
        champ_metier.send_keys(metier)
        print(f"- Champ métier rempli : '{metier}'")

        # 2. Région (ID: selectRegion)
        if region_text == "Toute la France":
            # On ne touche à rien, l'option par défaut est déjà "Toute la France"
            print(f"- Région sélectionnée : '{region_text}' (par défaut)")
        else:
            select_region_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "selectRegion"))
            )
            select_object = Select(select_region_element)
            select_object.select_by_visible_text(region_text)
            print(f"- Région sélectionnée : '{region_text}'")

        # 3. Bouton Rechercher (type='submit' dans le formulaire)
        # 3. Bouton Rechercher (type='submit' dans le formulaire)
        bouton_rechercher = driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
        bouton_rechercher.click()
        print("✅ Recherche lancée !")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la recherche : {e}")
        # Sauvegarde du HTML pour analyse si ça échoue encore
        with open("iquesta_debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        return False

def affiner_recherche_par_contrat(driver, contract_type):
    """Sélectionne le type de contrat et clique sur le bouton de recherche."""
    print(f"\n🔍 Affinage de la recherche pour le type de contrat : '{contract_type}'...")

    # Dictionnaire de correspondance pour traduire les préférences utilisateur en options du site
    contract_map = {
        "CDI": "Emploi",
        "CDD": "Emploi",
        "Alternance": "Contrat en alternance",
        "Stage": "Stage"
    }

    target_option_text = contract_map.get(contract_type)

    if not target_option_text:
        print(f"⚠️ Type de contrat '{contract_type}' non reconnu. Le filtre ne sera pas appliqué.")
        return False

    try:
        # 1. Sélectionner le type de contrat dans le menu déroulant
        select_contract_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "selectContract"))
        )
        select_object = Select(select_contract_element)
        select_object.select_by_visible_text(target_option_text)
        print(f"- Type de contrat '{target_option_text}' sélectionné.")

        # 2. La page se recharge automatiquement, on attend simplement
        time.sleep(3)  # Attente pour que les résultats se mettent à jour
        print("✅ Recherche affinée.")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'affinage par contrat : {e}")
        return False
        print("✅ Recherche affinée avec succès.")
        return True

    except (TimeoutException, NoSuchElementException) as e:
        print(f"❌ Erreur lors de l'affinage de la recherche par contrat : {e}")
        return False

def recuperer_liens_offres(driver):
    """Récupère tous les liens des offres sur la page de résultats."""
    print("\n🔗 Récupération des liens des offres...")
    try:
        liens_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.fw-bold"))
        )
        liens = [elem.get_attribute('href') for elem in liens_elements]
        print(f"✅ {len(liens)} offres trouvées sur la page.")
        return liens
    except TimeoutException:
        print("❌ Aucune offre trouvée sur la page de résultats.")
        return []

def verifier_et_postuler(driver, user_data):
    """Vérifie si l'offre est interne et lance la candidature si c'est le cas."""
    try:
        # Cherche le bouton qui mène au formulaire de candidature interne d'iQuesta
        bouton_postuler_interne = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='/applications/connectJobPass/']"))
        )
        print("✅ Offre avec candidature interne détectée.")
        bouton_postuler_interne.click()
        # Une fois sur la page du formulaire, on appelle la fonction de remplissage
        return remplir_formulaire_candidature(driver, user_data)
    except TimeoutException:
        # Si ce bouton n'est pas trouvé, on considère que c'est une redirection externe
        print("ℹ️ Offre externe (pas de formulaire iQuesta). Ignorée.")
        return False

def remplir_formulaire_candidature(driver, user_data):
    """Remplit le formulaire de candidature.

    Cette fonction est maintenant appelée APRES avoir cliqué sur le bouton
    de candidature interne.
    """
    print("\n📝 Remplissage du formulaire de candidature...")
    try:
        print("- Page du formulaire de candidature atteinte.")

        # Remplir les champs du formulaire
        print("- Remplissage de l'e-mail...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "application-email"))
        ).send_keys(user_data['email'])

        print("- Remplissage du prénom...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "firstName"))
        ).send_keys(user_data['first_name'])

        print("- Remplissage du nom...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "lastName"))
        ).send_keys(user_data['last_name'])

        print("- Remplissage du message (optionnel)...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "message"))
        ).send_keys("Candidature via un script automatisé de test.")

        # Uploader le CV et la lettre de motivation
        cv_path = user_data.get('cv_path')
        lm_path = user_data.get('lm_path')

        if cv_path:
            absolute_cv_path = os.path.abspath(cv_path)
            print(f"- Téléchargement du CV depuis : {absolute_cv_path}")
            if os.path.exists(absolute_cv_path):
                driver.find_element(By.NAME, "cv").send_keys(absolute_cv_path)
            else:
                print(f"❌ ERREUR : Fichier CV non trouvé à l'emplacement : {absolute_cv_path}")
                return False

        if lm_path:
            absolute_lm_path = os.path.abspath(lm_path)
            print(f"- Téléchargement de la lettre de motivation depuis : {absolute_lm_path}")
            if os.path.exists(absolute_lm_path):
                driver.find_element(By.NAME, "lm").send_keys(absolute_lm_path)
            else:
                print(f"- AVERTISSEMENT : Fichier LM non trouvé à l'emplacement : {absolute_lm_path}")

        # La soumission est maintenant activée.
        print("\n- Clic sur le bouton 'Postuler'...")
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'][value='Postuler']"))
        )
        submit_button.click()

        print("\n✅ Candidature soumise avec succès !")
        return True

    except Exception as e:
        print(f"❌ Erreur lors du remplissage du formulaire. Les sélecteurs sont probablement incorrects.")
        print(f"   Message d'erreur Selenium : {e}")
        print("💾 Sauvegarde du HTML de la page de candidature dans 'iquesta_application_debug.html' pour analyse...")
        with open("iquesta_application_debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("💡 Ouvrez ce fichier et inspectez le formulaire pour trouver les bons sélecteurs (ID, name, class, etc.).")
        print("❌ Échec de la soumission de la candidature.")
        return False

def main():
    """Fonction principale pour orchestrer le scraping."""
    load_dotenv()
    USER_EMAIL = os.getenv("USER_EMAIL")
    PAUSE_DURATION = 10

    if not USER_EMAIL:
        print("❌ La variable d'environnement USER_EMAIL n'est pas définie.")
        return

    driver = None
    db = None  # Initialiser db à None
    try:
        # Initialisation de la base de données en premier
        print("📚 Connexion à la base de données...")
        db = UserDatabase()
        user_data = db.get_user_by_email(USER_EMAIL)
        
        if not user_data:
            print(f"❌ Aucun utilisateur trouvé avec l'e-mail : {USER_EMAIL}. Vérifiez la base de données.")
            return

        user_id = user_data['id']
        print(f"👤 Utilisateur '{user_data.get('first_name')}' (ID: {user_id}) trouvé.")
        
        # Vérification des fichiers CV/LM
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cv_path_relative = user_data.get('cv_path')
        lm_path_relative = user_data.get('lm_path')

        if not cv_path_relative or not lm_path_relative:
            logger.error("❌ ERREUR CRITIQUE : Le chemin du CV ou de la LM n'est pas enregistré pour cet utilisateur.")
            logger.info("🛑 Arrêt du script.")
            db.close()
            sys.exit(1)

        cv_path = os.path.join(project_root, cv_path_relative)
        lm_path = os.path.join(project_root, lm_path_relative)

        if not os.path.exists(cv_path) or not os.path.exists(lm_path):
            logger.error(f"""❌ ERREUR CRITIQUE : Fichier CV ou LM introuvable. Vérifiez les chemins.
   - Chemin CV cherché : {cv_path}
   - Chemin LM cherché : {lm_path}""")
            logger.info("🛑 Arrêt du script.")
            db.close()
            sys.exit(1)
        logger.info("✅ Chemins des fichiers CV et LM validés.")

        # --- 2. Récupérer les préférences de recherche de l'utilisateur ---
        search_query = user_data.get('search_query')
        location = user_data.get('location')
        contract_type = user_data.get('contract_type')

        if not search_query or not location:
            logger.error("❌ ERREUR CRITIQUE : Le métier (search_query) ou le lieu (location) ne sont pas définis. Veuillez les configurer.")
            logger.info("🛑 Arrêt du script.")
            db.close()
            sys.exit(1)

        print(f"ℹ️ Préférences de recherche : Poste='{search_query}', Lieu='{location}', Contrat='{contract_type or 'Non spécifié'}'")

        driver = initialiser_driver()

        driver.get("https://www.iquesta.com/")
        gerer_cookies(driver)
        
        if rechercher_offres(driver, metier=search_query, region_text=location):
            # Après la recherche initiale, on affine par type de contrat si spécifié
            if contract_type:
                if not affiner_recherche_par_contrat(driver, contract_type):
                    print("⚠️ L'affinage par contrat a échoué. Le script continue avec les résultats actuels.")
            else:
                print("ℹ️ Pas de type de contrat spécifié, le filtre ne sera pas appliqué.")

            # On peut maintenant traiter les offres (filtrées ou non)
            try:
                liens_offres = recuperer_liens_offres(driver)
                if not liens_offres:
                    print("ℹ️ Aucune offre à traiter sur la page de résultats. Fin du script.")
                    return

                candidature_reussie = False
                for i, lien in enumerate(liens_offres):
                    print(f"\n--- Traitement de l'offre {i+1}/{len(liens_offres)} ---")
                    
                    if db.check_if_applied(user_id, lien):
                        print("✅ Offre déjà enregistrée dans la base de données. Ignorée.")
                        continue
                    
                    driver.get(lien)
                    
                    if verifier_et_postuler(driver, user_data):
                        db.record_application(user_id, lien)
                        candidature_reussie = True
                        print("\n🎉 Processus de candidature terminé et enregistré !")
                        break # Sortir de la boucle après une candidature réussie
                    else:
                        print("-> Offre non traitable, retour à la page de résultats.")
                        driver.back()
                        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "offerFormSearch")))

                if not candidature_reussie:
                    print("\nℹ️ Aucune nouvelle offre interne et traitable n'a été trouvée sur cette page.")

            except Exception as e:
                print(f"💥 Une erreur est survenue lors du traitement des offres : {e}")
        else:
            print("❌ Échec de la recherche initiale.")

    except Exception as e:
        print(f"💥 Une erreur inattendue est survenue dans main: {e}")
    finally:
        if driver:
            print(f"\n👀 Le navigateur restera ouvert {PAUSE_DURATION} secondes.")
            time.sleep(PAUSE_DURATION)
            print("🚪 Fermeture du navigateur.")
            driver.quit()
        if db:
            db.close()

if __name__ == "__main__":
    main()
