"""
Script d'automatisation de candidatures France Travail
Auteur: Assistant
Version: Réorganisée
"""

# ===== IMPORTS =====
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException, NoSuchElementException
import time
import random
import os
import csv
from datetime import datetime
from dotenv import load_dotenv

# ===== CONFIGURATION =====
# Le chemin du fichier de log reste une constante globale.
LOG_FILE = "dossier_pole_emploi/candidatures_france_travail.csv"

# ===== INITIALISATION =====
# Le driver est maintenant initialisé dans la fonction lancer_scraping
# pour garantir qu'il est propre à chaque exécution.
# On le déclare en global pour que les fonctions helper puissent l'utiliser.
driver = None

# ===== FONCTIONS UTILITAIRES =====

def attendre_delai_aleatoire(min_seconds=2, max_seconds=5):
    """Attendre un délai aléatoire entre min_seconds et max_seconds."""
    delai = random.uniform(min_seconds, max_seconds)
    print(f"⏳ Attente de {delai:.2f} secondes...")
    time.sleep(delai)

def remplir_champ(element, texte):
    """Remplir un champ avec un délai aléatoire entre chaque caractère."""
    element.clear()
    for caractere in texte:
        element.send_keys(caractere)
        time.sleep(random.uniform(0.05, 0.2))

def log_candidature(offre_url, offre_id=None, offre_titre=None):
    """Enregistrer une candidature dans le fichier de log"""
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Créer le fichier s'il n'existe pas
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "ID de l'offre", "Titre de l'offre", "URL de l'offre"])
    
    # Ajouter la candidature au fichier
    with open(LOG_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([today, offre_id or "", offre_titre or "", offre_url])
    
    print(f"✅ Candidature enregistrée dans le fichier {LOG_FILE}")

# ===== GESTION DES COOKIES ET CONNEXION =====

def gerer_cookies():
    """Gère la bannière de cookies en accédant au Shadow DOM."""
    print("🍪 Tentative de gestion de la bannière de cookies (Shadow DOM)...")
    
    try:
        attendre_delai_aleatoire(3, 5)
        
        script = """
        // Trouver l'élément pe-cookies
        const peCookiesElement = document.querySelector('pe-cookies');
        if (!peCookiesElement) return false;
        
        // Accéder au shadow root
        const shadowRoot = peCookiesElement.shadowRoot;
        if (!shadowRoot) return false;
        
        // Trouver le bouton dans le shadow DOM
        const continueButton = shadowRoot.querySelector('#pecookies-continue-btn');
        if (!continueButton) return false;
        
        // Cliquer sur le bouton
        continueButton.click();
        return true;
        """
        
        result = driver.execute_script(script)
        
        if result:
            print("✅ Clic sur le bouton 'Continuer sans accepter' réussi.")
            attendre_delai_aleatoire(2, 3)
            return True
        else:
            print("⚠️  Bouton 'Continuer sans accepter' non trouvé dans le Shadow DOM.")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la gestion des cookies: {e}")
        return False

def etape_saisie_identifiant(identifiant):
    """Saisir l'identifiant et cliquer sur Poursuivre."""
    try:
        print("🔍 Attente du champ identifiant...")
        identifiant_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "identifiant"))
        )
        print("✅ Champ identifiant trouvé.")
        
        remplir_champ(identifiant_field, identifiant)
        
        poursuivre_button = driver.find_element(By.ID, "submit")
        poursuivre_button.click()
        
        attendre_delai_aleatoire(2, 4)
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la saisie de l'identifiant: {e}")
        return False

def etape_saisie_password(password):
    """Saisir le mot de passe et cliquer sur Se connecter."""
    try:
        print("🔍 Attente du champ mot de passe...")
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        print("✅ Champ mot de passe trouvé.")
        remplir_champ(password_field, password)
        
        submit_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "submit"))
        )
        submit_button.click()
        
        attendre_delai_aleatoire(3, 5)
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la saisie du mot de passe: {e}")
        return False

