import logging
import sys
import os
import time
import random

# Ajout du chemin racine du projet pour permettre les imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException, ElementClickInterceptedException, 
    StaleElementReferenceException, WebDriverException, ElementNotInteractableException
)
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from database.user_database import UserDatabase

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Fonctions robustes de bas niveau (inspirées du code utilisateur) ---

def setup_driver():
    """Configure un driver Chrome robuste."""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-gpu")
    prefs = {"profile.default_content_setting_values.notifications": 2}
    options.add_experimental_option("prefs", prefs)
    
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(40)
        return driver
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création du driver: {e}")
        return None

def try_select_suggestion(driver, field_id):
    """Tente de sélectionner une suggestion avec plusieurs stratégies."""
    logger.info("🔍 Recherche de suggestions...")
    strategies = [
        {'name': 'MUI/DSFR Selectors', 'selectors': [".MuiAutocomplete-listbox [role='option']:first-child", ".fr-menu [role='option']:first-child"]},
        {'name': 'Generic Listbox', 'selectors': ["[role='listbox'] [role='option']:first-child"]},
        {'name': 'Keyboard Navigation', 'action': 'keyboard'}
    ]
    
    for strategy in strategies:
        try:
            logger.info(f"🎯 Stratégie: {strategy['name']}")
            if strategy.get('action') == 'keyboard':
                input_element = driver.find_element(By.ID, field_id)
                input_element.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.4)
                input_element.send_keys(Keys.ENTER)
                time.sleep(0.5)
                logger.info("✅ Sélection par clavier.")
                return True
            else:
                for selector in strategy.get('selectors', []):
                    suggestions = driver.find_elements(By.CSS_SELECTOR, selector)
                    for suggestion in suggestions:
                        if suggestion.is_displayed() and suggestion.is_enabled():
                            text = suggestion.text.strip()
                            if text:
                                logger.info(f"🎯 Clic sur suggestion: '{text}'")
                                driver.execute_script("arguments[0].click();", suggestion)
                                time.sleep(1)
                                return True
        except Exception as e:
            logger.warning(f"⚠️ Stratégie '{strategy['name']}' échouée: {e}")
            continue
    return False

def fill_mui_autocomplete(driver, wait, field_id, value, max_retries=3):
    """Remplit un champ autocomplete MUI/DSFR de manière robuste."""
    logger.info(f"🎯 Remplissage du champ '{field_id}' avec '{value}'")
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 Tentative {attempt}/{max_retries} pour le champ '{field_id}'")
            
            # Stratégie : cliquer sur le label pour activer le champ, puis interagir.
            label_selector = (By.CSS_SELECTOR, f"label[for='{field_id}']")
            try:
                label = wait.until(EC.element_to_be_clickable(label_selector))
                label.click()
                logger.info(f"✅ Label pour '{field_id}' cliqué.")
            except Exception as e:
                logger.error(f"Impossible de cliquer sur le label pour {field_id}: {e}")
                # Tenter de cliquer directement sur l'input comme fallback
                input_field = wait.until(EC.element_to_be_clickable((By.ID, field_id)))
                input_field.click()

            # L'input est maintenant trouvé par son ID après l'activation
            input_field = wait.until(EC.visibility_of_element_located((By.ID, field_id)))
            
            # Clic et nettoyage
            driver.execute_script("arguments[0].click();", input_field)
            time.sleep(0.5)
            input_field.send_keys(Keys.CONTROL + "a", Keys.DELETE)
            time.sleep(0.5)

            # Saisie progressive
            logger.info(f"⌨️  Saisie de '{value}'...")
            actions = ActionChains(driver)
            for char in value:
                actions.send_keys(char).pause(random.uniform(0.05, 0.15)).perform()
            
            time.sleep(1.5) # Attendre l'apparition des suggestions

            if try_select_suggestion(driver, field_id):
                logger.info(f"✅ Champ '{field_id}' rempli avec succès!")
                return True
            else:
                logger.warning(f"⚠️ Aucune suggestion sélectionnée pour '{field_id}', validation par TAB.")
                input_field.send_keys(Keys.TAB)
                time.sleep(0.5)
                final_value = input_field.get_attribute('value')
                if final_value and value.lower() in final_value.lower():
                    logger.info(f"✅ Validation par TAB réussie: '{final_value}'")
                    return True

            logger.error(f"❌ Tentative {attempt + 1} échouée.")

        except Exception as e:
            logger.error(f"❌ Erreur critique dans la tentative {attempt + 1} pour '{field_id}': {e}", exc_info=False)
            if attempt >= max_retries - 1:
                raise e
            time.sleep(2)
            
    logger.error(f"❌ Échec final du remplissage du champ '{field_id}'")
    return False

# --- Processus de scraping principal ---

def run_scraper(user_data):
    logger.info(f"Lancement du scraper pour : {user_data['email']}")
    driver = None
    try:
        driver = setup_driver()
        if not driver:
            return

        url = "https://www.alternance.emploi.gouv.fr/recherches-offres-formations"
        logger.info(f"Accès à l'URL : {url}")
        driver.get(url)
        wait = WebDriverWait(driver, 20)

        try:
            cookie_button = wait.until(EC.element_to_be_clickable((By.ID, "tarteaucitronPersonalize2")))
            cookie_button.click()
            logger.info("Bannière de cookies acceptée.")
        except Exception:
            logger.warning("Bannière de cookies non trouvée ou déjà acceptée.")

        try:
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[src*='labonnealternance']")))
            logger.info("Basculement vers l'iframe réussi.")
        except Exception as e:
            logger.error(f"Impossible de basculer vers l'iframe: {e}")
            raise

        logger.info("Attente de la présence de la modale du formulaire.")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".fr-modal__body")))
        time.sleep(1) # Laisse le temps à la modale de se stabiliser

        if not fill_mui_autocomplete(driver, wait, "metier", user_data['search_query']):
            raise Exception("Impossible de remplir le champ métier")

        # On ferme le menu déroulant des suggestions qui pourrait masquer le champ suivant.
        logger.info("Fermeture du menu déroulant avec la touche ESCAPE.")
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5) # Petite pause pour laisser l'interface se stabiliser

        if not fill_mui_autocomplete(driver, wait, "lieu", user_data['location']):
            raise Exception("Impossible de remplir le champ lieu")

        logger.info("Tentative de soumission du formulaire.")
        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'][title=\"C'est parti\"]")))
        submit_button.click()
        logger.info("Formulaire soumis. Scraping terminé avec succès.")
        time.sleep(10)

    except Exception as e:
        logger.error(f"Une erreur est survenue dans run_scraper: {e}", exc_info=True)
        if driver:
            timestamp = int(time.time())
            driver.save_screenshot(f'error_screenshot_{timestamp}.png')
            with open(f'error_page_{timestamp}.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info(f"Screenshot et source de la page sauvegardés.")
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver fermé.")

def main():
    user_email = 'test@example.com' # Email par défaut pour le test
    if len(sys.argv) > 1 and sys.argv[1] != 'test@example.com':
        user_email = sys.argv[1]
    
    logger.info(f"Recherche de l'utilisateur : {user_email}")
    db = UserDatabase()
    user_data = db.get_user_by_email(user_email)
    db.close()
    
    if not user_data:
        logger.warning(f"Utilisateur non trouvé, utilisation d'un profil de test.")
        user_data = {'email': 'test@example.com', 'search_query': 'Développeur web', 'location': 'Paris'}

    if user_data:
        run_scraper(user_data)
    else:
        logger.error(f"Aucune donnée utilisateur disponible pour lancer le scraper.")

if __name__ == "__main__":
    main()