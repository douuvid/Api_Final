"""
France Travail API Client Implementation

This module provides a client for interacting with the France Travail (Pôle Emploi) API.
"""

import requests
import time
from typing import Optional, Dict, Any, Callable, TypeVar, cast
from functools import wraps
from datetime import datetime, timedelta

# Définition du type générique pour les fonctions décorées
F = TypeVar('F', bound=Callable[..., Any])


class FranceTravailAPI:
    """Client for the France Travail (Pôle Emploi) API.
    
    This class provides methods to authenticate and interact with the France Travail API.
    It handles OAuth2 authentication and provides methods to search and retrieve job offers.
    
    Args:
        client_id (str): Your France Travail API client ID
        client_secret (str): Your France Travail API client secret
    """
    
    def __init__(self, client_id: str, client_secret: str):
        """
        Initialise le client API France Travail.
        
        Args:
            client_id: Identifiant client de l'application
            client_secret: Clé secrète de l'application
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = None
        self.base_url = "https://api.francetravail.io/partenaire"
        # Nouvelle URL d'authentification
        self.auth_url = "https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
        
        # Gestion des limites de taux d'appel
        self._rate_limits = {
            'offres': {
                'limit': 10,  # appels par seconde
                'last_call': 0,
                'calls': []
            },
            'romeo': {
                'limit': 2,
                'last_call': 0,
                'calls': []
            },
            'bonne_boite': {
                'limit': 2,
                'last_call': 0,
                'calls': []
            },
            'soft_skills': {
                'limit': 1,
                'last_call': 0,
                'calls': []
            }
        }
    
    def _rate_limit(self, api_type: str = 'offres') -> Callable[[F], F]:
        """
        Décoreur pour gérer les limites de taux d'appel.
        
        Args:
            api_type: Type d'API ('offres', 'romeo', 'bonne_boite', 'soft_skills')
            
        Returns:
            Le décorateur à appliquer aux méthodes de l'API
        """
        def decorator(func: F) -> F:
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                # Vérifier et attendre si nécessaire
                self._check_rate_limit(api_type)
                # Appeler la fonction
                return func(self, *args, **kwargs)
            return cast(F, wrapper)
        return decorator
    
    def _check_rate_limit(self, api_type: str):
        """
        Vérifie et applique les limites de taux d'appel.
        
        Args:
            api_type: Type d'API ('offres', 'romeo', 'bonne_boite', 'soft_skills')
        """
        if api_type not in self._rate_limits:
            return
            
        now = time.time()
        limit_info = self._rate_limits[api_type]
        
        # Nettoyer les appaux plus vieux qu'une seconde
        limit_info['calls'] = [t for t in limit_info['calls'] if now - t < 1.0]
        
        # Attendre si nécessaire
        if len(limit_info['calls']) >= limit_info['limit']:
            # Calculer le temps d'attente nécessaire
            oldest_call = limit_info['calls'][0]
            wait_time = 1.0 - (now - oldest_call)
            if wait_time > 0:
                time.sleep(wait_time)
            
            # Nettoyer après l'attente
            now = time.time()
            limit_info['calls'] = [t for t in limit_info['calls'] if now - t < 1.0]
        
        # Enregistrer l'appel
        limit_info['calls'].append(time.time())
        limit_info['last_call'] = now
    
    def is_token_valid(self) -> bool:
        """Vérifie si le token est toujours valide."""
        if not self.access_token or not self.token_expiry:
            return False
        return datetime.now() < self.token_expiry - timedelta(seconds=60)  # Marge de sécurité de 60 secondes

    def authenticate(self) -> bool:
        """Authentification à l'API France Travail avec OAuth2.
        
        Returns:
            bool: True si l'authentification a réussi, False sinon
        """
        # Vérifier si on a déjà un token valide
        if self.is_token_valid():
            return True
            
        # Préparer les données d'authentification
        import base64
        
        # Afficher des informations de débogage
        print(f"🔑 Client ID: {self.client_id[:5]}...{self.client_id[-5:]}")
        
        # Créer l'en-tête d'authentification
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('ascii')
        base64_bytes = base64.b64encode(auth_bytes)
        base64_auth = base64_bytes.decode('ascii')
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {base64_auth}'
        }
        
        # Créer les paramètres d'authentification avec les scopes de base
        data = {
            'grant_type': 'client_credentials',
            'scope': 'api_offresdemploiv2 o2dsoffre'  # Scopes de base
        }
        
        try:
            # Faire la requête d'authentification
            print(f"🔑 Tentative d'authentification avec l'URL: {self.auth_url}")
            print(f"🔑 Headers: {headers}")
            print(f"🔑 Data: {data}")
            
            response = requests.post(
                self.auth_url,
                headers=headers,
                data=data,
                timeout=10,
                allow_redirects=True
            )
            
            # Analyser la réponse
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                expires_in = data.get('expires_in', 3600)  # Par défaut 1h
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                print("✅ Authentification réussie")
                return True
            else:
                print(f"❌ Erreur d'authentification: {response.status_code}")
                print(f"Réponse: {response.text}")
                print(f"Headers de la réponse: {response.headers}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            return False
    
    @_rate_limit('offres')
    def search_jobs(self, params: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
        """Search for job offers.
        
        Args:
            params: Optional dictionary containing search parameters.
                - motsCles: Search keywords
                - commune: INSEE city code
                - distance: Search radius in km
                - typeContrat: Contract type (CDI, CDD, etc.)
                - experience: Required experience level
                - qualification: Qualification level
                - secteurActivite: Business sector
                - entrepriseAdaptee: Adapted company (true/false)
                - range: Pagination (e.g., "0-9" for first 10 results)
                
        Returns:
            Optional[Dict]: Dictionary containing search results or None if an error occurred
        """
        if not self.access_token:
            if not self.authenticate():
                return None
        
        url = f"{self.base_url}/offresdemploi/v2/offres/search"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code in [200, 206]:  # 206 = partial content
                print(f"Réponse API (premiers 500 caractères): {response.text[:500]}...")  # Debug
                return response.json()
            elif response.status_code == 401:  # Token might be expired
                # Try to reauthenticate and retry once
                if self.authenticate():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    response = requests.get(url, headers=headers, params=params)
                    if response.status_code in [200, 206]:
                        print(f"Réponse API après réauthentification: {response.text[:500]}...")  # Debug
                        return response.json()
            
            print(f"Error in job search: {response.status_code}")
            print(f"Headers: {response.headers}")
            print(f"Response: {response.text}")
            return None
                
        except Exception as e:
            print(f"Error during job search: {e}")
            return None
    
    @_rate_limit('offres')
    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """Get details for a specific job offer.
        
        Args:
            job_id: The ID of the job offer to retrieve
            
        Returns:
            Optional[Dict]: Dictionary containing job details or None if an error occurred
        """
        if not self.access_token:
            if not self.authenticate():
                return None
        
        url = f"{self.base_url}/offresdemploi/v2/offres/{job_id}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:  # Token might be expired
                # Try to reauthenticate and retry once
                if self.authenticate():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        return response.json()
            
            print(f"Error getting job details: {response.status_code}")
            print(response.text)
            return None
                
        except Exception as e:
            print(f"Error getting job details: {e}")
            return None
            
    def _get_common_skills(self, job_type: str) -> dict:
        """Retourne les compétences communes par type de métier"""
        return {
            'developpeur': [
                'programmation', 'algorithmes', 'résolution de problèmes',
                'travail d\'équipe', 'communication', 'autonomie', 'adaptabilité',
                'veille technologique', 'anglais technique', 'gestion de version',
                'tests unitaires', 'documentation', 'méthodes agiles'
            ],
            'designer': [
                'créativité', 'sens esthétique', 'maîtrise des outils graphiques',
                'travail d\'équipe', 'communication', 'gestion de projet',
                'veille tendance', 'anglais technique', 'design thinking',
                'prototypage', 'expérience utilisateur (UX)', 'interface utilisateur (UI)'
            ]
        }.get(job_type, [])

    def _simulate_matching(self, rome_code: str, skills: list) -> dict:
        """Simule le matching de compétences localement"""
        # Déterminer le type de métier basé sur le code ROME
        job_type = 'developpeur' if rome_code.startswith('M18') else 'designer'
        common_skills = self._get_common_skills(job_type)
        
        # Nettoyer les compétences en entrée
        skills = [s.lower().strip() for s in skills if s.strip()]
        
        # Calculer les correspondances
        matching_skills = [s for s in skills if s in common_skills]
        missing_skills = [s for s in common_skills if s not in skills]
        
        # Calculer un score de matching (entre 0 et 1)
        score = len(matching_skills) / len(common_skills) if common_skills else 0
        
        # Générer des recommandations
        recommendations = []
        if missing_skills:
            recommendations.append({
                'skill': missing_skills[0],  # Prendre la première compétence manquante
                'suggestion': f"Cette compétence est très demandée pour les postes de {job_type}",
                'importance': 'haute'
            })
        
        return {
            'match_score': round(score, 2),
            'matching_skills': matching_skills,
            'missing_skills': missing_skills[:3],
            'recommendations': recommendations,
            'job_type': job_type,
            'status': 'simulation',
            'source': 'local_simulation'
        }

    @_rate_limit('soft_skills')
    def match_soft_skills(self, rome_code: str, skills: list) -> Dict:
        """Évalue la correspondance entre des compétences et un métier spécifique.
        
        Cette méthode tente d'utiliser l'API France Travail, et en cas d'échec,
        utilise une simulation locale basée sur des compétences prédéfinies.
        
        Args:
            rome_code: Code ROME du métier cible (ex: 'M1805' pour Développeur).
            skills: Liste des compétences à évaluer.
                
        Returns:
            Un dictionnaire contenant les résultats du matching.
            
        Raises:
            ValueError: Si les paramètres d'entrée sont invalides.
        """
        # Validation des entrées
        if not rome_code or not isinstance(rome_code, str) or len(rome_code) != 5 or not rome_code[0].isalpha():
            raise ValueError("Le code ROME doit être une chaîne de 5 caractères commençant par une lettre (ex: 'M1805')")
            
        if not skills or not isinstance(skills, list) or not all(isinstance(skill, str) and skill.strip() for skill in skills):
            raise ValueError("La liste des compétences doit contenir des chaînes de caractères non vides")
        
        # Essayer d'abord avec l'API si on a les crédentiels
        if self.client_id and self.client_secret:
            try:
                # S'assurer qu'on a un token valide
                if not self.is_token_valid() and not self.authenticate():
                    print("⚠️ Impossible de s'authentifier, utilisation de la simulation locale...")
                    return self._simulate_matching(rome_code, skills)
                
                # Préparer l'URL et les en-têtes
                url = f"{self.base_url}/match-soft-skills/v1/match"
                headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-API-Version': 'v1'  # Ajout du header de version
                }
                
                # Afficher les informations de débogage
                print(f"🔍 En-têtes de la requête: {headers}")
                print(f"🔍 URL de la requête: {url}")
                
                # Nettoyer et formater les compétences
                cleaned_skills = [s.strip() for s in skills if s.strip()]
                
                # Préparer les données de la requête
                payload = {
                    'rome_code': rome_code.upper(),
                    'skills': cleaned_skills
                }
                
                print(f"🔍 Envoi de la requête à {url}")
                print(f"🔑 Token: {self.access_token[:20]}...")
                print(f"📄 Données: {payload}")
                
                # Faire la requête
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=15
                )
                
                # Afficher des informations de débogage
                print(f"📡 Code de statut: {response.status_code}")
                print(f"📄 En-têtes de réponse: {dict(response.headers)}")
                
                # Traiter la réponse
                if response.status_code == 200:
                    result = response.json()
                    result['source'] = 'france_travail_api'
                    print("✅ Résultats obtenus depuis l'API France Travail")
                    return result
                    
                # Gérer les erreurs connues
                if response.status_code == 401:
                    print("🔒 Token expiré ou invalide, tentative de renouvellement...")
                    if self.authenticate():  # Essayer de se réauthentifier
                        headers['Authorization'] = f'Bearer {self.access_token}'
                        response = requests.post(
                            url, 
                            headers=headers, 
                            json=payload, 
                            timeout=15
                        )
                        if response.status_code == 200:
                            result = response.json()
                            result['source'] = 'france_travail_api'
                            return result
                
                # Si on arrive ici, il y a eu une erreur
                print(f"⚠️ L'API a retourné une erreur {response.status_code}")
                try:
                    error_details = response.json()
                    print(f"📄 Détails de l'erreur: {error_details}")
                except:
                    print(f"📄 Réponse brute: {response.text[:500]}...")
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Erreur de connexion à l'API: {e}")
            except Exception as e:
                print(f"⚠️ Erreur inattendue lors de l'appel à l'API: {e}")
                import traceback
                print(f"📝 Stack trace: {traceback.format_exc()}")
        else:
            print("ℹ️ Aucune information d'identification fournie, utilisation de la simulation locale")
        
        # En cas d'échec, utiliser la simulation locale
        print("🔄 Utilisation de la simulation locale...")
        return self._simulate_matching(rome_code, skills)