def connexion_france_travail(identifiant, password):
    """Se connecter au site France Travail"""
    print("🔐 Tentative de connexion à France Travail...")
    
    # URL de connexion
    url_connexion = "https://authentification-candidat.francetravail.fr/connexion/XUI/?realm=/individu&goto=https://authentification-candidat.francetravail.fr/connexion/oauth2/realms/root/realms/individu/authorize?realm%3D/individu%26response_type%3Did_token%2520token%2520scope%3Dactu%2520actuStatut%2520application_USG_PN073-tdbcandidat_6408B42F17FC872440D4FF01BA6BAB16999CD903772C528808D1E6FA2B585CF2%2520compteUsager%2520contexteAuthentification%2520coordonnees%2520courrier%2520email%2520etatcivil%2520idIdentiteExterne%2520idRci%2520individu%2520logW%2520messagerieintegree%2520navigation%2520nomenclature%2520notifications%2520openid%2520pilote%2520pole_emploi%2520prdvl%2520profile%2520reclamation%2520suggestions%2520mesrdvs%26client_id%3DUSG_PN073-tdbcandidat_6408B42F17FC872440D4FF01BA6BAB16999CD903772C528808D1E6FA2B585CF2%26state%3Dkk6ywfeBSqE6u5Mu%26nonce%3DIjrKFxkMGDHZS0Pb%26redirect_uri%3Dhttps://candidat.francetravail.fr/espacepersonnel/#login/"
    
    print("ℹ️  Chargement de la page de connexion...")
    try:
        driver.get(url_connexion)
        print("✅ Page de connexion chargée.")
    except Exception as e:
        print(f"❌ Le chargement de la page a échoué (timeout ou autre erreur) : {e}")
        return False
    gerer_cookies()
    
    if not etape_saisie_identifiant(identifiant):
        return False
    
    if not etape_saisie_password(password):
        return False
    
    # Vérifier si la connexion a réussi
    if "espacepersonnel" in driver.current_url:
        print("✅ Connexion réussie à France Travail !")
        return True
    else:
        print(f"❌ La connexion semble avoir échoué. URL actuelle: {driver.current_url}")
        return False

# ===== RECHERCHE D'OFFRES =====

def saisir_mots_cles(mots_cles):
    """Saisir les mots-clés dans le champ de recherche."""
    try:
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        print(f"🔍 Saisie des mots-clés : {mots_cles}")
        wait = WebDriverWait(driver, 15) # Attendre jusqu'à 15 secondes
        mots_cles_field = wait.until(EC.presence_of_element_located((By.ID, "saisie-offre-search-selectized")))
        remplir_champ(mots_cles_field, mots_cles)
        attendre_delai_aleatoire(1, 2)
        return mots_cles_field
    except Exception as e:
        print(f"❌ Erreur lors de la saisie des mots-clés: {e}")
        return None

def saisir_localisation(localisation):
    """Saisir la localisation et gérer les suggestions."""
    if not localisation:
        return True
        
    try:
        print(f"📍 Saisie du lieu de travail : {localisation}")
        localisation_field = driver.find_element(By.ID, "lieu-travail-search-selectized")
        remplir_champ(localisation_field, localisation)
        attendre_delai_aleatoire(1, 2)
        
        # Attendre que des suggestions apparaissent
        attendre_delai_aleatoire(2, 3)
        
        # Tenter de sélectionner la première suggestion
        try:
            suggestion = driver.find_element(By.CSS_SELECTOR, ".selectize-dropdown-content .option")
            suggestion.click()
            print("✅ Suggestion de localisation sélectionnée.")
        except:
            print("⚠️ Pas de suggestion de localisation trouvée ou erreur lors de la sélection.")
            localisation_field.send_keys(Keys.TAB)
            
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la saisie de la localisation: {e}")
        return False

def lancer_recherche(mots_cles_field):
    """Lancer la recherche d'offres."""
    try:
        print("🚀 Lancement de la recherche...")
        try:
            search_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button.search-button")
            search_button.click()
            print("✅ Recherche lancée via bouton.")
        except:
            mots_cles_field.send_keys(Keys.RETURN)
            print("✅ Recherche lancée via touche Entrée.")
        
        attendre_delai_aleatoire(5, 8)
        return True
    except Exception as e:
        print(f"❌ Erreur lors du lancement de la recherche: {e}")
        return False

