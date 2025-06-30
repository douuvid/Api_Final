import logging
import sys
import os
import time
import random
from datetime import datetime

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
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from database.user_database import UserDatabase

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Fonctions robustes de bas niveau (inspirées du code utilisateur) ---

def setup_driver():
    """Configure un driver Chrome robuste sans ouverture automatique des DevTools."""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Désactiver le mode headless pour permettre les interactions visuelles
    options.headless = False
    
    # Simuler un user-agent avec DevTools ouverts
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Chrome-Lighthouse")
    
    # RETRAIT de l'option --auto-open-devtools-for-tabs qui cause des problèmes de fenêtre
    
    # Configurer préférences pour outils de développement (sans les ouvrir automatiquement)
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "devtools.preferences": {"currentDockState": "\"bottom\"", "panel-selectedTab": "\"elements\""},
        "devtools.open_docked": True
    }
    options.add_experimental_option("prefs", prefs)
    
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(120)  # Timeout plus long
        
        logger.info("Driver Chrome créé avec succès")
        return driver
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création du driver: {e}")
        return None

def select_suggestion(driver, wait, timeout=5):
    """Sélectionne la première suggestion dans la liste d'autocomplétion."""
    # Différents sélecteurs possibles pour la liste de suggestions
    suggestion_selectors = [
        # Sélecteurs spécifiques au site alternance.emploi.gouv.fr
        ".suggestions",  # Vérifié sur le site
        ".suggestions-container",
        ".listbox",
        "#ac-metier-item-list",  # ID spécifique pour le champ métier
        "#ac-lieu-item-list",    # ID spécifique pour le champ lieu
        # Sélecteurs génériques
        "div.suggestions", 
        "ul.autosuggest-suggestions",
        ".autocomplete-results", 
        ".autocomplete-items",
        "div[role='listbox']",
        ".modal .dropdown-menu",
        ".dropdown-content"
    ]
    
    # Méthode simple: d'abord essayons juste d'envoyer les touches flèche bas puis Entrée
    # Cette méthode est souvent plus fiable car elle ne dépend pas de la structure DOM
    try:
        logger.info("Tentative avec flèche bas + Entrée pour sélectionner la suggestion...")
        
        # Trouver un champ actif (qui a le focus)
        active_element = driver.switch_to.active_element
        if active_element:
            # Simuler flèche bas pour sélectionner la première suggestion
            active_element.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.7)  # Attendre que la sélection soit effective
            
            # Appuyer sur Entrée pour valider
            active_element.send_keys(Keys.ENTER)
            time.sleep(0.5)
            logger.info("Méthode touches clavier appliquée")
            return True
    except Exception as e:
        logger.warning(f"Méthode clavier échouée: {e}, essai méthodes alternatives")
    
    # Si la méthode simple échoue, essayons les méthodes basées sur le DOM
    try:
        logger.info("Recherche des suggestions via DOM...")
        
        # Essayer chaque sélecteur pour trouver la liste de suggestions
        suggestion_list = None
        for selector in suggestion_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    for element in elements:
                        if element.is_displayed():
                            suggestion_list = element
                            logger.info(f"Liste de suggestions visible trouvée avec le sélecteur: {selector}")
                            break
                if suggestion_list:
                    break
            except:
                continue
                
        if not suggestion_list:
            # Essai avec attente
            for selector in suggestion_selectors:
                try:
                    suggestion_list = WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if suggestion_list.is_displayed():
                        logger.info(f"Liste de suggestions trouvée avec le sélecteur: {selector} après attente")
                        break
                except:
                    continue
        
        if not suggestion_list:
            # Essai avec JavaScript pour détecter les éléments visibles
            js_script = """
            return Array.from(document.querySelectorAll('.suggestions, .suggestions-container, [role="listbox"], .listbox'))
                   .filter(el => el.offsetParent !== null && window.getComputedStyle(el).display !== 'none')
                   .map(el => el.outerHTML);
            """
            suggestions_html = driver.execute_script(js_script)
            if suggestions_html:
                logger.info(f"Suggestions détectées via JavaScript: {len(suggestions_html)} éléments")
                # Essayons une simulation clavier plus directe
                active = driver.switch_to.active_element
                if active:
                    active.send_keys(Keys.ARROW_DOWN)
                    time.sleep(0.5)
                    active.send_keys(Keys.ENTER)
                    return True
            else:
                logger.warning("Aucune liste de suggestions visible détectée par JavaScript")
                return False
                
        # Différents sélecteurs possibles pour les éléments de suggestion
        item_selectors = [
            "li", 
            "div.suggestion-item",
            "[role='option']",
            ".dropdown-item",
            "a",
            "*"  # En dernier recours, tout élément enfant
        ]
        
        # Essayer chaque sélecteur pour les éléments
        suggestions = []
        for selector in item_selectors:
            try:
                items = suggestion_list.find_elements(By.CSS_SELECTOR, selector)
                visible_items = [item for item in items if item.is_displayed()]
                if visible_items:
                    suggestions = visible_items
                    logger.info(f"{len(visible_items)} options visibles trouvées avec le sélecteur: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Erreur avec sélecteur {selector}: {e}")
                continue
        
        if not suggestions:
            logger.warning("Aucune option visible trouvée dans la liste")
            # Derniers recours : flèche bas + Entrée
            active = driver.switch_to.active_element
            if active:
                active.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.5)
                active.send_keys(Keys.ENTER)
                return True
            return False
            
        logger.info(f"{len(suggestions)} suggestions visibles trouvées.")
        
        # Sélectionner le premier élément avec plusieurs méthodes
        first_item = suggestions[0]
        logger.info(f"Sélection de: {first_item.text if first_item.text.strip() else '[texte non visible]'}")
        
        # Méthode 1: JavaScript click avec mise en évidence
        try:
            driver.execute_script("""
                arguments[0].style.border = '2px solid red';
                arguments[0].scrollIntoView({block: 'center'});
                setTimeout(() => arguments[0].click(), 100);
            """, first_item)
            time.sleep(0.8)
            return True
        except Exception as e:
            logger.warning(f"Click JS amélioré échoué: {e}, essai méthode alternative")
            
        # Méthode 2: ActionChains complète (scroll, hover, pause, click)
        try:
            actions = ActionChains(driver)
            actions.move_to_element(first_item)
            actions.pause(0.3)
            actions.click()
            actions.perform()
            time.sleep(0.5)
            return True
        except Exception as e:
            logger.warning(f"ActionChains complète échouée: {e}, essai méthode alternative")
            
        # Méthode 3: Send ENTER key après focus
        try:
            first_item.click()  # D'abord focus
            first_item.send_keys(Keys.ENTER)
            time.sleep(0.5)
            return True
        except Exception as e:
            logger.warning(f"ENTER key après focus échoué: {e}, dernier essai")
            
        # Méthode 4: Simulation complète clavier via élément actif
        try:
            active = driver.switch_to.active_element
            if active:
                active.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.5)
                active.send_keys(Keys.ENTER)
                return True
        except Exception as e:
            logger.warning(f"Simulation clavier finale échouée: {e}")
            return False
            
    except Exception as e:
        logger.warning(f"Erreur lors de la sélection de suggestion: {e}")
        
    # En dernier recours, essayer directement sur les champs
    try:
        for field_id in ['metier', 'lieu']:
            field = driver.find_element(By.ID, field_id)
            if field.is_enabled() and field.is_displayed():
                field.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.5)
                field.send_keys(Keys.ENTER)
                return True
    except:
        pass
        
    return False

