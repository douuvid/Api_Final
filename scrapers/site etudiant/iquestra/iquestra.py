import os
import sys
import time
import json
import re
import string
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import argparse
from dotenv import load_dotenv

# --- Configuration ---
# Ajout du chemin racine pour les imports locaux
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)
dotenv_path = os.path.join(project_root, '.env')

from database.user_database import UserDatabase

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv(dotenv_path=dotenv_path, override=True)

URL_ACCUEIL = "https://www.iquesta.com/"

def initialiser_driver():
    """Initialise et retourne le driver Chrome."""
    logger.info("Initialisation du driver Chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("Driver initialisé.")
        return driver
    except Exception as e:
        logger.critical(f"Erreur Driver: {e}")
        return None

def gerer_cookies(driver):
    """Gère le bandeau des cookies."""
    logger.info("Tentative de gestion des cookies...")
    try:
        bouton_cookies = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
        )
        bouton_cookies.click()
        logger.info("Cookies acceptés.")
    except TimeoutException:
        logger.info("Pas de bannière de cookies détectée.")

def rechercher_offres(driver, metier, region_text):
    """Remplit le formulaire de recherche et lance la recherche."""
    logger.info(f"Lancement de la recherche pour '{metier}' en '{region_text}'...")
    try:
        champ_metier = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "controlTerm")))
        champ_metier.clear()
        champ_metier.send_keys(metier)
        logger.info(f"- Champ métier rempli : '{metier}'")

        if region_text != "Toute la France":
            try:
                select_region_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "selectRegion")))
                select_object = Select(select_region_element)
                select_object.select_by_visible_text(region_text)
                logger.info(f"- Région sélectionnée : '{region_text}'")
            except NoSuchElementException:
                logger.error(f"ERREUR : La région '{region_text}' est introuvable.")
                try:
                    # Récupérer et afficher toutes les options disponibles pour le débogage
                    options = [option.text for option in select_object.options if option.text.strip() != ""]
                    logger.info("ACTION REQUISE : Veuillez utiliser l'une des régions suivantes dans le profil utilisateur :")
                    for option in options:
                        logger.info(f"- {option}")
                except Exception as e:
                    logger.error(f"Impossible de lister les régions disponibles : {e}")
                return False # Arrête la recherche car la région est invalide

        bouton_rechercher = driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
        bouton_rechercher.click()
        logger.info("Recherche lancée !")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la recherche : {e}")
        return False

def affiner_recherche_par_contrat(driver, contract_type):
    """Sélectionne le type de contrat pour affiner la recherche."""
    logger.info(f"Affinage de la recherche pour le type de contrat : '{contract_type}'...")
    contract_map = {"CDI": "Emploi", "CDD": "Emploi", "Alternance": "Contrat en alternance", "Stage": "Stage"}
    target_option_text = contract_map.get(contract_type)

    if not target_option_text:
        logger.warning(f"Type de contrat '{contract_type}' non reconnu. Le filtre ne sera pas appliqué.")
        return False

    try:
        select_contract_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "selectContract")))
        select_object = Select(select_contract_element)
        select_object.select_by_visible_text(target_option_text)
        logger.info(f"- Type de contrat '{target_option_text}' sélectionné.")
        time.sleep(3)
        logger.info("Recherche affinée.")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'affinage par contrat : {e}")
        return False

def recuperer_liens_offres(driver):
    """Récupère tous les liens des offres sur la page de résultats."""
    logger.info("Récupération des liens des offres...")
    try:
        liens_elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.fw-bold")))
        liens = [elem.get_attribute('href') for elem in liens_elements]
        logger.info(f"DEBUG: {len(liens)} liens d'offres trouvés sur la page.")
        logger.info(f"{len(liens)} offres trouvées sur la page.")
        return liens
    except TimeoutException:
        logger.warning("Aucune offre trouvée sur la page de résultats.")
        return []

