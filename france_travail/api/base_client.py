# /Users/davidravin/Desktop/Api_Final/france_travail/api/base_client.py
import os
import requests
import logging
import time
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BaseClient:
    """
    Client de base pour interagir avec les API de France Travail.
    Gère l'authentification, les appels et la limitation de débit (rate limiting).
    """
    def __init__(self, client_id=None, client_secret=None, base_url=None, scope=None, simulation=False):
        load_dotenv()
        self.client_id = client_id or os.getenv('FRANCE_TRAVAIL_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('FRANCE_TRAVAIL_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Les identifiants FRANCE_TRAVAIL_CLIENT_ID et FRANCE_TRAVAIL_CLIENT_SECRET sont requis.")

        self.auth_url = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
        self.base_url = base_url
        self.scope = scope
        
        self.access_token = None
        self.simulation = simulation

        # Limite par défaut, peut être surchargée par les clients spécifiques
        self.request_delay = 1.0 / 10  # 10 appels/seconde
        self.last_request_time = 0

    def _authenticate(self):
        """
        S'authentifie auprès de l'API pour obtenir un token d'accès.
        """
        logging.info(f"Tentative d'authentification pour le scope: {self.scope}...")
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.scope
        }
        
        params = {
            'realm': '/partenaire'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            response = requests.post(self.auth_url, params=params, data=data, headers=headers, timeout=15)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            
            if not self.access_token:
                logging.error("Le token d'accès n'a pas été trouvé dans la réponse.")
                return False
                
            logging.info("Authentification réussie.")
            return True

        except requests.exceptions.HTTPError as e:
            logging.error(f"Erreur HTTP lors de l'authentification: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logging.error(f"Une erreur inattendue est survenue lors de l'authentification: {e}")
            return False

    def _make_request(self, method, endpoint, **kwargs):
        """
        Méthode générique pour effectuer des requêtes à l'API, avec gestion du rate limiting.
        """
        if not self.access_token and not self._authenticate():
            return None

        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_delay:
            sleep_time = self.request_delay - elapsed
            logging.info(f"Rate limiting: pause de {sleep_time:.2f}s.")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

        url = f"{self.base_url}{endpoint}"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers

        try:
            response = requests.request(method, url, **kwargs)
            
            if response.status_code == 401:
                logging.warning("Token expiré (401). Tentative de ré-authentification.")
                self.access_token = None
                if self._authenticate():
                    kwargs['headers']['Authorization'] = f'Bearer {self.access_token}'
                    response = requests.request(method, url, **kwargs)

            response.raise_for_status()
            
            if response.status_code == 204:
                return None
            return response.json()

        except requests.exceptions.HTTPError as e:
            logging.error(f"Erreur HTTP pour {method.upper()} {url}: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logging.error(f"Erreur pour {method.upper()} {url}: {e}")
            return None
