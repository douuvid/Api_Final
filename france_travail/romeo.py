"""
Client pour l'API ROMEO v2 de France Travail - VERSION CORRIGÉE

Ce module fournit une interface pour interagir avec l'API ROMEO qui permet
de rechercher et de récupérer des informations sur les entreprises.

Corrections apportées:
- Authentification OAuth2 correcte
- URL de base mise à jour
- Gestion des tokens d'accès
"""

import base64
import json
import time
from typing import Dict, Optional, Any, List, Union
import requests
from datetime import datetime, timedelta


class RomeoAPI:
    """
    Client pour l'API ROMEO v2 de France Travail.
    
    Cette classe permet d'interagir avec l'API ROMEO qui fournit des informations
    sur les entreprises en France. L'API est limitée à 2 appels par seconde.
    
    Args:
        client_id (str): Identifiant client de l'API ROMEO
        client_secret (str): Clé secrète de l'API ROMEO
    """
    
    def __init__(self, client_id: str, client_secret: str, base_url: str = None):
        """
        Initialise le client API ROMEO avec les identifiants fournis.
        
        Args:
            client_id: Identifiant client de l'API ROMEO
            client_secret: Clé secrète de l'API ROMEO
            base_url: URL de base de l'API (optionnel)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        
        # URL correcte pour l'API ROMEO
        self.base_url = base_url or "https://api.emploi-store.fr/partenaire/romeo/v1"
        self.auth_url = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
        
        self.rate_limit = 2  # 2 appels par seconde
        self.rate_limit_interval = 1.0  # en secondes
        self.last_calls: List[float] = []
        
        # Headers par défaut
        self.default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'FranceTravail-API-Client/1.0'
        }
        
        # Gestion du token d'authentification OAuth2
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    def _get_oauth2_token(self) -> str:
        """
        Obtient un token OAuth2 depuis l'API France Travail.
        
        Returns:
            Le token d'accès OAuth2
            
        Raises:
            requests.HTTPError: Si l'authentification échoue
        """
        # Vérifier si le token existe et n'est pas expiré
        if self._access_token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._access_token
        
        # Préparer les données pour l'authentification OAuth2
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'api_romev1 o2dsoffre'  # Scope spécifique pour ROMEO
        }
        
        # Headers pour l'authentification
        auth_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.post(
                self.auth_url,
                data=auth_data,
                headers=auth_headers,
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            self._access_token = token_data['access_token']
            
            # Calculer l'expiration du token (généralement 1 heure)
            expires_in = token_data.get('expires_in', 3600)
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)  # Margin de 60s
            
            return self._access_token
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Erreur lors de l'authentification OAuth2: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" - {e.response.status_code} - {e.response.text}"
            raise requests.HTTPError(error_msg) from e
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Retourne les en-têtes d'authentification avec token OAuth2."""
        token = self._get_oauth2_token()
        return {
            **self.default_headers,
            'Authorization': f'Bearer {token}'
        }
    
    def _check_rate_limit(self):
        """Vérifie et applique la limite de taux d'appel (2 appels/seconde)."""
        now = time.time()
        
        # Supprime les appels plus vieux que l'intervalle
        self.last_calls = [t for t in self.last_calls if now - t < self.rate_limit_interval]
        
        # Si on a atteint la limite, on attend
        if len(self.last_calls) >= self.rate_limit:
            sleep_time = self.rate_limit_interval - (now - self.last_calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # On enregistre l'appel actuel
        self.last_calls.append(time.time())
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Effectue une requête à l'API ROMEO avec gestion des erreurs et du rate limiting.
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            endpoint: Point de terminaison de l'API
            **kwargs: Arguments supplémentaires pour requests.request()
            
        Returns:
            La réponse JSON de l'API
            
        Raises:
            requests.HTTPError: Si la requête échoue
        """
        self._check_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        headers = {**self._get_auth_headers(), **kwargs.pop('headers', {})}
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=30,
                **kwargs
            )
            response.raise_for_status()
            
            # Gérer les réponses vides
            if response.content:
                return response.json()
            else:
                return {"status": "success", "message": "No content"}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Erreur lors de l'appel à l'API ROMEO: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" - {e.response.status_code}"
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {e.response.text[:200]}"
            raise requests.HTTPError(error_msg) from e
            
    # ===== MÉTHODES DE TEST ET DIAGNOSTIC =====
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test la connexion à l'API ROMEO.
        
        Returns:
            Informations sur le statut de la connexion
        """
        try:
            # Test d'authentification
            token = self._get_oauth2_token()
            
            # Test d'un appel simple
            response = self._make_request('GET', '/status')
            
            return {
                "status": "success",
                "message": "Connexion réussie à l'API ROMEO",
                "token_obtained": bool(token),
                "api_response": response
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur de connexion: {str(e)}",
                "token_obtained": bool(self._access_token)
            }

    # ===== MÉTHODES DE L'API =====
    
    def search_companies(self, **criteria) -> Dict[str, Any]:
        """
        Recherche des entreprises selon des critères donnés.
        
        Args:
            **criteria: Critères de recherche possibles:
                - nom: Nom de l'entreprise
                - siret: Numéro SIRET
                - siren: Numéro SIREN
                - ville: Ville
                - code_postal: Code postal
                - code_activite: Code d'activité
                - forme_juridique: Forme juridique
                - limit: Nombre max de résultats (défaut: 20)
                - offset: Décalage pour la pagination (défaut: 0)
            
        Returns:
            Un dictionnaire contenant les résultats de la recherche
        """
        # Filtrer les critères non-null
        params = {k: v for k, v in criteria.items() if v is not None}
        
        # Limites par défaut
        if 'limit' not in params:
            params['limit'] = 20
        if 'offset' not in params:
            params['offset'] = 0
            
        return self._make_request('GET', '/entreprises/search', params=params)
    
    def get_company_by_siret(self, siret: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une entreprise par son SIRET.
        
        Args:
            siret: Numéro SIRET de l'entreprise (14 chiffres)
            
        Returns:
            Les détails de l'entreprise
        """
        if not siret:
            raise ValueError("Le SIRET est obligatoire")
        
        # Validation basique du format SIRET
        siret_clean = siret.replace(' ', '').replace('-', '')
        if not siret_clean.isdigit() or len(siret_clean) != 14:
            raise ValueError("Le SIRET doit contenir 14 chiffres")
            
        return self._make_request('GET', f'/entreprises/{siret_clean}')
    
    def get_company_by_siren(self, siren: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une entreprise par son SIREN.
        
        Args:
            siren: Numéro SIREN de l'entreprise (9 chiffres)
            
        Returns:
            Les détails de l'entreprise
        """
        if not siren:
            raise ValueError("Le SIREN est obligatoire")
            
        # Validation basique du format SIREN
        siren_clean = siren.replace(' ', '').replace('-', '')
        if not siren_clean.isdigit() or len(siren_clean) != 9:
            raise ValueError("Le SIREN doit contenir 9 chiffres")
            
        return self._make_request('GET', f'/entreprises/siren/{siren_clean}')
    
    def search_companies_by_location(
        self,
        latitude: float,
        longitude: float,
        radius: int = 10,
        activity_code: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Recherche des entreprises à proximité de coordonnées géographiques.
        
        Args:
            latitude: Latitude du point de recherche
            longitude: Longitude du point de recherche
            radius: Rayon de recherche en kilomètres (défaut: 10)
            activity_code: Code d'activité pour filtrer les résultats (optionnel)
            limit: Nombre maximum de résultats (défaut: 20)
            
        Returns:
            Les entreprises trouvées à proximité
        """
        # Validation des coordonnées
        if not (-90 <= latitude <= 90):
            raise ValueError("La latitude doit être entre -90 et 90")
        if not (-180 <= longitude <= 180):
            raise ValueError("La longitude doit être entre -180 et 180")
            
        params = {
            'lat': str(latitude),
            'lng': str(longitude),
            'radius': str(radius),
            'limit': str(limit)
        }
        
        if activity_code:
            params['code_activite'] = activity_code
            
        return self._make_request('GET', '/entreprises/geo', params=params)
    
    def get_activity_sectors(self) -> Dict[str, Any]:
        """
        Récupère la liste des secteurs d'activité.
        
        Returns:
            La liste des secteurs d'activité disponibles
        """
        return self._make_request('GET', '/referentiels/secteurs')
    
    def get_legal_forms(self) -> Dict[str, Any]:
        """
        Récupère la liste des formes juridiques.
        
        Returns:
            La liste des formes juridiques disponibles
        """
        return self._make_request('GET', '/referentiels/formes-juridiques')
    
    def get_api_status(self) -> Dict[str, Any]:
        """
        Vérifie le statut de l'API.
        
        Returns:
            Le statut actuel de l'API
        """
        return self._make_request('GET', '/status')
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques d'utilisation de l'API.
        
        Returns:
            Les statistiques d'utilisation
        """
        return self._make_request('GET', '/compte/statistiques')


# ===== SCRIPT DE TEST =====

def test_romeo_api():
    """Script de test pour l'API ROMEO."""
    import os
    from dotenv import load_dotenv
    
    # Charger les variables d'environnement
    load_dotenv()
    
    client_id = os.getenv('ROMEO_CLIENT_ID')
    client_secret = os.getenv('ROMEO_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Erreur: Variables d'environnement ROMEO_CLIENT_ID et ROMEO_CLIENT_SECRET requises")
        return False
    
    print(f"🔑 Identifiants chargés:")
    print(f"   Client ID: {client_id[:20]}...")
    print(f"   Client Secret: {client_secret[:20]}...")
    
    # Initialiser le client
    romeo = RomeoAPI(client_id, client_secret)
    
    print("\n=== TEST DE CONNEXION À L'API ROMEO ===")
    
    # Test de connexion
    connection_test = romeo.test_connection()
    print(f"Statut: {connection_test['status']}")
    print(f"Message: {connection_test['message']}")
    
    if connection_test['status'] == 'error':
        return False
    
    try:
        # Test de recherche simple
        print("\n=== TEST DE RECHERCHE D'ENTREPRISES ===")
        results = romeo.search_companies(nom="Google", limit=2)
        print(f"Résultats trouvés: {len(results.get('data', []))}")
        
        # Test de statut API
        print("\n=== TEST DE STATUT API ===")
        status = romeo.get_api_status()
        print(f"Statut API: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_romeo_api()
    if success:
        print("\n✅ Tests réussis!")
    else:
        print("\n❌ Tests échoués!")
