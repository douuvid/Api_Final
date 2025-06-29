import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Ajout du chemin racine pour les imports locaux
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.user_database import UserDatabase

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# --- CONFIGURATION ---
# L'email de l'utilisateur pour lequel lancer le scraper est récupéré depuis .env
USER_EMAIL = os.getenv("USER_EMAIL")
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

def rechercher_offres(driver, metier, region):
    """Remplit le formulaire de recherche et lance la recherche."""
    print(f"\n🔍 Lancement de la recherche pour '{metier}' en '{region}'...")
    try:
        champ_metier = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "query")))
        champ_metier.send_keys(metier)
        print(f"- Champ métier rempli : '{metier}'")

        region_dropdown = driver.find_element(By.CSS_SELECTOR, "button[data-id='region']")
        region_dropdown.click()
        
        option_xpath = f"//span[contains(text(), '{region}')]"
        option_region = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, option_xpath)))
        option_region.click()
        print(f"- Région sélectionnée : '{region}'")

        bouton_rechercher = driver.find_element(By.ID, "submit-search-form")
        bouton_rechercher.click()
        print("✅ Recherche lancée !")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la recherche : {e}")
        return False

def cliquer_premiere_offre(driver):
    """Clique sur la première offre dans les résultats."""
    print("\n📄 Analyse de la page de résultats...")
    try:
        offre_selector = "a.job-title.stretched-link"
        premiere_offre = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, offre_selector))
        )
        print("✅ Première offre trouvée. Clic en cours...")
        driver.execute_script("arguments[0].click();", premiere_offre)
        return True
    except Exception as e:
        print(f"❌ Erreur lors du clic sur la première offre : {e}")
        return False

def remplir_formulaire_candidature(driver, user_email, first_name, last_name, cv_path, lm_path):
    """Remplit le formulaire de candidature dans le nouvel onglet."""
    print("\n📝 Remplissage du formulaire de candidature...")
    try:
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        driver.switch_to.window(driver.window_handles[1])
        print("- Basculement vers l'onglet de l'offre.")

        wait = WebDriverWait(driver, 20)
        
        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        email_input.send_keys(user_email)

        name_input = driver.find_element(By.ID, "name")
        name_input.send_keys(f"{first_name} {last_name}")
        
        message_input = driver.find_element(By.ID, "message")
        message_input.send_keys(f"Bonjour,\n\nCandidature de la part de {first_name} {last_name}.\n\nCordialement.")
        print("- Champs texte remplis.")

        if not cv_path or not os.path.exists(cv_path):
            print(f"❌ ERREUR: Fichier CV non trouvé : {cv_path}")
            return False
        cv_input = driver.find_element(By.ID, "cv")
        cv_input.send_keys(os.path.abspath(cv_path))
        print(f"- CV uploadé : {cv_path}")

        if lm_path and os.path.exists(lm_path):
            lm_input = driver.find_element(By.ID, "lm")
            lm_input.send_keys(os.path.abspath(lm_path))
            print(f"- Lettre de motivation uploadée : {lm_path}")
        else:
            print("- Pas de lettre de motivation fournie.")

        print("\n✅ Formulaire rempli.")
        print("\nℹ️ La candidature n'a PAS été envoyée. Pour l'activer, décommentez le code de soumission.")
        return True

    except Exception as e:
        print(f"❌ Erreur lors du remplissage du formulaire : {e}")
        return False

def main():
    """Fonction principale pour orchestrer le scraping."""
    db = UserDatabase()
    try:
        print(f"🔍 Recherche de l'utilisateur : {USER_EMAIL}")
        user_data = db.get_user_by_email(USER_EMAIL)
        
        if not user_data:
            print(f"❌ ERREUR: Aucun utilisateur trouvé avec l'email {USER_EMAIL}.")
            return

        first_name = user_data.get('first_name')
        last_name = user_data.get('last_name')
        cv_path = user_data.get('cv_path')
        lm_path = user_data.get('lm_path')

        if not all([first_name, last_name, cv_path]):
            print(f"❌ ERREUR: Données manquantes pour {USER_EMAIL}. Prénom, nom et CV sont requis.")
            return
        
        print(f"✅ Utilisateur trouvé : {first_name} {last_name}")
    finally:
        db.close()

    driver = initialiser_driver()
    if not driver:
        return

    try:
        driver.get(URL_ACCUEIL)
        gerer_cookies(driver)
        
        if rechercher_offres(driver, "stage informatique", "Toute la France"):
            if cliquer_premiere_offre(driver):
                if remplir_formulaire_candidature(driver, USER_EMAIL, first_name, last_name, cv_path, lm_path):
                    print("\n🎉 Processus de candidature terminé !")
                else:
                    print("\n❌ Échec du remplissage du formulaire.")
            else:
                print("\n❌ Échec du clic sur l'offre.")
        else:
            print("\n❌ Échec de la recherche.")

        print("\n👀 Le navigateur restera ouvert 10 secondes.")
        time.sleep(10)

    except Exception as e:
        print(f"❌ Une erreur majeure est survenue : {e}")
    finally:
        if driver:
            print("🚪 Fermeture du navigateur.")
            driver.quit()

if __name__ == "__main__":
    main()
