#!/usr/bin/env python3
"""
Automation Runner - Interface between the web application and the existing Python automation scripts
"""

import json
import sys
import os
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
import time

# Add the attached_assets and parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'attached_assets'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))  # Pour accéder au module db_integration

# Import database integration
try:
    from db_integration import DatabaseIntegration
    DB_INTEGRATION_LOADED = True
except ImportError as e:
    logging.error(f"Failed to import database integration: {e}")
    DB_INTEGRATION_LOADED = False

# Import the main automation script
try:
    from alternance_gouv_1751543361694 import run_scraper, setup_driver, parse_results
    from postuler_functions_1751543385370 import postuler_offre, remplir_formulaire_candidature
    from capture_functions_1751543392689 import capture_and_highlight, switch_to_iframe_if_needed
    SCRIPTS_LOADED = True
except ImportError as e:
    logging.error(f"Failed to import automation scripts: {e}")
    SCRIPTS_LOADED = False

class AutomationRunner:
    def __init__(self, session_id: int, user_config: Dict[str, Any] = None, settings: Dict[str, Any] = None, user_id: int = None):
        self.session_id = session_id
        self.user_config = user_config or {}
        self.settings = settings or {}
        self.user_id = user_id
        self.driver = None
        self.applications_processed = 0
        self.successful_applications = 0
        self.failed_applications = 0
        self.db_integration = None
        
        self.setup_logging()
        
        # Si un user_id est fourni, récupérer les préférences depuis la base de données
        if user_id and DB_INTEGRATION_LOADED:
            try:
                self.db_integration = DatabaseIntegration()
                user_prefs = self.db_integration.get_user_preferences(user_id)
                if user_prefs:
                    logging.info(f"Préférences utilisateur récupérées pour l'ID {user_id}")
                    # Fusionner les préférences utilisateur avec la configuration fournie
                    # Les préférences explicites ont la priorité sur celles de la base de données
                    for key, value in user_prefs.items():
                        if key not in self.user_config or not self.user_config[key]:
                            self.user_config[key] = value
                    
                    # Fusionner les paramètres
                    if 'settings' in user_prefs and isinstance(user_prefs['settings'], dict):
                        if not self.settings:
                            self.settings = user_prefs['settings']
                        else:
                            for setting_key, setting_value in user_prefs['settings'].items():
                                if setting_key not in self.settings:
                                    self.settings[setting_key] = setting_value
                    
                    logging.info(f"Configuration finale: métier='{self.user_config.get('search_query', '')}', lieu='{self.user_config.get('location', '')}', email='{self.user_config.get('email', '')}")
                else:
                    logging.warning(f"Aucune préférence utilisateur trouvée pour l'ID {user_id}")
            except Exception as e:
                logging.error(f"Erreur lors de la récupération des préférences utilisateur: {e}")
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/automation_{self.session_id}.log'),
                logging.StreamHandler()
            ]
        )
        
    def log_message(self, level: str, message: str, metadata: Optional[Dict] = None):
        """Log a message that will be sent to the web interface"""
        log_entry = {
            'type': 'log',
            'level': level,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'metadata': metadata or {}
        }
        
        # Send to web interface via stdout
        print(f"WEB_LOG: {json.dumps(log_entry)}")
        
        # Also log locally
        getattr(logging, level.lower(), logging.info)(message)
    
    def send_web_log(self, message: str, level: str = "info", metadata: Dict[str, Any] = None):
        """Send a log message to the web interface"""
        self.log_message(level, message, metadata)
        
    def send_web_event(self, event_type: str, data: Dict[str, Any] = None):
        """Send an event to the web interface"""
        self.emit_event(event_type, data or {})
        
    def send_session_stats(self):
        """Send session statistics to the web interface"""
        self.update_session_stats()
        
    def send_session_completed(self):
        """Send session completion event to the web interface"""
        self.emit_event("session_completed", {
            "session_id": self.session_id,
            "completed_at": datetime.now().isoformat(),
            "total_applications": self.applications_processed,
            "successful_applications": self.successful_applications,
            "failed_applications": self.failed_applications
        })
    
    def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to the web interface"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id
        }
        
        print(f"WEB_EVENT: {json.dumps(event)}")
    
    def setup_driver(self):
        """Setup the Selenium WebDriver"""
        try:
            self.log_message('info', 'Configuration du navigateur Chrome...')
            self.driver = setup_driver()
            self.log_message('success', 'Navigateur configuré avec succès')
            return True
        except Exception as e:
            self.log_message('error', f'Erreur lors de la configuration du navigateur: {str(e)}')
            return False
    
    def capture_screenshot(self, description: str, application_data: Optional[Dict] = None):
        """Capture a screenshot and notify the web interface"""
        try:
            if not self.driver:
                return None
                
            filename = f"debug_screenshots/session_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            if SCRIPTS_LOADED:
                capture_and_highlight(self.driver, None, description)
            else:
                self.driver.save_screenshot(filename)
            
            # Notify web interface
            screenshot_data = {
                'session_id': self.session_id,
                'file_path': filename,
                'description': description,
                'captured_at': datetime.now().isoformat()
            }
            
            if application_data:
                screenshot_data['application_id'] = application_data.get('id')
            
            self.emit_event('screenshot_captured', screenshot_data)
            return filename
            
        except Exception as e:
            self.log_message('error', f'Erreur lors de la capture: {str(e)}')
            return None
    
    def process_application(self, offer_data: Dict[str, Any]) -> bool:
        """Process a single job application"""
        try:
            self.log_message('info', f'Traitement de l\'offre: {offer_data["title"]}')
            
            # Create application record
            application_data = {
                'session_id': self.session_id,
                'job_title': offer_data['title'],
                'company': offer_data.get('company', 'Non spécifié'),
                'location': offer_data.get('location', 'Non spécifié'),
                'status': 'pending',
                'applied_at': datetime.now().isoformat()
            }
            
            self.emit_event('application_started', application_data)
            
            # Capture screenshot before processing
            self.capture_screenshot(f"Avant candidature - {offer_data['title']}", application_data)
            
            # Process the application
            success = self.fill_application_form(offer_data, application_data)
            
            if success:
                application_data['status'] = 'completed'
                self.successful_applications += 1
                self.log_message('success', f'Candidature envoyée avec succès pour {offer_data["title"]}')
            else:
                application_data['status'] = 'failed'
                application_data['error_message'] = 'Échec lors du remplissage du formulaire'
                self.failed_applications += 1
                self.log_message('error', f'Échec de candidature pour {offer_data["title"]}')
            
            # Capture screenshot after processing
            self.capture_screenshot(f"Après candidature - {offer_data['title']}", application_data)
            
            self.emit_event('application_completed', application_data)
            self.applications_processed += 1
            
            return success
            
        except Exception as e:
            self.log_message('error', f'Erreur lors du traitement de l\'offre: {str(e)}')
            traceback.print_exc()
            return False
    
    def fill_application_form(self, offer_data: Dict[str, Any], application_data: Dict[str, Any]) -> bool:
        """Fill the application form using the existing automation functions"""
        try:
            if not SCRIPTS_LOADED:
                self.log_message('warning', 'Scripts d\'automatisation non chargés, simulation de candidature')
                return True
            
            # Use the existing postuler_offre function
            url_offre = offer_data.get('url', '')
            titre_offre = offer_data.get('title', '')
            
            if not url_offre:
                self.log_message('error', 'URL de l\'offre manquante')
                return False
            
            # Navigate to the offer and apply
            success = postuler_offre(self.driver, url_offre, titre_offre, self.user_config)
            
            return success
            
        except Exception as e:
            self.log_message('error', f'Erreur lors du remplissage du formulaire: {str(e)}')
            return False
    
    def update_session_stats(self):
        """Update and emit session statistics"""
        stats = {
            'total_applications': self.applications_processed,
            'successful_applications': self.successful_applications,
            'failed_applications': self.failed_applications,
            'session_id': self.session_id
        }
        
        self.emit_event('session_stats_updated', stats)
    
    def run(self):
        """Run the automation process"""
        logging.info("Démarrage de l'automatisation réelle...")
        self.send_web_log("Démarrage de l'automatisation réelle...", "info")
        
        if not SCRIPTS_LOADED:
            logging.error("Scripts d'automatisation non disponibles")
            self.send_web_log("Scripts d'automatisation non disponibles", "error")
            self.send_session_stats()
            self.send_session_completed()
            return False
        
        # Préparation des données utilisateur
        user_data = {}
        
        # Si un user_id est spécifié, récupérer les préférences depuis la BDD
        if self.user_id and DB_INTEGRATION_LOADED:
            try:
                self.db_integration = DatabaseIntegration()
                db_user_data = self.db_integration.get_user_preferences(self.user_id)
                if db_user_data:
                    # Utiliser les données de la base prioritairement
                    user_data = db_user_data
                    logging.info(f"Préférences utilisateur récupérées depuis BDD: métier='{db_user_data.get('search_query', '')}', lieu='{db_user_data.get('location', '')}'")                 
                    self.send_web_log(f"Préférences récupérées de la base: {db_user_data.get('search_query', '')} à {db_user_data.get('location', '')}", "info")
                else:
                    logging.warning(f"Aucune préférence trouvée pour l'utilisateur ID {self.user_id}")
            except Exception as e:
                logging.error(f"Erreur lors de la récupération des préférences utilisateur: {e}")
        
        # Fusionner avec les données du formulaire (si fournies)
        if self.user_config:
            # Si des données user_config sont fournies et qu'il n'y a pas de données BDD ou si certaines valeurs sont vides
            for key, value in self.user_config.items():
                if key not in user_data or not user_data.get(key):
                    user_data[key] = value
            
            # Pour assurer la compatibilité
            if "firstName" in self.user_config and "first_name" not in user_data:
                user_data["first_name"] = self.user_config.get("firstName", "")
            if "lastName" in self.user_config and "last_name" not in user_data:
                user_data["last_name"] = self.user_config.get("lastName", "")
            if "searchKeywords" in self.user_config and "search_query" not in user_data:
                user_data["search_query"] = self.user_config.get("searchKeywords", "")
            
        try:
            # Démarrer le navigateur
            self.driver = setup_driver()
            if not self.driver:
                raise Exception("Impossible de démarrer le navigateur")
            
            # S'assurer que les clés nécessaires sont présentes dans user_data
            search_query = user_data.get("search_query", "")
            location = user_data.get("location", "")
            
            # Compléter user_data avec les champs obligatoires s'ils sont manquants
            user_data.update({
                "phone": self.user_config.get("phone", "") if "phone" not in user_data else user_data["phone"],
                "message": self.user_config.get("message", "") if "message" not in user_data else user_data["message"],
                "cv_path": self.user_config.get("cvPath", "") if "cv_path" not in user_data else user_data["cv_path"],
                "cover_letter_path": self.user_config.get("coverLetterPath", "") if "cover_letter_path" not in user_data else user_data["cover_letter_path"],
                "search_query": search_query,
                "location": location
            })
            
            self.send_web_log(f"Recherche lancée: '{search_query}' à '{location}'", "info")
            
            # Configure les paramètres dans user_data car la fonction n'accepte qu'un seul paramètre
            # Inclure toutes les configurations nécessaires dans le dictionnaire user_data
            user_data["settings"] = {
                "autoSendApplication": self.settings.get("autoSendApplication", True),
                "autoFillForm": self.settings.get("autoFillForm", True),
                "pauseBeforeSend": self.settings.get("pauseBeforeSend", False),
                "maxApplicationsPerSession": self.settings.get("maxApplicationsPerSession", 5),
                "delayBetweenApplications": self.settings.get("delayBetweenApplications", 5),
                "captureScreenshots": self.settings.get("captureScreenshots", True),
            }
            
            logging.info(f"Recherche lancée: {user_data.get('search_query', '')} à {user_data.get('location', '')}")
            
            # Call the scraper with our configuration
            offers = run_scraper(user_data)
            
            # Count applications and report back
            if offers:
                self.applications_processed = len(offers)
                for offer in offers:
                    if offer.get('application_status') == 'postulé':
                        self.successful_applications += 1
                    elif offer.get('application_status') == 'échec':
                        self.failed_applications += 1
                
                self.send_web_log(f"Traité {self.applications_processed} offres, {self.successful_applications} candidatures réussies", "info")
                self.send_web_event("offers_found", {"offers": offers})
                
                # Si l'intégration DB est activée et qu'un user_id est fourni, enregistrer les résultats
                if self.db_integration and self.user_id:
                    try:
                        self.db_integration.save_application_results(self.user_id, offers)
                        self.send_web_log(f"Candidatures enregistrées dans la base de données pour l'utilisateur ID {self.user_id}", "info")
                    except Exception as db_error:
                        self.send_web_log(f"Erreur lors de l'enregistrement des candidatures dans la BDD: {str(db_error)}", "error")
                
            else:
                self.send_web_log("Aucune offre trouvée correspondant aux critères", "warning")
            
            # Update statistics
            self.send_session_stats()
            
            # Completion
            self.send_session_completed()
            return True
            
        except Exception as e:
            error_msg = f"Erreur durant l'automatisation: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            self.send_web_log(error_msg, "error")
            self.send_session_completed()
            return False
            
        finally:
            # Fermer la connexion à la base de données si elle est ouverte
            if self.db_integration:
                try:
                    self.db_integration.close()
                except Exception as e:
                    logging.error(f"Erreur lors de la fermeture de la connexion BDD: {e}")
                    
            # Fermer le driver Selenium
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    logging.error(f"Erreur lors de la fermeture du driver: {e}")

def main():
    """Main entrypoint to run from console or as a subprocess"""
    try:
        # Vérifier si un argument --user-id est passé
        user_id = None
        if len(sys.argv) > 1 and sys.argv[1].startswith("--user-id="):
            try:
                user_id = int(sys.argv[1].split("=")[1])
                logging.info(f"User ID spécifié en ligne de commande: {user_id}")
            except (IndexError, ValueError):
                logging.error("Format de --user-id invalide")
                
        # Get the configuration from stdin
        user_config = {}
        settings = {}
        
        try:
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                user_data = json.loads(stdin_data)
                user_config = {k: v for k, v in user_data.items() if k != "settings"}
                settings = user_data.get("settings", {})
        except (json.JSONDecodeError, ValueError) as json_error:
            logging.warning(f"Aucune configuration valide fournie via stdin: {json_error}")
            # Si pas de config en stdin mais un user_id, on continue pour récupérer depuis la BDD
            if not user_id:
                raise ValueError("Ni configuration stdin ni user_id valide fourni")
                
        session_id = 1  # Hardcoded for testing
        
        # Create and run the automation
        runner = AutomationRunner(session_id, user_config, settings, user_id)
        runner.run()
        
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        logging.error(f"Main process error: {e}")
        logging.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    main()