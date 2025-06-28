import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# --- CONFIGURATION (chargée depuis le fichier .env) ---
MON_EMAIL = os.getenv("IQUESTA_EMAIL")
MON_PRENOM = os.getenv("IQUESTA_PRENOM")
MON_NOM = os.getenv("IQUESTA_NOM")
MON_MESSAGE = os.getenv("IQUESTA_MESSAGE", "Bonjour, vivement intéressé par cette opportunité, je vous soumets ma candidature.")
CHEMIN_CV = os.getenv("IQUESTA_CV_PATH")
CHEMIN_LM = os.getenv("IQUESTA_LM_PATH")
# -----------------------------------------------------

# Vérification des variables d'environnement essentielles
if not all([MON_EMAIL, MON_PRENOM, MON_NOM, CHEMIN_CV]):
    print("❌ ERREUR: Des informations de configuration sont manquantes dans votre fichier .env.")
    print("Veuillez créer un fichier .env à la racine du projet et y définir :")
    print("IQUESTA_EMAIL, IQUESTA_PRENOM, IQUESTA_NOM, IQUESTA_CV_PATH")
    sys.exit(1) # Arrête le script si la configuration est incomplète

URL_ACCUEIL = "https://www.iquesta.com/"

def initialiser_driver():
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
    print("🍪 Tentative de gestion des cookies...")
    try:
        bouton_cookies = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
        )
        bouton_cookies.click()
        print("✅ Cookies acceptés.")
        time.sleep(1)
    except TimeoutException:
        print("ℹ️  Pas de bannière de cookies détectée, ou déjà acceptée.")
    except Exception as e:
        print(f"❌ Erreur lors de la gestion des cookies: {e}")

def rechercher_offres(driver, metier, region):
    print(f"\n🔍 Lancement de la recherche pour '{metier}' en '{region}'...")
    try:
        champ_metier = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "controlTerm")))
        champ_metier.send_keys(metier)
        print(f"- Champ métier rempli : '{metier}'")

        dropdown_region = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "selectRegion")))
        dropdown_region.click()
        
        option_xpath = f"//select[@id='selectRegion']/option[normalize-space()='{region}']"
        option_region = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, option_xpath)))
        option_region.click()
        print(f"- Région sélectionnée : '{region}'")

        bouton_rechercher = driver.find_element(By.XPATH, "//form[contains(@class, 'container')]//button[@type='submit']")
        bouton_rechercher.click()
        print("✅ Recherche lancée !")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la recherche : {e}")
        return False

def cliquer_premiere_offre(driver):
    print("\n📄 Analyse de la page de résultats...")
    try:
        resultats_container_xpath = "//div[@class='list-offer']"
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, resultats_container_xpath)))
        print("- Conteneur des résultats trouvé.")

        offres_xpath = "//div[contains(@class, 'offer-summary')]//h2/a[@href]"
        offres = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, offres_xpath)))
        
        if offres:
            print(f"✅ {len(offres)} offres trouvées. Clic sur la première.")
            premiere_offre = offres[0]
            driver.execute_script("arguments[0].click();", premiere_offre)
            return True
        else:
            print("⚠️ Aucune offre trouvée sur la page.")
            return False
    except Exception as e:
        print(f"❌ Erreur lors du clic sur la première offre : {e}")
        return False

def remplir_formulaire_candidature(driver):
    print("\n📝 Remplissage du formulaire de candidature...")
    try:
        form_xpath = "//form[@id='application-form']"
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, form_xpath)))
        print("- Formulaire trouvé.")

        driver.find_element(By.NAME, "email").send_keys(MON_EMAIL)
        driver.find_element(By.NAME, "firstName").send_keys(MON_PRENOM)
        driver.find_element(By.NAME, "lastName").send_keys(MON_NOM)
        driver.find_element(By.NAME, "message").send_keys(MON_MESSAGE)
        print("- Champs texte remplis.")

        if not os.path.exists(CHEMIN_CV):
            print(f"❌ ERREUR: Le fichier CV n'a pas été trouvé à l'emplacement : {CHEMIN_CV}")
            print("Veuillez vérifier le chemin dans la variable IQUESTA_CV_PATH de votre fichier .env.")
            return False

        cv_input = driver.find_element(By.NAME, "cv")
        cv_input.send_keys(CHEMIN_CV)
        print(f"- CV uploadé depuis : {CHEMIN_CV}")

        if CHEMIN_LM and os.path.exists(CHEMIN_LM):
            lm_input = driver.find_element(By.NAME, "lm")
            lm_input.send_keys(CHEMIN_LM)
            print(f"- Lettre de motivation uploadée depuis : {CHEMIN_LM}")
        else:
            print("- Pas de lettre de motivation fournie ou fichier non trouvé.")

        print("\n✅ Formulaire rempli.")
        bouton_postuler = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Postuler']")
        print("- Bouton 'Postuler' localisé.")

        # --- DÉCOMMENTER POUR ACTIVER LA CANDIDATURE AUTOMATIQUE ---
        # print("\n🚀 SOUMISSION DE LA CANDIDATURE...")
        # bouton_postuler.click()
        # print("🎉 Candidature envoyée avec succès !")
        # ---------------------------------------------------------
        
        print("\nℹ️ La candidature n'a PAS été envoyée. Pour l'activer, décommentez les lignes ci-dessus dans le code.")

        return True

    except Exception as e:
        print(f"❌ Erreur lors du remplissage du formulaire : {e}")
        return False

def main():
    driver = initialiser_driver()
    if not driver:
        return

    try:
        driver.get(URL_ACCUEIL)
        print(f"🌍 Page d'accueil chargée : {URL_ACCUEIL}")
        
        gerer_cookies(driver)
        
        if rechercher_offres(driver, "Développeur", "Ile de France"):
            print("\n🎉 Recherche réussie !")
            time.sleep(2)

            if cliquer_premiere_offre(driver):
                print("\n🎉 Clic sur l'offre réussi !")
                time.sleep(3) # Laisse le temps à la page de l'offre de se charger

                if remplir_formulaire_candidature(driver):
                    print("\n🎉 Troisième étape réussie ! Le formulaire est rempli.")
                else:
                    print("\n❌ Échec du remplissage du formulaire.")

                print("\n👀 Le navigateur restera ouvert pour observation. Fermez-le manuellement.")
                while True:
                    time.sleep(1)
            else:
                print("\n❌ Échec du clic sur l'offre.")
                time.sleep(5)
        else:
            print("\n❌ Échec de la recherche.")
            time.sleep(5)

    except Exception as e:
        print(f"❌ Une erreur majeure est survenue : {e}")
    finally:
        if driver:
            pass

if __name__ == "__main__":
    main()