def fill_field_with_autocomplete(driver, wait, field_id, value, max_retries=3):
    """Remplit un champ avec autocomplétion dans le modal."""
    logger.info(f"🎡 Remplissage du champ '{field_id}' avec '{value}'")
    
    # Différentes stratégies de sélecteurs pour trouver le champ dans le modal
    selectors = [
        f"#{field_id}",  # ID direct
        f"input[placeholder='Indiquez un métier ou une formation']",  # Par placeholder (comme vu dans la capture)
        ".modal-content input.autocomplete",  # Par structure modale 
        ".modal input[type='text']",  # Tout input text dans un modal
    ]
    
    for attempt in range(max_retries):
        logger.info(f"🔄 Tentative {attempt + 1}/{max_retries} pour le champ '{field_id}'")
        
        # Tenter chaque sélecteur jusqu'à ce qu'un fonctionne
        input_field = None
        for selector in selectors:
            try:
                input_field = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                logger.info(f"Champ trouvé avec le sélecteur: {selector}")
                break
            except:
                continue
        
        if not input_field:
            logger.warning(f"Aucun champ trouvé à la tentative {attempt + 1}")
            continue
            
        try:
            # Cliquer pour activer le champ
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_field)
            driver.execute_script("arguments[0].click();", input_field)
            time.sleep(0.5)
            
            # Effacer le contenu existant
            input_field.clear()
            input_field.send_keys(Keys.CONTROL + "a")
            input_field.send_keys(Keys.DELETE)
            time.sleep(0.2)
            
            # Taper le texte caractère par caractère avec délai aléatoire
            for char in value:
                input_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
                
            # Attendre que les suggestions apparaissent
            time.sleep(1.5)
            
            # Chercher les suggestions avec plusieurs sélecteurs possibles
            if select_suggestion(driver, wait):
                logger.info(f"✅ Valeur '{value}' saisie et suggestion sélectionnée")
                return True
            else:
                # Si pas de suggestion, essayer d'appuyer sur Entrée
                logger.warning("Pas de suggestion trouvée, essai avec la touche Entrée")
                input_field.send_keys(Keys.ENTER)
                time.sleep(1)
                return True
                
        except Exception as e:
            logger.warning(f"Erreur tentative {attempt+1}: {str(e)}")
            
    logger.error(f"❌ Échec du remplissage du champ '{field_id}' après {max_retries} tentatives")
    return False

# --- Processus de scraping principal ---