def rechercher_offres(mots_cles, localisation):
    """Fonction pour rechercher des offres"""
    
    # Saisir le métier/mots-clés
    mots_cles_field = saisir_mots_cles(mots_cles)
    if not mots_cles_field:
        return False
    
    # Saisir le lieu de travail
    if not saisir_localisation(localisation):
        return False
    
    # Lancer la recherche
    if not lancer_recherche(mots_cles_field):
        return False
    
    print(f"✅ Recherche terminée. URL actuelle: {driver.current_url}")
    return True

# ===== GESTION DES CANDIDATURES =====

def est_deja_postule():
    """Déterminer si l'offre a déjà fait l'objet d'une candidature."""
    try:
        indicateurs = [
            "Vous avez déjà postulé à cette offre",
            "Candidature déjà envoyée",
            "Candidature envoyée le",
            "Votre candidature a été enregistrée"
        ]
        
        page_source = driver.page_source
        for indicateur in indicateurs:
            if indicateur in page_source:
                print(f"ℹ️  Détecté : '{indicateur}' - Offre déjà postulée.")
                return True
        
        # Chercher un élément spécifique indiquant une candidature existante
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, ".candidature-envoyee, .already-applied, .msg-candidature-envoyee")
            if elements:
                print("ℹ️  Élément indiquant une candidature existante trouvé.")
                return True
        except:
            pass
            
        # Vérifier si le bouton postuler est désactivé
        try:
            postuler_button = driver.find_element(By.ID, "detail-apply")
            if postuler_button.get_attribute("disabled") or "Déjà postulé" in postuler_button.text:
                print("ℹ️  Bouton 'Postuler' désactivé ou indiquant 'Déjà postulé'.")
                return True
        except:
            pass
            
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification si déjà postulé: {e}")
        return False

def est_redirection_externe():
    """Vérifie de manière robuste si la candidature est une redirection externe."""
    try:
        # Attente courte pour ne pas ralentir si le menu n'existe pas
        wait = WebDriverWait(driver, 2)
        dropdown_menu = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".dropdown-menu.show")))
        
        titre_element = dropdown_menu.find_element(By.CSS_SELECTOR, ".dropdown-apply-title")
        is_external = "sur le site de l'entreprise" in titre_element.text.lower()
        
        if is_external:
            print("↪️  Détection d'une redirection externe.")
            driver.find_element(By.TAG_NAME, 'body').click() # Fermer le menu
            return True
        else:
            # Le menu existe mais n'indique pas de redirection
            return False
            
    except (NoSuchElementException, TimeoutException):
        # Comportement normal si le menu n'est pas trouvé : ce n'est pas une redirection.
        return False
    except Exception as e:
        # Sécurité pour toute autre erreur inattendue
        print(f"⚠️ Erreur inattendue dans est_redirection_externe: {e}")
        return False

def selectionner_cv():
    """Sélectionner le premier CV disponible."""
    try:
        print("📝 Recherche des CV disponibles...")
        attendre_delai_aleatoire(3, 5)
        
        selectors = [
            "input[type='radio'][name='choix-cv']",
            "input[type='radio'][name='selectedCvId']",
            "input[type='radio']"
        ]
        
        radios_cv = None
        for selector in selectors:
            radios_cv = driver.find_elements(By.CSS_SELECTOR, selector)
            if radios_cv and len(radios_cv) > 0:
                print(f"ℹ️  CV trouvés avec le sélecteur : {selector}")
                break
        
        if not (radios_cv and len(radios_cv) > 0):
            print("⚠️  Aucun CV disponible à sélectionner.")
            return False
            
        print(f"ℹ️  Nombre de CV disponibles : {len(radios_cv)}")
        print("➡️ Sélection du premier CV...")
        
        try:
            radios_cv[0].click()
            print("✅ Clic sur le premier CV réussi.")
        except Exception as e:
            print(f"⚠️  Erreur lors du clic direct : {e}")
            try:
                driver.execute_script("arguments[0].click();", radios_cv[0])
                print("✅ Clic sur le premier CV via JavaScript réussi.")
            except Exception as e:
                print(f"❌ Erreur lors du clic via JavaScript : {e}")
                return False
        
        attendre_delai_aleatoire(1, 2)
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la sélection du CV: {e}")
        return False