def collect_offer_details(driver, offer_url):
    """Collecte les détails d'une offre en utilisant les données structurées JSON-LD, avec fallback."""
    logger.info("Collecte des détails de l'offre...")
    details = {'Lien': offer_url, 'Titre': 'N/A', 'Entreprise': 'N/A', 'Lieu': 'N/A', 'Description': 'N/A'}

    try:
        # Try to get data from JSON-LD first
        json_ld_script = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//script[@type="application/ld+json"]')))
        json_content = json_ld_script.get_attribute('innerHTML')
        json_content_cleaned = "".join(filter(lambda x: x in string.printable, json_content))
        data = json.loads(json_content_cleaned)

        details['Titre'] = data.get('title', 'N/A')
        details['Description'] = data.get('description', 'N/A')
        if 'hiringOrganization' in data and 'name' in data['hiringOrganization']:
            details['Entreprise'] = data['hiringOrganization']['name']
        if 'jobLocation' in data and 'address' in data['jobLocation']:
            addr = data['jobLocation']['address']
            details['Lieu'] = f"{addr.get('streetAddress', '')}, {addr.get('postalCode', '')} {addr.get('addressLocality', '')}".strip(' ,')
        logger.info("Données JSON-LD extraites avec succès.")

    except Exception as e:
        logger.warning(f"Erreur JSON-LD: {e}. Tentative avec sélecteurs classiques.")
        try:
            # Fallback to classic selectors
            details['Titre'] = driver.find_element(By.TAG_NAME, "h1").text.strip()
            # Updated selectors based on analysis
            details['Entreprise'] = driver.find_element(By.XPATH, "//a[contains(@href, '/Entreprise-')]").text.strip()
            details['Lieu'] = driver.find_element(By.XPATH, "//a[contains(@href, 'google.com/maps/search')]").text.strip()
            full_text = driver.find_element(By.XPATH, "//div[contains(@class, 'clean-img')]").text
            details['Description'] = full_text.split('E-mail')[0].strip()
        except Exception as fallback_e:
            logger.error(f"Erreur des sélecteurs de secours: {fallback_e}")
    
    if 'N/A' in details.values():
        logger.warning(f"Données incomplètes pour l'offre. Collectées: {details}")
    
    return details

def verifier_et_postuler(driver, user_data):
    """Remplit le formulaire et simule la postulation à l'offre."""
    try:
        # Attendre que le formulaire soit présent
        form = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "form.form-horizontal"))
        )
        logger.info("Formulaire de candidature trouvé. Remplissage des informations...")

        # Utiliser un bloc try/except pour gérer les formulaires non standards
        try:
            # Remplir les champs
            form.find_element(By.NAME, "email").send_keys(user_data['email'])
            form.find_element(By.NAME, "nom").send_keys(user_data['last_name'])
            form.find_element(By.NAME, "prenom").send_keys(user_data['first_name'])

            # Gérer les uploads de fichiers
            cv_upload = form.find_element(By.ID, "cv")
            cv_upload.send_keys(user_data['cv_path'])
            logger.info(f"- CV chargé : {user_data['cv_path']}")

            lm_upload = form.find_element(By.ID, "lm")
            lm_upload.send_keys(user_data['lm_path'])
            logger.info(f"- LM chargée : {user_data['lm_path']}")
            
            time.sleep(2)

            # La soumission est commentée pour la sécurité. Décommentez pour activer.
            # submit_button = form.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Postuler']")
            # submit_button.click()
            logger.info("CANDIDATURE ENVOYÉE !")
            return True
        except NoSuchElementException as e:
            logger.warning(f"Un champ du formulaire est introuvable. Ce formulaire est probablement non standard. Abandon de la candidature pour cette offre.")
            logger.debug(f"Détail de l'erreur Selenium : {e.msg}")
            return False

    except TimeoutException:
        logger.info("Pas de formulaire de candidature direct trouvé (offre externe probable).")
        return False
    except Exception as e:
        logger.error(f"Erreur inattendue lors du processus de candidature : {e}")
        return False

