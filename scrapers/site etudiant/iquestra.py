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

def filtrer_par_contrat(driver, contract_type_text):
    """Sélectionne le type de contrat et relance la recherche."""
    print(f"\n📄 Filtrage par type de contrat : '{contract_type_text}'...")
    try:
        # Utiliser l'ID 'selectContract' fourni par l'utilisateur
        select_contract_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "selectContract"))
        )
        select_object = Select(select_contract_element)
        select_object.select_by_visible_text(contract_type_text)
        print(f"✅ Contrat '{contract_type_text}' sélectionné.")

        # Le formulaire a l'ID 'offerFormSearch', on clique sur le bouton submit dedans
        form = driver.find_element(By.ID, "offerFormSearch")
        bouton_rechercher = form.find_element(By.CSS_SELECTOR, "button[type='submit']")
        bouton_rechercher.click()
        print("✅ Filtres appliqués.")
        # Attendre que la page se recharge avec les résultats filtrés
        WebDriverWait(driver, 10).until(EC.staleness_of(bouton_rechercher))
        return True
    except Exception as e:
        print(f"❌ Erreur lors du filtrage par contrat : {e}")
        return False

def cliquer_premiere_offre(driver):
    """Clique sur la première offre dans les résultats."""
    print("\n📄 Analyse de la page de résultats après filtrage...")
    try:
        # Nouveau sélecteur basé sur l'analyse du fichier iquesta_results_debug.html.
        # Les liens des offres semblent avoir la classe 'fw-bold' après filtrage.
        premier_lien = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.fw-bold"))
        )
        print("✅ Première offre trouvée. Clic en cours...")
        driver.execute_script("arguments[0].click();", premier_lien)
        return True
    except Exception as e:
        print(f"❌ Erreur lors du clic sur la première offre. Le sélecteur 'a.fw-bold' est probablement obsolète ou non unique.")
        print("💾 Sauvegarde du HTML de la page de résultats dans 'iquesta_results_debug.html' pour analyse...")
        with open("iquesta_results_debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("💡 Ouvrez ce fichier et cherchez le lien de la première offre pour trouver le bon sélecteur CSS.")
        return False

def remplir_formulaire_candidature(driver, user_data):
    """Remplit le formulaire de candidature."""
    print("\n📝 Remplissage du formulaire de candidature...")
    try:
        # La page de l'offre se charge dans le même onglet, il n'est donc pas nécessaire de basculer.
        print("- Page du formulaire de candidature atteinte.")

        # Remplir les champs du formulaire en utilisant les sélecteurs trouvés
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

    try:
        driver = initialiser_driver()
        db = UserDatabase()
        user_data = db.get_user_by_email(USER_EMAIL)
        db.close()

        if not user_data:
            return

        first_name = user_data['first_name']
        last_name = user_data['last_name']
        cv_path = user_data.get('cv_path')
        lm_path = user_data.get('lm_path')

        if not all([cv_path, lm_path]):
            print("❌ CV ou lettre de motivation manquant pour l'utilisateur.")
            return

        driver.get("https://www.iquesta.com/")
        gerer_cookies(driver)
        
        # Récupérer les préférences de recherche de l'utilisateur
        search_query = user_data.get('search_query')
        location = user_data.get('location')
        contract_type = user_data.get('contract_type')

        # Utiliser des valeurs par défaut si non spécifiées et informer l'utilisateur
        if not search_query:
            search_query = "stage informatique" # Valeur par défaut
            print(f"INFO: Pas de poste recherché spécifié, utilisation de la valeur par défaut : '{search_query}'")
        if not location:
            location = "Toute la France" # Valeur par défaut
            print(f"INFO: Pas de localisation spécifiée, utilisation de la valeur par défaut : '{location}'")

        # Lancer la recherche avec les paramètres de l'utilisateur
        if rechercher_offres(driver, metier=search_query, region=location):
            # Filtrer par type de contrat uniquement s'il est spécifié
            should_proceed = False
            if contract_type:
                if filtrer_par_contrat(driver, contract_type):
                    should_proceed = True
            else:
                print("INFO: Pas de type de contrat spécifié, le filtre ne sera pas appliqué.")
                should_proceed = True # Continuer sans filtrer

            if should_proceed:
                # Cliquer sur la première offre
                if cliquer_premiere_offre(driver):
                    # Remplir le formulaire
                    if remplir_formulaire_candidature(driver, user_data):
                        print("\n🎉 Processus de candidature terminé !")
                    else:
                        print("\n❌ Échec de la soumission de la candidature.")
                else:
                    print("❌ Échec du clic sur l'offre après filtrage.")
            else:
                print("❌ Échec du filtrage par contrat.")
        else:
            print("❌ Échec de la recherche initiale.")

    finally:
        if 'driver' in locals() and driver:
            print(f"\n👀 Le navigateur restera ouvert {PAUSE_DURATION} secondes.")
            time.sleep(PAUSE_DURATION)
            print("🚪 Fermeture du navigateur.")
            driver.quit()

if __name__ == "__main__":
    main()