def cocher_confirmation():
    """Cocher la case de confirmation des coordonnées."""
    try:
        print("📝 Recherche de la case à cocher de confirmation...")
        checkbox_selectors = [
            "input[type='checkbox'][id='confirmcoordonnees']",
            "input[type='checkbox'][name='confirmcoordonnees']",
            "input[type='checkbox'][required]"
        ]
        
        checkbox = None
        for selector in checkbox_selectors:
            checkbox_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if checkbox_elements:
                checkbox = checkbox_elements[0]
                print(f"ℹ️  Case à cocher trouvée avec le sélecteur : {selector}")
                break
                
        if not checkbox:
            print("⚠️  Case à cocher de confirmation non trouvée.")
            return False
        
        print("➡️ Coche de la case de confirmation...")
        
        try:
            checkbox.click()
            print("✅ Clic sur la case à cocher réussi.")
        except Exception as e:
            print(f"⚠️  Erreur lors du clic direct sur la case à cocher : {e}")
            try:
                driver.execute_script("arguments[0].click();", checkbox)
                print("✅ Clic sur la case à cocher via JavaScript réussi.")
            except Exception as e:
                print(f"❌ Erreur lors du clic sur la case à cocher via JavaScript : {e}")
                return False
        
        attendre_delai_aleatoire(1, 2)
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la coche de confirmation: {e}")
        return False

def cliquer_envoyer():
    """Cliquer sur le bouton Envoyer."""
    try:
        print("🔍 Recherche du bouton 'Envoyer'...")
        
        bouton_selectors = [
            "button[type='submit']",
            "button.btn-primary",
            ".btn.btn-primary"
        ]
        
        bouton_envoyer = None
        for selector in bouton_selectors:
            boutons = driver.find_elements(By.CSS_SELECTOR, selector)
            if boutons:
                bouton_envoyer = boutons[0]
                print(f"ℹ️  Bouton 'Envoyer' trouvé avec le sélecteur : {selector}")
                break
        
        if not bouton_envoyer:
            print("⚠️  Bouton 'Envoyer' non trouvé.")
            return False
        
        print("➡️ Clic sur le bouton 'Envoyer'...")
        
        try:
            bouton_envoyer.click()
            print("✅ Clic sur le bouton 'Envoyer' réussi.")
        except Exception as e:
            print(f"⚠️  Erreur lors du clic direct sur le bouton 'Envoyer' : {e}")
            try:
                driver.execute_script("arguments[0].click();", bouton_envoyer)
                print("✅ Clic sur le bouton 'Envoyer' via JavaScript réussi.")
            except Exception as e:
                print(f"❌ Erreur lors du clic sur le bouton 'Envoyer' via JavaScript : {e}")
                return False
        
        attendre_delai_aleatoire(3, 5)
        print("🎉 Candidature envoyée avec succès !")
        return True
    except Exception as e:
        print(f"❌ Erreur lors du clic sur 'Envoyer': {e}")
        return False

def completer_candidature(offre_id, titre_offre):
    """Compléter le formulaire de candidature."""
    print("📝 Complétion du formulaire de candidature...")
    
    try:
        if "candidature/postulerenligne" not in driver.current_url:
            print(f"❌ URL non reconnue comme une page de candidature : {driver.current_url}")
            return False
            
        print(f"✅ Page de candidature chargée. URL : {driver.current_url}")
        
        # Sélectionner le CV
        if not selectionner_cv():
            return False
            
        # Cocher la case de confirmation
        if not cocher_confirmation():
            return False
            
        # Cliquer sur le bouton "Envoyer"
        if not cliquer_envoyer():
            return False
            
        # Enregistrer la candidature après succès
        log_candidature(driver.current_url, offre_id, titre_offre)
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la complétion de la candidature: {e}")
        return False