def main():
    """Fonction principale pour orchestrer le scraping et enregistrer les données."""
    parser = argparse.ArgumentParser(description="Scraper iQuesta pour postuler aux offres d'emploi.")
    parser.add_argument('--email', type=str, help="L'email de l'utilisateur pour lequel lancer le scraper. Surcharge la variable d'environnement USER_EMAIL.")
    args = parser.parse_args()

    user_email_to_use = args.email if args.email else os.getenv("USER_EMAIL")

    if not user_email_to_use:
        logger.critical("ERREUR: Email utilisateur non spécifié. Utilisez l'option --email ou définissez USER_EMAIL dans .env.")
        sys.exit(1)

    logger.info("--- Lancement du Scraper iQuesta ---")
    db = UserDatabase()
    user_data = db.get_user_by_email(user_email_to_use)

    if not user_data:
        logger.critical(f"Utilisateur '{user_email_to_use}' non trouvé. Arrêt.")
        db.close()
        return

    logger.info("DEBUG: Données utilisateur récupérées de la base de données :")
    logger.info(json.dumps(user_data, indent=2, default=str))

    user_id = user_data['id']
    logger.info(f"Utilisateur '{user_data['first_name']}' (ID: {user_id}) trouvé.")

    if not os.path.exists(user_data['cv_path']) or not os.path.exists(user_data['lm_path']):
        logger.critical('Fichier CV ou LM introuvable. Vérifiez les chemins dans la base de données.')
        db.close()
        return
    logger.info("Chemins des fichiers CV et LM validés.")

    search_query = user_data.get('search_query')
    location = user_data.get('location')
    contract_type = user_data.get('contract_type')
    if not search_query or not location:
        logger.critical("--- ACTION REQUISE ---")
        logger.critical("Le 'poste recherché' (search_query) ou le 'lieu' (location) ne sont pas définis pour cet utilisateur.")
        logger.critical("Le scraper ne peut pas lancer de recherche. Veuillez mettre à jour le profil de l'utilisateur.")
        logger.critical("Arrêt du scraper.")
        db.close()
        return
    logger.info(f"Préférences : Poste='{search_query}', Lieu='{location}', Contrat='{contract_type or 'Tous'}'")

    driver = initialiser_driver()
    if not driver:
        db.close()
        return

    sent_applications_count = 0
    try:
        driver.get(URL_ACCUEIL)
        gerer_cookies(driver)
        
        if rechercher_offres(driver, metier=search_query, region_text=location):
            if contract_type:
                affiner_recherche_par_contrat(driver, contract_type)

            liens_offres = recuperer_liens_offres(driver)
            if not liens_offres:
                logger.info("Aucune offre à traiter. Fin.")
                return

            for i, lien in enumerate(liens_offres):
                logger.info(f"--- Traitement de l'offre {i+1}/{len(liens_offres)} ---")
                driver.get(lien)
                
                offer_details = collect_offer_details(driver, lien)
                
                if db.check_if_applied(user_id, lien):
                    logger.info("Déjà postulé (vérifié dans la DB).")
                    offer_details['Statut'] = 'Déjà postulé'
                else:
                    if verifier_et_postuler(driver, user_data):
                        logger.info("Candidature envoyée avec succès. Enregistrement dans la base de données...")
                        offer_details['Statut'] = 'Candidature envoyée'
                        sent_applications_count += 1
                    else:
                        offer_details['Statut'] = 'Échec candidature'
                
                db.record_application(user_id, offer_details)

    finally:
        logger.info("\n--- Résumé de la session ---")
        logger.info(f"Nombre total de candidatures envoyées : {sent_applications_count}")
        if driver:
            logger.info("Fermeture du navigateur.")
            driver.quit()
        if db:
            db.close()
        logger.info("--- Scraper iQuesta terminé ---")

if __name__ == "__main__":
    main()