def run_scraper(user_data):
    logger.info(f"Lancement du scraper pour : {user_data['email']}")
    driver = None
    try:
        # Créer le WebDriver avec ouverture auto des DevTools
        driver = setup_driver()
        if not driver:
            logger.error("Impossible de créer le WebDriver. Arrêt du script.")
            return

        # Configuration de l'attente explicite
        wait = WebDriverWait(driver, 20)
        short_wait = WebDriverWait(driver, 5)

        # Accès à la page
        url = "https://www.alternance.emploi.gouv.fr/recherches-offres-formations"
        logger.info(f"Accès à l'URL : {url}")
        driver.get(url)
        
        # Les DevTools s'ouvrent automatiquement maintenant grâce à notre setup
        logger.info("DevTools devraient maintenant être ouverts automatiquement")
        
        # Pause pour s'assurer que la page est complètement chargée
        time.sleep(3)

        # Gestion des cookies
        try:
            cookie_button = short_wait.until(EC.element_to_be_clickable((By.ID, "tarteaucitronPersonalize2")))
            cookie_button.click()
            logger.info("Bannière de cookies acceptée.")
        except Exception as e:
            logger.warning(f"Bannière de cookies non trouvée ou déjà acceptée: {e}")

        try:
            # Étape 1: Basculement et traitement de l'iframe contenant le formulaire
            # Identifier l'iframe contenant le formulaire
            logger.info("Recherche de l'iframe...")
            iframe = None
            try:
                iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id*='recherche']")))  # L'iframe contenant le mot 'recherche' dans l'ID
                logger.info("Iframe trouvé.")
            except TimeoutException:
                try: 
                    iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
                    logger.info("Iframe trouvé via tag name.")
                except TimeoutException:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    if iframes:
                        iframe = iframes[0]  # Prendre le premier iframe comme fallback
                        logger.info(f"Premier iframe pris par défaut. Total iframes: {len(iframes)}")
                    else:
                        logger.error("Aucun iframe trouvé sur la page")
                        raise Exception("Erreur: Page mal chargée, aucun iframe disponible")

            if not iframe:
                logger.error("Iframe non trouvé malgré les tentatives")
                driver.save_screenshot('no_iframe_error.png')
                with open('page_source_no_iframe.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                raise Exception("Erreur: Iframe contenant le formulaire non trouvé")
            
            # Basculer vers l'iframe
            logger.info("Basculement vers l'iframe...")
            driver.switch_to.frame(iframe)
            logger.info("Basculement vers l'iframe réussi.")
            
            # Pause pour laisser le contenu de l'iframe se charger complètement
            logger.info("Attente du chargement de l'iframe...")
            time.sleep(4)
            
            # Code pour forcer l'affichage du formulaire modal en se basant sur l'inspection manuelle
            logger.info("Tentative d'activation du formulaire par simulation d'inspection...")
            
            # Script JavaScript qui simule exactement ce que fait l'inspection pour révéler le formulaire modal
            reveal_modal_script = """
            (function() {
                console.log('Début de la simulation d\'inspection');
                
                // 1. Simuler les variables globales DevTools
                window.__REACT_DEVTOOLS_GLOBAL_HOOK__ = { 
                    isDisabled: false,
                    supportsFiber: true,
                    renderers: new Map(),
                    inject: function() {},
                    hookNames: new Map(),
                    connected: true
                };
                
                // 2. Forcer l'affichage des éléments cachés dans le modal
                var modalElement = document.querySelector('.fr-modal__body');
                if (modalElement) {
                    console.log('Modal trouvé, force affichage');
                    modalElement.style.display = 'block';
                } else {
                    console.log('Modal non trouvé');
                }
                
                // 3. Créer le formulaire modal s'il n'existe pas
                var formContainer = document.querySelector('.fr-modal__content');
                if (!formContainer) {
                    console.log('Conteneur de formulaire non trouvé - tentative création');
                    // Forcer la réinitialisation des éléments DOM cachés
                    document.body.innerHTML += '<div style="display:none" id="temp-trigger"></div>';
                    document.getElementById('temp-trigger').click();
                }
                
                // 4. Simuler l'état actif des DevTools
                window.devtools = { isOpen: true, orientation: 'vertical' };
                document.__devTools = true;
                
                // 5. Déclencher des événements qui peuvent activer des comportements JavaScript
                document.dispatchEvent(new CustomEvent('devtoolschange', { detail: { isOpen: true } }));
                document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true }));
                
                // 6. Vérifier et révéler les champs du formulaire
                var metierField = document.getElementById('metier');
                var formFields = document.querySelectorAll('input, select, button');
                
                if (metierField) {
                    console.log('Champ métier trouvé, activation...');
                    metierField.style.display = 'block';
                    metierField.style.visibility = 'visible';
                    metierField.focus();
                    
                    // Récupérer l'état actuel du formulaire pour diagnostique
                    return {
                        success: true, 
                        formFound: !!metierField,
                        formFieldsCount: formFields.length,
                        modalVisible: !!modalElement
                    };
                } else {
                    // Retourner information sur le DOM actuel
                    return { 
                        success: false, 
                        formFound: false,
                        bodyContent: document.body.innerHTML.substring(0, 500) + '...',
                        formFields: formFields.length
                    };
                }
            })();
            """
            
            try:
                # Exécuter le script pour révéler le formulaire
                result = driver.execute_script(reveal_modal_script)
                logger.info(f"Résultat de l'activation: {result}")
                
                # Pause pour observer si le formulaire est visible
                time.sleep(2)
                
                # Tenter de trouver et cliquer sur le champ métier
                try:
                    metier_field = driver.find_element(By.ID, "metier")
                    logger.info("Champ métier trouvé! Simulation d'un clic...")
                    driver.execute_script("arguments[0].click();", metier_field)
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f"Champ métier non trouvé après activation: {e}")
            except Exception as e:
                logger.warning(f"Erreur lors de l'activation du formulaire: {e}")
                
                # Pause pour observer le résultat
                time.sleep(2)
                
                # Maintenant, essayons de remplir les champs directement, puisque nous avons activé le formulaire
                logger.info("Tentative de remplissage direct du champ métier...")
                
                try:
                    # Recherche du champ métier via ID
                    metier_field = wait.until(EC.presence_of_element_located((By.ID, "metier")))
                    logger.info("Champ métier trouvé par ID")
                    
                    # Utilisation du script JavaScript pour insérer la valeur et déclencher les événements nécessaires
                    fill_input_script = """
                    (function() {
                        var input = document.getElementById('metier');
                        if (input) {
                            // Mettre le focus et remplir le champ
                            input.focus();
                            input.value = arguments[0];
                            
                            // Déclencher les événements nécessaires pour activer l'autocomplétion
                            input.dispatchEvent(new Event('focus', { bubbles: true }));
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                            
                            return { success: true, value: input.value };
                        }
                        return { success: false, error: 'Champ métier non trouvé' };
                    })();
                    """
                    
                    # Exécution du script avec la valeur du métier
                    result = driver.execute_script(fill_input_script, user_data['search_query'])
                    logger.info(f"Résultat du remplissage du champ métier: {result}")
                    
                    # Attendre que les suggestions apparaissent
                    time.sleep(2)
                    
                    # Sélectionner la première suggestion (via touche flèche bas puis Entrée)
                    select_suggestion_script = """
                    (function() {
                        var input = document.getElementById('metier');
                        if (input) {
                            // Simuler flèche bas pour sélectionner la première suggestion
                            input.dispatchEvent(new KeyboardEvent('keydown', {
                                key: 'ArrowDown',
                                code: 'ArrowDown',
                                keyCode: 40,
                                which: 40,
                                bubbles: true
                            }));
                            
                            // Petite pause
                            setTimeout(function() {
                                // Simuler Entrée pour valider la suggestion
                                input.dispatchEvent(new KeyboardEvent('keydown', {
                                    key: 'Enter',
                                    code: 'Enter',
                                    keyCode: 13,
                                    which: 13,
                                    bubbles: true
                                }));
                            }, 500);
                            
                            return true;
                        }
                        return false;
                    })();
                    """
                    
                    # Attendre que les suggestions apparaissent puis sélectionner
                    time.sleep(1)
                    driver.execute_script(select_suggestion_script)
                    logger.info("Sélection de la suggestion effectuée")
                    time.sleep(2)
                    
                    # Même procédure pour le champ lieu
                    logger.info("Tentative de remplissage du champ lieu...")
                    fill_lieu_script = """
                    (function() {
                        var input = document.getElementById('lieu');
                        if (input) {
                            // Mettre le focus et remplir le champ
                            input.focus();
                            input.value = arguments[0];
                            
                            // Déclencher les événements
                            input.dispatchEvent(new Event('focus', { bubbles: true }));
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                            
                            return { success: true, value: input.value };
                        }
                        return { success: false, error: 'Champ lieu non trouvé' };
                    })();
                    """
                    
                    driver.execute_script(fill_lieu_script, user_data['location'])
                    logger.info("Remplissage du champ lieu effectué")
                    time.sleep(2)
                    
                    # Sélectionner suggestion lieu
                    driver.execute_script(select_suggestion_script.replace('metier', 'lieu'))
                    logger.info("Sélection de la suggestion lieu effectuée")
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Erreur lors du remplissage direct des champs: {e}")
                    # Continuer avec l'approche standard si l'approche directe échoue
                
                # Approche finale: Activation complète du formulaire 
                logger.info("Activation complète du formulaire avec révélation des éléments cachés...")
                
                # Script combiné pour activer tous les éléments du formulaire
                complete_activation_script = """
                (function() {
                    console.log('Début activation complète du formulaire...');
                    
                    // Simuler l'environnement DevTools
                    window.__REACT_DEVTOOLS_GLOBAL_HOOK__ = { 
                        isDisabled: false,
                        supportsFiber: true,
                        renderers: new Map(),
                        inject: function() {},
                        hookNames: new Map(),
                        connected: true
                    };
                    window.devtools = { isOpen: true, orientation: 'vertical' };
                    document.__devTools = true;
                    window.__REDUX_DEVTOOLS_EXTENSION__ = function() { return function() { return arguments[0]; } };
                    
                    // API Chrome DevTools simulée
                    window.chrome = window.chrome || {};
                    window.chrome.devtools = {
                        inspectedWindow: { eval: function() {} },
                        network: { getHAR: function() {} }
                    };
                    
                    // Déclencher des événements d'activation
                    document.dispatchEvent(new CustomEvent('devtoolschange', { detail: { isOpen: true } }));
                    document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true }));
                    document.dispatchEvent(new Event('readystatechange', { bubbles: true }));
                    window.dispatchEvent(new Event('load', { bubbles: true }));
                    
                    // Révéler les éléments cachés du DOM
                    var revealed = 0;
                    document.querySelectorAll('*').forEach(function(el) {
                        if (getComputedStyle(el).display === 'none') {
                            console.log('Révélation élément caché:', el.tagName);
                            el.style.display = el.tagName === 'INPUT' ? 'inline-block' : 'block';
                            el.style.visibility = 'visible';
                            el.style.opacity = '1';
                            revealed++;
                        }
                    });
                    
                    // Traiter spécifiquement les éléments de formulaire
                    var metierField = document.getElementById('metier');
                    var lieuField = document.getElementById('lieu');
                    var formFields = [metierField, lieuField];
                    
                    // Activer et rendre visibles les champs du formulaire
                    formFields.forEach(function(field) {
                        if (field) {
                            field.style.display = 'block';
                            field.style.visibility = 'visible';
                            field.disabled = false;
                            field.setAttribute('data-activated', 'true');
                        }
                    });
                    
                    return { 
                        success: true, 
                        revealed: revealed, 
                        metierFound: !!metierField,
                        lieuFound: !!lieuField,
                        formCount: document.forms.length 
                    };
                })();
                """
                
                try:
                    # Exécuter le script d'activation complète
                    activation_result = driver.execute_script(complete_activation_script)
                    logger.info(f"Résultat de l'activation complète: {activation_result}")
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"Erreur lors de l'activation complète du formulaire: {e}")
                
                # Tentative de remplissage des champs après activation complète
                logger.info("Tentative de remplissage des champs après activation complète...")
                try:
                    # Ne pas remplir les champs ici pour éviter la double saisie
                    # Ces champs seront remplis plus tard dans le flux principal
                    logger.info("Activation du formulaire terminée, les champs seront remplis dans l'étape suivante")
                except Exception as e:
                    logger.error(f"Erreur lors du remplissage après activation complète: {e}")
                    driver.save_screenshot('form_filling_error.png')
                    
                time.sleep(2)
                
                # Pause pour donner le temps au JavaScript de prendre effet
                time.sleep(5)
                
                # Effectuer un clic simulant une interaction humaine pour réveiller le formulaire
                try:
                    # Essayer de trouver un élément visible et cliquer dessus
                    visible_elements = driver.find_elements(By.CSS_SELECTOR, "body *:not(script):not(style):not(meta)")
                    for el in visible_elements[:5]:  # Limiter aux 5 premiers éléments pour éviter de parcourir tout le DOM
                        try:
                            if el.is_displayed():
                                logger.info(f"Clic sur un élément visible: {el.tag_name}")
                                el.click()
                                break
                        except:
                            continue
                except Exception as e:
                    logger.warning(f"Erreur lors de la tentative de clic sur un élément visible: {e}")
                
                # Pause supplémentaire
                time.sleep(3)
                
                # Vérifier si les champs du formulaire sont présents
                try:
                    metier_field = wait.until(EC.presence_of_element_located((By.ID, "metier")))
                    logger.info("✅ Le champ métier est visible.") 
                except Exception as e:
                    logger.warning(f"Le champ métier n'est pas visible: {e}")
                    logger.info("Essai de localisation par d'autres sélecteurs...")
                    # Essayer d'autres sélecteurs
                    try:
                        metier_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#metier, input[name='metier'], input[placeholder*='métier']")))
                        logger.info("✅ Champ métier trouvé avec un sélecteur alternatif!")
                    except Exception as e2:
                        logger.error(f"Impossible de trouver le champ métier avec des sélecteurs alternatifs: {e2}")
                        # Sauvegarde du DOM pour analyse
                        with open('etat_iframe.html', 'w', encoding='utf-8') as f:
                            f.write(driver.page_source)
                        logger.info("DOM de l'iframe sauvegardé dans 'etat_iframe.html'")
        except Exception as e:
            logger.error(f"Erreur lors de l'interaction avec l'iframe: {e}")
            # Revenir au contenu principal
            driver.switch_to.default_content()
            with open('etat_page_principale.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info("DOM de la page principale sauvegardé dans 'etat_page_principale.html'")
            raise  # Relancer l'exception pour indiquer qu'il y a eu un problème grave
        
        # Pause avant de commencer le remplissage
        time.sleep(2)
        
        # Étape 3: Remplissage des champs avec notre fonction améliorée
        logger.info("Début du remplissage des champs du formulaire...")
        
        # Vérifier la présence des champs principal avant de commencer
        try:
            # Utiliser les sélecteurs variables pour trouver le champ métier
            metier_selectors = [
                "#metier", 
                "input[placeholder*='métier']",
                ".modal input[type='text']:first-child",
                "input.fr-input"
            ]
            
            metier_input = None
            for selector in metier_selectors:
                try:
                    metier_input = short_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.info(f"Champ métier trouvé avec le sélecteur: {selector}")
                    break
                except:
                    continue
            
            if not metier_input:
                logger.warning("Champ métier introuvable avec les sélecteurs standard")
        except Exception as e:
            logger.error(f"Problème lors de la recherche des champs: {e}")
        
        # Tentative de remplissage du champ métier
        if not fill_field_with_autocomplete(driver, wait, 'metier', user_data['search_query']):
            logger.error("Impossible de remplir le champ métier")
            raise Exception("Erreur lors de la tentative de soumission du formulaire: Échec du remplissage du champ 'métier'")
                
        # Pause entre les champs
        time.sleep(1.5)
            
        # Tentative de remplissage du champ lieu
        if not fill_field_with_autocomplete(driver, wait, 'lieu', user_data['location']):
            logger.warning("Impossible de remplir le champ lieu, essai de continuer sans")
            
        # Pause avant soumission 
        time.sleep(1)
            
        # Étape 4: Soumission du formulaire - multiple sélecteurs et stratégies
        logger.info("Préparation à la soumission du formulaire...")
            
        # Liste des sélecteurs possibles pour le bouton de soumission
        submit_button_selectors = [
            "button[title=\"C'est parti\"]",
            ".fr-btn--primary",
            "button.search-button",
            "button[type='submit']",
            "input[type='submit']",
            ".modal-content button",
            "button:contains('partir')"
        ]
            
        # Tentative avec chaque sélecteur
        submit_button = None
        for selector in submit_button_selectors:
            try:
                submit_button = short_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                logger.info(f"Bouton de soumission trouvé avec le sélecteur: {selector}")
                break
            except:
                continue
        
        if not submit_button:
            # Si aucun bouton n'est trouvé avec les sélecteurs, essayer avec le texte du bouton
            try:
                # Recherche par texte (moins fiable mais solution de secours)
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if "parti" in button.text or "search" in button.text.lower() or "submit" in button.get_attribute("class").lower():
                        submit_button = button
                        logger.info(f"Bouton de soumission trouvé avec le texte: {button.text}")
                        break
            except Exception as e:
                logger.warning(f"Tentative de recherche par texte échouée: {e}")
        
        # Pause avant soumission 
        time.sleep(1)
        
        # Étape 4: Soumission du formulaire - multiple sélecteurs et stratégies
        logger.info("Préparation à la soumission du formulaire...")
        
        # Liste des sélecteurs possibles pour le bouton de soumission
        submit_button_selectors = [
            "button[title=\"C'est parti\"]",
            ".fr-btn--primary",
            "button.search-button",
            "button[type='submit']",
            "input[type='submit']",
            ".modal-content button",
            "button:contains('partir')"
        ]
        
        # Tentative avec chaque sélecteur
        submit_button = None
        for selector in submit_button_selectors:
            try:
                submit_button = short_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                logger.info(f"Bouton de soumission trouvé avec le sélecteur: {selector}")
                break
            except:
                continue
        
        if not submit_button:
            # Si aucun bouton n'est trouvé avec les sélecteurs, essayer avec le texte du bouton
            try:
                # Recherche par texte (moins fiable mais solution de secours)
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if "parti" in button.text or "search" in button.text.lower() or "submit" in button.get_attribute("class").lower():
                        submit_button = button
                        logger.info(f"Bouton de soumission trouvé avec le texte: {button.text}")
                        break
            except Exception as e:
                logger.warning(f"Tentative de recherche par texte échouée: {e}")
                
        if submit_button:
            # Essayer trois méthodes de clic différentes en séquence
            click_methods = [
                ("JavaScript", lambda btn: driver.execute_script("arguments[0].click();", btn)),
                ("ActionChains", lambda btn: ActionChains(driver).move_to_element(btn).click().perform()),
                ("Native", lambda btn: btn.click())
            ]
            
            click_success = False
            for method_name, click_method in click_methods:
                try:
                    logger.info(f"Tentative de clic par {method_name}...")
                    click_method(submit_button)
                    logger.info(f"Clic par {method_name} réussi")
                    click_success = True
                    break
                except Exception as e:
                    logger.warning(f"Clic par {method_name} a échoué: {e}")
            
            if not click_success:
                logger.error("Toutes les méthodes de clic ont échoué")
                raise Exception("Impossible de cliquer sur le bouton de soumission")
            
            logger.info("Formulaire soumis, attente des résultats...")
            
            # Retour au contenu principal
            driver.switch_to.default_content()
            
            # Attendre que la page change (URL ou contenu)
            start_url = driver.current_url
            start_time = time.time()
            wait_time = 15  # Temps d'attente maximum
            
            # Boucle d'attente avec vérification d'URL ou contenu changé
            while time.time() - start_time < wait_time:
                    if driver.current_url != start_url:
                        logger.info("URL changée - transition de page détectée")
                        break
                        
                    # Vérifier si des éléments de résultats sont présents
                    try:
                        # Vérifier si on a été redirigé vers "La bonne alternance"
                        if "labonnealternance" in driver.current_url:
                            logger.info(f"Redirection vers La bonne alternance détectée: {driver.current_url}")
                            break
                            
                        # Vérifier si une iframe La bonne alternance est présente
                        iframes = driver.find_elements(By.TAG_NAME, "iframe")
                        for iframe in iframes:
                            if "labonnealternance" in iframe.get_attribute("src"):
                                logger.info(f"Iframe La bonne alternance détectée: {iframe.get_attribute('src')}")
                                break
                        
                        # Vérifier les éléments spécifiques à La bonne alternance
                        if driver.find_elements(By.CSS_SELECTOR, ".chakra-container, .chakra-heading, [data-testid], .desktop-widget"):
                            logger.info("Éléments de La bonne alternance détectés")
                            break
                            
                        # Anciens sélecteurs pour compatibilité
                        if driver.find_elements(By.CSS_SELECTOR, "#result-list-content, .fr-card, .result-item"):
                            logger.info("Éléments de résultats standards détectés")
                            break
                    except Exception as e:
                        logger.debug(f"Exception lors de la vérification des résultats: {e}")
                        pass
                        
                    time.sleep(0.5)
            
            # Pause supplémentaire pour s'assurer que tout est chargé
            logger.info("Attente supplémentaire pour finaliser le chargement...")
            time.sleep(5)
        else:
            logger.error("Impossible de trouver le bouton de soumission")
            raise Exception("Bouton de soumission non trouvé")
        
        logger.info("Formulaire soumis. Attente des résultats...")
        
        # Retour au contexte principal et attente des résultats
        logger.info("Retour au contexte principal de la page.")
        driver.switch_to.default_content()
        
        # Attendre soit un changement d'URL, soit l'apparition des résultats
        current_url = driver.current_url
        
        # Définir un timeout plus long pour l'attente des résultats
        wait_results = WebDriverWait(driver, 20)  # 20 secondes de timeout
        
        try:
            # Attendre que soit l'URL change, soit le conteneur de résultats apparaît
            logger.info("Attente de chargement des résultats...")
            result_container = wait_results.until(
                lambda d: (d.current_url != current_url) or 
                          ("labonnealternance" in d.current_url) or
                          any("labonnealternance" in iframe.get_attribute("src") 
                              for iframe in d.find_elements(By.TAG_NAME, "iframe")) or
                          d.find_elements(By.CSS_SELECTOR, ".chakra-container, .chakra-heading, [data-testid], .desktop-widget") or
                          d.find_elements(By.ID, "result-list-content")
            )
            
            # Identifier le type de page de résultats
            is_bonne_alternance = "labonnealternance" in driver.current_url
            has_bonne_alternance_iframe = any("labonnealternance" in iframe.get_attribute("src") 
                                              for iframe in driver.find_elements(By.TAG_NAME, "iframe"))
            
            if is_bonne_alternance or has_bonne_alternance_iframe:
                logger.info(f"Page 'La bonne alternance' chargée. URL finale: {driver.current_url}")
            else:
                logger.info(f"Page de résultats standard chargée. URL finale: {driver.current_url}")
            time.sleep(2)  # Pause pour s'assurer que le JavaScript a terminé le rendu
        except TimeoutException:
            logger.error("Timeout: la page de résultats n'a pas chargé dans le délai imparti.")
            # Sauvegarder la page pour diagnostic
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"debug_screenshots/timeout_results_{timestamp}.png"
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                driver.save_screenshot(screenshot_path)
                logger.info(f"Capture d'écran de diagnostic enregistrée dans {screenshot_path}")
                
                # Sauvegarder également le code source de la page
                source_path = f"debug_screenshots/page_source_{timestamp}.html"
                with open(source_path, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                logger.info(f"Code source de la page enregistré dans {source_path}")
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde du diagnostic: {e}")
                
            # Vérifier si nous avons une iframe labonnealternance et l'afficher dans les logs
            try:
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    src = iframe.get_attribute("src")
                    if src and "labonnealternance" in src:
                        logger.info(f"Iframe labonnealternance détectée mais non traitée: {src}")
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse des iframes: {e}")
            with open('page_apres_soumission_erreur.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info("État de la page sauvegardé dans 'page_apres_soumission_erreur.html'")
        except Exception as e:
            logger.error(f"Erreur lors de la tentative de soumission du formulaire: {e}")
            # Sauvegarder la page pour diagnostic
            with open('page_erreur_soumission.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info("État de la page sauvegardé dans 'page_erreur_soumission.html'")

        try:
            # Petite pause pour s'assurer que le JS a fini de rendre les éléments
            time.sleep(3)

        except TimeoutException:
            logger.error("Le conteneur des résultats (id='result-list-content') n'est pas apparu après la soumission.")
            logger.info("Sauvegarde de la page actuelle pour débogage...")
            error_page_path = os.path.join(os.path.dirname(__file__), 'page_apres_soumission_erreur.html')
            with open(error_page_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info(f"Page sauvegardée dans : {error_page_path}")
            raise # Re-raise the exception to stop the script
        
        # Sauvegarde du code source de la page de résultats pour analyse...
        logger.info("Sauvegarde du code source de la page de résultats pour analyse...")
        results_filepath = os.path.join(os.path.dirname(__file__), 'page_resultats.html')
        with open(results_filepath, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info(f"✅ Code source des résultats sauvegardé dans '{results_filepath}'.")
        
        # Traitement spécifique pour La bonne alternance
        job_offers = []
        
        # Vérifier si nous avons une iframe de La bonne alternance
        labonne_iframe = None
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                src = iframe.get_attribute("src")
                if src and "labonnealternance" in src:
                    labonne_iframe = iframe
                    logger.info(f"Iframe La bonne alternance trouvée pour extraction: {src}")
                    break
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de l'iframe: {e}")
        
        if labonne_iframe:
            # Traitement spécifique pour La bonne alternance
            try:
                # Initialiser la liste des offres
                job_offers = []
                
                # Basculer vers l'iframe
                logger.info("Basculement vers l'iframe La bonne alternance...")
                driver.switch_to.frame(labonne_iframe)
                
                # Attendre que le contenu de l'iframe se charge complètement
                try:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".fr-card, div[role='group'], .chakra-stack")))
                    logger.info("Contenu de l'iframe chargé avec succès")
                except TimeoutException:
                    logger.warning("Timeout en attendant le chargement du contenu de l'iframe - continuons quand même")
                
                # Capturer une capture d'écran pour le debug
                screenshot_path = "debug_screenshots/labonnealternance_content.png"
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                driver.save_screenshot(screenshot_path)
                logger.info(f"Capture d'écran de l'iframe enregistrée dans {screenshot_path}")
                
                # Afficher l'HTML complet de l'iframe pour debug
                iframe_html = driver.page_source
                debug_html_path = "debug_screenshots/labonnealternance_html.html"
                os.makedirs(os.path.dirname(debug_html_path), exist_ok=True)
                with open(debug_html_path, 'w', encoding='utf-8') as f:
                    f.write(iframe_html)
                logger.info(f"HTML de l'iframe sauvegardé dans {debug_html_path}")
                
                # Scroll pour charger plus de contenu si nécessaire (important pour le chargement dynamique)
                try:
                    for _ in range(3):  # Scrollez 3 fois pour charger plus de contenu
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                except Exception as e:
                    logger.warning(f"Erreur lors du scroll: {e} - continuons quand même")
                
                # Différentes stratégies de sélection des offres
                selectors_strategies = [
                    ".fr-card",  # Format standard France Connect
                    "div[role='group']",  # Chakra UI groupes (structure commune)
                    ".chakra-stack .chakra-card",  # Format Chakra UI card
                    ".chakra-stack > div:not([class])",  # Divs directs dans les stacks (souvent utilisé pour les cartes)
                    ".chakra-box div[role='group']", # Boîtes Chakra contenant des groupes
                    ".result-item, .fr-tile, .tile" # Classes communes pour les résultats de recherche
                ]
                
                # Essayer chaque stratégie de sélecteur jusqu'à trouver des résultats
                formation_cards = []
                for selector in selectors_strategies:
                    logger.info(f"Essai avec le sélecteur: {selector}")
                    formation_cards = driver.find_elements(By.CSS_SELECTOR, selector)
                    if formation_cards:
                        logger.info(f"Trouvé {len(formation_cards)} éléments avec le sélecteur {selector}")
                        break
                
                if not formation_cards:
                    # Dernier recours: chercher tous les conteneurs qui pourraient être des cartes
                    logger.warning("Aucune offre trouvée avec les sélecteurs standards. Essai avec sélecteur générique...")
                    formation_cards = driver.find_elements(By.CSS_SELECTOR, ".chakra-box, div[role], article, section > div")
                    logger.info(f"Tentative de secours: {len(formation_cards)} éléments potentiels trouvés")
                
                # Pas de limite fixe pour le nombre d'offres, mais filtrons les cartes trop petites
                valid_cards = []
                for card in formation_cards:
                    # Vérifier si la carte a une taille minimale et du contenu
                    try:
                        if len(card.text.strip()) > 20:  # Au moins 20 caractères de texte
                            valid_cards.append(card)
                    except:
                        continue
                
                logger.info(f"Nombre total de cartes valides: {len(valid_cards)}")
                
                # Récupérer les URL de base pour les liens relatifs
                base_url = "https://labonnealternance.apprentissage.beta.gouv.fr"
                
                # Extraire les informations de chaque carte d'offre/formation
                for index, card in enumerate(valid_cards):
                    try:
                        # Capturer le HTML complet de la carte pour le debug
                        card_html = card.get_attribute('outerHTML')
                        card_debug_path = f"debug_screenshots/card_{index}.html"
                        with open(card_debug_path, 'w', encoding='utf-8') as f:
                            f.write(card_html)
                        
                        # Extraction du titre avec plusieurs stratégies
                        title = "Titre non disponible"
                        title_selectors = [
                            "h3, h4, h5, .chakra-heading, .fr-card__title",  # En-têtes standard
                            "[data-testid*='title'], [class*='title'], strong, b",  # Attributs data ou classes contenant 'title'
                            ".chakra-text:first-of-type, p:first-of-type"  # Premier élément de texte
                        ]
                        
                        for selector in title_selectors:
                            try:
                                title_element = card.find_element(By.CSS_SELECTOR, selector)
                                title_text = title_element.text.strip()
                                if title_text and len(title_text) > 3:  # Au moins 3 caractères
                                    title = title_text
                                    break
                            except:
                                continue
                        
                        if title == "Titre non disponible":
                            # Fallback: utiliser la première ligne du texte de la carte
                            text_lines = [line.strip() for line in card.text.split('\n') if line.strip()]
                            if text_lines:
                                title = text_lines[0]
                        
                        # Extraction de l'entreprise/établissement
                        company = "Entreprise non disponible"
                        company_selectors = [
                            ".fr-card__desc, .chakra-text[data-testid*='company']",
                            "p:not(:first-child), .subtitle, [class*='company']",
                            ".chakra-stack p"  # Paragraphes dans un chakra-stack
                        ]
                        
                        for selector in company_selectors:
                            try:
                                company_elements = card.find_elements(By.CSS_SELECTOR, selector)
                                if company_elements:
                                    for elem in company_elements:
                                        text = elem.text.strip()
                                        if text and not any(x in text.lower() for x in ["date", "durée", "km", "à "]) and len(text) > 3:
                                            company = text
                                            break
                            except:
                                continue
                        
                        if company == "Entreprise non disponible":
                            # Fallback: chercher la deuxième ligne de texte ou une ligne qui semble être un nom d'entreprise
                            text_lines = [line.strip() for line in card.text.split('\n') if line.strip()]
                            if len(text_lines) > 1:
                                company = text_lines[1]
                        
                        # Extraction du lieu avec recherche de code postal ou ville
                        location = "Lieu non disponible"
                        location_selectors = [
                            ".fr-card__start, address, [data-testid*='location'], [class*='location']",
                            ".chakra-text:contains('km'), .chakra-text:contains('Paris'), .chakra-text:contains('Lyon')",
                            "span:contains('km'), div:contains('km')",
                            "p:contains(', ')"  # Format commun pour les adresses: "Ville, Code postal"
                        ]
                        
                        import re
                        postal_code_pattern = re.compile(r'\b\d{5}\b')  # Regex pour les codes postaux français
                        
                        for selector in location_selectors:
                            try:
                                location_elements = card.find_elements(By.CSS_SELECTOR, selector.replace(':contains', ''))
                                if location_elements:
                                    for elem in location_elements:
                                        text = elem.text.strip()
                                        # Si le texte contient un code postal ou une distance en km, c'est probablement un lieu
                                        if text and (postal_code_pattern.search(text) or 'km' in text.lower() or any(city in text for city in ['Paris', 'Lyon', 'Marseille', 'Toulouse'])):
                                            location = text
                                            break
                            except:
                                continue
                        
                        if location == "Lieu non disponible":
                            # Fallback: chercher une ligne contenant un code postal ou km
                            text_lines = [line.strip() for line in card.text.split('\n') if line.strip()]
                            for line in text_lines:
                                if postal_code_pattern.search(line) or 'km' in line.lower():
                                    location = line
                                    break
                        
                        # Tenter d'extraire un lien
                        link = ""
                        try:
                            link_element = card.find_element(By.TAG_NAME, "a")
                            link = link_element.get_attribute('href') or ""
                            if link and link.startswith('/'):
                                link = f"{base_url}{link}"
                        except:
                            link = ""
                        
                        # Déterminer le type d'offre
                        card_text = card.text.lower()
                        offer_type = "Autre"
                        
                        if any(term in card_text for term in ["formation", "école", "diplôme", "certific", "étude", "apprentissage"]):
                            offer_type = "Formation"
                        elif any(term in card_text for term in ["entreprise", "emploi", "offre", "recrute", "job", "cdd", "cdi", "alternance"]):
                            offer_type = "Entreprise"
                        
                        # Créer un dictionnaire avec les informations de l'offre
                        job_offer = {
                            "title": title,
                            "company": company,
                            "location": location,
                            "link": link,
                            "type": offer_type,
                            "source": "La bonne alternance"
                        }
                        
                        job_offers.append(job_offer)
                        logger.info(f"Offre {index+1} ajoutée: {title} chez {company} à {location} ({offer_type})")
                    except Exception as e:
                        logger.error(f"Erreur lors de l'extraction des données de la carte {index}: {e}", exc_info=True)
                
                # Revenir au contexte principal
                driver.switch_to.default_content()
                logger.info("Retour au contexte principal après traitement de l'iframe")
                
                # Afficher le résumé des offres trouvées
                logger.info(f"Total des offres extraites depuis La bonne alternance: {len(job_offers)}")
                
                # Si des offres ont été trouvées, les retourner directement
                if job_offers:
                    return job_offers
                    
            except Exception as e:
                logger.error(f"Erreur lors du traitement de l'iframe La bonne alternance: {e}")
                driver.switch_to.default_content()  # S'assurer de revenir au contexte principal

        # Si on n'a pas pu extraire depuis l'iframe, essayer la méthode classique
        logger.info("Analyse des résultats via la méthode classique...")
        return parse_results(driver.page_source)

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

def parse_results(html_content):
    """Parse la page de résultats pour en extraire les offres."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Le conteneur principal des résultats
        results_container = soup.find('div', id='result-list-content')
        
        if not results_container:
            logger.error("Impossible de trouver le conteneur des offres sur la page (id='result-list-content').")
            # Fallback attempt on the whole body if the specific container is not found
            results_container = soup.find('body')
            if not results_container:
                logger.error("Le corps du document est vide. Impossible de continuer.")
                return
            logger.warning("Conteneur 'result-list-content' non trouvé, recherche des cartes sur toute la page.")

        # Les offres sont des div avec la classe 'fr-card'
        job_offers = results_container.find_all('div', class_='fr-card')
        
        if not job_offers:
            logger.warning("Aucune offre d'emploi trouvée avec le sélecteur 'div.fr-card'. Le site a peut-être changé ou il n'y a pas de résultats pour cette recherche.")
            return

        logger.info(f"{len(job_offers)} offres trouvées. Début de l'extraction...")
        base_url = "https://www.alternance.emploi.gouv.fr"
        extracted_count = 0

        for offer in job_offers:
            title_element = offer.find(['h3', 'h4'], class_='fr-card__title')
            title = title_element.get_text(strip=True) if title_element else 'N/A'
            
            company_element = offer.find('p', class_='fr-card__detail')
            company = company_element.get_text(strip=True) if company_element else 'N/A'

            location_element = offer.find('p', class_='fr-card__start')
            location = location_element.get_text(strip=True) if location_element else 'N/A'
            
            link_element = offer.find('a', class_='fr-card__link')
            link = link_element['href'] if link_element and link_element.has_attr('href') else 'N/A'

            # If any of the main fields are missing, this is likely not a job card we want.
            if title == 'N/A' or company == 'N/A':
                continue
            
            # Make sure the link is absolute
            if link.startswith('/'):
                link = f"{base_url}{link}"
            
            extracted_count += 1
            logger.info("--- Offre --- ")
            logger.info(f"Titre: {title}")
            logger.info(f"Entreprise: {company}")
            logger.info(f"Lieu: {location}")
            logger.info(f"Lien: {link}")
        
        if extracted_count == 0:
            logger.warning("Aucune offre valide n'a pu être extraite des cartes trouvées.")

    except Exception as e:
        logger.error(f"Erreur lors de l'analyse des résultats: {e}", exc_info=True)

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