def cliquer_envoyer_candidature():
    """Cliquer sur le bouton 'Envoyer ma candidature' de manière robuste."""
    try:
        print("🔍 Recherche du bouton 'Envoyer ma candidature'...")
        wait = WebDriverWait(driver, 10)
        # Utiliser XPath pour trouver le bouton par son texte, de manière plus flexible
        envoyer_candidature = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Envoyer ma candidature')] | //button[contains(., 'Envoyer ma candidature')]"))
        )
        envoyer_candidature.click()
        attendre_delai_aleatoire(3, 5)
        return True
    except Exception as e:
        print(f"❌ Erreur lors du clic sur 'Envoyer ma candidature': {e}")
        return False

def gerer_onglet_candidature(offre_id, offre_titre):
    """Gérer l'onglet de candidature et retourner un statut."""
    original_window = driver.current_window_handle
    nouvel_onglet = len(driver.window_handles) > 1

    try:
        if nouvel_onglet:
            driver.switch_to.window(driver.window_handles[-1])

        # AJOUT : Attente explicite pour le message 'déjà postulé'
        try:
            wait = WebDriverWait(driver, 5) # Attendre jusqu'à 5 secondes
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Vous avez déjà postulé sur cette offre')]")))
            print("👍 Offre déjà postulée (détecté avec attente explicite).")
            return "deja_postule"
        except TimeoutException:
            # Le message n'est pas apparu, on considère que c'est une nouvelle candidature.
            print("❔ Message 'déjà postulé' non trouvé, tentative de nouvelle candidature...")

        # Le reste de la logique pour une nouvelle candidature
        if completer_candidature(offre_id, offre_titre):
            return 'succes_direct'
        else:
            print("❌ La candidature n'a pas pu être complétée.")
            return "echec"

    except Exception as e:
        print(f"❌ Erreur lors de la gestion de l'onglet: {e}")
        return "echec"
    finally:
        if nouvel_onglet:
            print("⏳ Fermeture de l'onglet de candidature...")
            driver.close()
            driver.switch_to.window(original_window)

def traiter_offre():
    """Traiter une offre d'emploi."""
    try:
        # Attendre que le titre de l'offre soit visible
        wait = WebDriverWait(driver, 10)
        titre_element = wait.until(EC.visibility_of_element_located((By.ID, "labelPopinDetailsOffre")))
        titre_offre = titre_element.text.strip()
        print(f"\n\n📄 Traitement de l'offre : {titre_offre}")
        
        # Obtenir l'ID de l'offre si disponible
        offre_id = None
        try:
            li_element = driver.find_element(By.CSS_SELECTOR, "li.selected[data-id-offre]")
            offre_id = li_element.get_attribute("data-id-offre")
            print(f"ℹ️  ID de l'offre : {offre_id}")
        except:
            pass
        
        # Cliquer sur le bouton "Postuler"
        print("🔍 Recherche du bouton de candidature...")
        postuler_button = driver.find_element(By.ID, "detail-apply")
        
        print("➡️ Clic sur le bouton 'Postuler'...")
        driver.execute_script("arguments[0].click();", postuler_button)
        attendre_delai_aleatoire(2, 3)
        
        # Vérifier si c'est une redirection externe
        if est_redirection_externe():
            return "redirection_externe"

        # Vérifier si l'offre a déjà fait l'objet d'une candidature
        if est_deja_postule():
            return "deja_postule"
        
        # Cliquer sur "Envoyer ma candidature"
        if not cliquer_envoyer_candidature():
            return "echec_direct"
            
        # Gérer l'onglet de candidature
        statut_candidature = gerer_onglet_candidature(offre_id, titre_offre)
        if statut_candidature == "succes":
            return "succes_direct"
        elif statut_candidature == "deja_postule":
            return "deja_postule"
        else: # "echec"
            return "echec_direct"
            
    except Exception as e:
        print(f"❌ Erreur lors du traitement de l'offre: {e}")
        return "erreur"

def passer_offre_suivante():
    """Passer à l'offre suivante."""
    try:
        print("➡️ Clic sur le bouton 'Suivant'...")
        next_button = driver.find_element(By.CSS_SELECTOR, "button.btn-nav.next")
        
        # Vérifier si le bouton est désactivé
        if next_button.get_attribute("disabled"):
            print("🛑 Bouton 'Suivant' désactivé. Fin de la navigation.")
            return False
        
        next_button.click()
        attendre_delai_aleatoire(3, 5)
        return True
    except Exception as e:
        print(f"❌ Erreur lors du clic sur le bouton 'Suivant': {e}")
        return False

def lancer_scraping(identifiant, mot_de_passe, mots_cles, localisation, headless=True):
    """
    Lance le processus de scraping en streamant les logs en temps réel.
    """
    global driver
    import json

    yield "🚀 Initialisation du scraper..."
    
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    try:
        yield f"🚀 Lancement du processus pour '{mots_cles}' à '{localisation}'..."
        
        if not connexion_france_travail(identifiant, mot_de_passe):
            yield "❌ Échec de la connexion, arrêt du processus."
            return

        yield "✅ Connexion réussie. Navigation vers la page de recherche..."
        driver.get("https://candidat.francetravail.fr/rechercheoffre/landing")
        attendre_delai_aleatoire(3, 5)
        
        yield "🔍 Recherche des offres en cours..."
        rechercher_offres(mots_cles, localisation)
        
        offres_elements = driver.find_elements(By.CSS_SELECTOR, "li[data-id-offre]")
        
        if not offres_elements:
            yield "ℹ️  Aucune offre trouvée."
            return
        
        nombre_offres = len(offres_elements)
        yield f"TOTAL_OFFERS:{nombre_offres}"
        yield f"📊 {nombre_offres} offres trouvées. Début du traitement..."
        
        premiere_offre = offres_elements[0]
        premiere_offre.find_element(By.ID, "pagelink").click()
        attendre_delai_aleatoire(3, 5)
        
        offres_traitees = 0
        candidatures_reussies = 0
        deja_postule_count = 0
        redirections_externes_count = 0
        offres_directes_count = 0

        while True:
            resultat = traiter_offre()
            
            offres_traitees += 1
            yield f"PROGRESS:{offres_traitees}"
            if resultat == "succes_direct":
                candidatures_reussies += 1
                offres_directes_count += 1
            elif resultat == "echec_direct":
                offres_directes_count += 1
            elif resultat == "deja_postule":
                deja_postule_count += 1
            elif resultat == "redirection_externe":
                redirections_externes_count += 1
            
            if offres_traitees >= 10:
                yield "\n🛑 Limite de 10 offres atteinte pour le test."
                break

            if not passer_offre_suivante():
                break
        
        resume = {
            "offres_traitees": offres_traitees,
            "candidatures_reussies": candidatures_reussies,
            "offres_directes": offres_directes_count,
            "redirections_externes": redirections_externes_count,
            "deja_postule": deja_postule_count
        }
        yield f"FIN:{json.dumps(resume)}"

    except Exception as e:
        yield f"❌ Erreur générale inattendue: {e}"
    finally:
        yield "🛑 Fermeture du navigateur..."
        if driver:
            time.sleep(2)
            driver.quit()

# ===== EXÉCUTION (pour test direct du script) =====

if __name__ == "__main__":
    load_dotenv()
    TEST_EMAIL = os.getenv("FRANCE_TRAVAIL_TEST_EMAIL")
    TEST_PASSWORD = os.getenv("FRANCE_TRAVAIL_TEST_PASSWORD")
    TEST_MOTS_CLES = "serveur"
    TEST_LOCALISATION = "Paris"

    if not TEST_EMAIL or not TEST_PASSWORD:
        print("ERREUR: Veuillez définir FRANCE_TRAVAIL_TEST_EMAIL et FRANCE_TRAVAIL_TEST_PASSWORD dans votre fichier .env")
        exit()
    
    print("--- Lancement du scraper en mode test ---")
    scraper_generator = lancer_scraping(
        identifiant=TEST_EMAIL,
        mot_de_passe=TEST_PASSWORD,
        mots_cles=TEST_MOTS_CLES,
        localisation=TEST_LOCALISATION,
        headless=False
    )
    
    for message in scraper_generator:
        # En mode test, on ne traite pas le préfixe 'FIN:'
        print(message)
