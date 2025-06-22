"""
Client France Travail utilisant les APIs ROME 4.0.

Ce module utilise les nouvelles APIs ROME 4.0 pour :
- Récupérer les compétences référentielles
- Analyser les métiers et leurs exigences
- Effectuer un matching précis des compétences
- Accéder aux contextes de travail et fiches métiers
"""

import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re

class FranceTravailROME4API:
    """
    Client pour les APIs ROME 4.0 de France Travail.
    Utilise les endpoints spécialisés pour les compétences et métiers.
    """
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = None
        
        # URLs pour ROME 4.0
        self.auth_url = "https://entreprise.pole-emploi.fr/connexion/oauth2/access_token"
        self.base_url = "https://api.francetravail.io/partenaire"
        
        # Endpoints ROME 4.0
        self.endpoints = {
            'competences': '/rome4/v1/competence',
            'metiers': '/rome4/v1/metier',
            'contextes': '/rome4/v1/contexte',
            'fiches': '/rome4/v1/fiche'
        }
        
        # Cache pour optimiser les performances
        self.cache = {
            'competences': {},
            'metiers': {},
            'contextes': {},
            'fiches': {}
        }
    
    def authenticate(self) -> bool:
        """Authentification avec les scopes ROME 4.0."""
        import base64
        
        if self.is_token_valid():
            return True
        
        auth_string = f"{self.client_id}:{self.client_secret}"
        base64_auth = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {base64_auth}',
            'Accept': 'application/json'
        }
        
        # Scopes pour ROME 4.0
        data = {
            'grant_type': 'client_credentials',
            'scope': 'api_rome-metiersv1 api_rome-competencesv1 api_rome-contextesv1 api_rome-fichesv1',
            'realm': '/partenaire'
        }
        
        try:
            response = requests.post(
                f"{self.auth_url}?realm=%2Fpartenaire",
                headers=headers,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
                print("✅ Authentification ROME 4.0 réussie")
                return True
            else:
                print(f"❌ Erreur d'authentification: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception authentification: {e}")
        
        return False
    
    def is_token_valid(self) -> bool:
        """Vérifie la validité du token."""
        if not self.access_token or not self.token_expiry:
            return False
        return datetime.now() < self.token_expiry
    
    def get_competences_referentiel(self, limit: int = 100) -> List[Dict]:
        """
        Récupère la liste des compétences du référentiel ROME 4.0.
        """
        if not self.authenticate():
            return []
        
        cache_key = f"competences_ref_{limit}"
        if cache_key in self.cache['competences']:
            return self.cache['competences'][cache_key]
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        try:
            url = f"{self.base_url}{self.endpoints['competences']}"
            params = {'limit': limit} if limit else {}
            
            print(f"🔍 Récupération du référentiel compétences (limit: {limit})")
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                competences = data if isinstance(data, list) else data.get('competences', [])
                self.cache['competences'][cache_key] = competences
                print(f"✅ Récupéré {len(competences)} compétences du référentiel")
                return competences
            else:
                print(f"❌ Erreur récupération compétences: {response.status_code}")
                print(f"Response: {response.text[:300]}...")
                
        except Exception as e:
            print(f"❌ Exception compétences: {e}")
        
        return []
    
    def get_metier_details(self, rome_code: str) -> Dict:
        """
        Récupère les détails d'un métier via l'API ROME 4.0.
        """
        if not self.authenticate():
            return {}
        
        if rome_code in self.cache['metiers']:
            return self.cache['metiers'][rome_code]
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        try:
            url = f"{self.base_url}{self.endpoints['metiers']}/{rome_code.upper()}"
            
            print(f"🔍 Récupération détails métier {rome_code}")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                metier_data = response.json()
                self.cache['metiers'][rome_code] = metier_data
                print(f"✅ Détails métier {rome_code} récupérés")
                return metier_data
            else:
                print(f"❌ Erreur métier {rome_code}: {response.status_code}")
                print(f"Response: {response.text[:300]}...")
                
        except Exception as e:
            print(f"❌ Exception métier {rome_code}: {e}")
        
        return {}
    
    def get_fiche_metier(self, rome_code: str) -> Dict:
        """
        Récupère la fiche métier complète avec compétences organisées.
        """
        if not self.authenticate():
            return {}
        
        cache_key = f"fiche_{rome_code}"
        if cache_key in self.cache['fiches']:
            return self.cache['fiches'][cache_key]
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        try:
            url = f"{self.base_url}{self.endpoints['fiches']}/{rome_code.upper()}"
            
            print(f"🔍 Récupération fiche métier {rome_code}")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                fiche_data = response.json()
                self.cache['fiches'][cache_key] = fiche_data
                print(f"✅ Fiche métier {rome_code} récupérée")
                return fiche_data
            else:
                print(f"❌ Erreur fiche {rome_code}: {response.status_code}")
                print(f"Response: {response.text[:300]}...")
                
        except Exception as e:
            print(f"❌ Exception fiche {rome_code}: {e}")
        
        return {}
    
    def get_contextes_travail(self, rome_code: str) -> List[Dict]:
        """
        Récupère les contextes de travail pour un métier.
        """
        if not self.authenticate():
            return []
        
        cache_key = f"contextes_{rome_code}"
        if cache_key in self.cache['contextes']:
            return self.cache['contextes'][cache_key]
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        try:
            url = f"{self.base_url}{self.endpoints['contextes']}"
            params = {'codeRome': rome_code.upper()}
            
            print(f"🔍 Récupération contextes travail {rome_code}")
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                contextes_data = response.json()
                contextes = contextes_data if isinstance(contextes_data, list) else contextes_data.get('contextes', [])
                self.cache['contextes'][cache_key] = contextes
                print(f"✅ {len(contextes)} contextes récupérés pour {rome_code}")
                return contextes
            else:
                print(f"❌ Erreur contextes {rome_code}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception contextes {rome_code}: {e}")
        
        return []
    
    def extract_competences_from_metier(self, rome_code: str) -> Dict[str, List[str]]:
        """
        Extrait les compétences structurées d'un métier ROME 4.0.
        Retourne un dictionnaire avec savoir, savoir-faire, savoir-être.
        """
        print(f"🔍 Extraction compétences structurées pour {rome_code}")
        
        # Récupération via fiche métier (plus complète)
        fiche = self.get_fiche_metier(rome_code)
        metier = self.get_metier_details(rome_code)
        
        competences_structurees = {
            'savoir': [],
            'savoir_faire': [],
            'savoir_etre': [],
            'competences_transverses': []
        }
        
        # Extraction depuis la fiche métier
        if fiche:
            # Structure possible des compétences dans ROME 4.0
            competences_sections = [
                'savoirs', 'savoir', 'connaissances',
                'savoirFaire', 'savoir_faire', 'competencesTechniques',
                'savoirEtre', 'savoir_etre', 'competencesComportementales',
                'competences', 'competencesTransverses'
            ]
            
            for section in competences_sections:
                if section in fiche:
                    items = fiche[section]
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                libelle = item.get('libelle') or item.get('nom') or item.get('designation')
                                if libelle:
                                    if 'savoir' in section.lower() and 'faire' not in section.lower():
                                        competences_structurees['savoir'].append(libelle)
                                    elif 'faire' in section.lower():
                                        competences_structurees['savoir_faire'].append(libelle)
                                    elif 'etre' in section.lower() or 'comportement' in section.lower():
                                        competences_structurees['savoir_etre'].append(libelle)
                                    else:
                                        competences_structurees['competences_transverses'].append(libelle)
                            elif isinstance(item, str):
                                competences_structurees['competences_transverses'].append(item)
        
        # Extraction depuis métier si fiche insuffisante
        if metier and not any(competences_structurees.values()):
            # Parcours des structures possibles
            for key, value in metier.items():
                if 'competence' in key.lower() or 'savoir' in key.lower():
                    if isinstance(value, list):
                        for comp in value:
                            if isinstance(comp, dict):
                                libelle = comp.get('libelle') or comp.get('nom')
                                if libelle:
                                    competences_structurees['competences_transverses'].append(libelle)
        
        # Nettoyage et déduplication
        for category in competences_structurees:
            competences_structurees[category] = list(set([
                comp.strip() for comp in competences_structurees[category] 
                if comp and len(comp.strip()) > 2
            ]))
        
        total_competences = sum(len(comps) for comps in competences_structurees.values())
        print(f"✅ {total_competences} compétences extraites pour {rome_code}")
        
        return competences_structurees
    
    def match_competences_rome4(self, rome_code: str, user_skills: List[str]) -> Dict:
        """
        Matching avancé utilisant les données structurées ROME 4.0.
        """
        print(f"🎯 Matching ROME 4.0 pour {rome_code}")
        
        # 1. Récupération des compétences du métier
        metier_competences = self.extract_competences_from_metier(rome_code)
        
        if not any(metier_competences.values()):
            print("⚠️ Pas de compétences ROME 4.0, fallback simulation")
            return self._simulate_matching(rome_code, user_skills)
        
        # 2. Préparation des données
        user_skills_lower = [skill.lower().strip() for skill in user_skills]
        
        # 3. Matching par catégorie
        matches_by_category = {
            'savoir': [],
            'savoir_faire': [],
            'savoir_etre': [],
            'competences_transverses': []
        }
        
        weights = {
            'savoir': 1.0,
            'savoir_faire': 1.2,  # Plus important
            'savoir_etre': 0.8,
            'competences_transverses': 1.0
        }
        
        total_weighted_score = 0
        total_weight = 0
        
        for category, rome_competences in metier_competences.items():
            if not rome_competences:
                continue
                
            rome_competences_lower = [comp.lower().strip() for comp in rome_competences]
            category_matches = []
            
            for user_skill in user_skills_lower:
                for rome_comp in rome_competences_lower:
                    # Matching exact et partiel
                    if (user_skill == rome_comp or 
                        user_skill in rome_comp or 
                        rome_comp in user_skill or
                        self._similarity_score(user_skill, rome_comp) > 0.7):
                        category_matches.append(user_skill)
                        break
            
            matches_by_category[category] = list(set(category_matches))
            
            # Calcul score pondéré pour cette catégorie
            if user_skills:
                category_score = len(category_matches) / len(user_skills)
                total_weighted_score += category_score * weights[category]
                total_weight += weights[category]
        
        # 4. Score global
        final_score = total_weighted_score / total_weight if total_weight > 0 else 0
        
        # 5. Compétences manquantes prioritaires
        all_matches = set()
        for matches in matches_by_category.values():
            all_matches.update(matches)
        
        missing_skills = []
        for category, rome_competences in metier_competences.items():
            for rome_comp in rome_competences[:3]:  # Top 3 par catégorie
                if not any(match in rome_comp.lower() or rome_comp.lower() in match 
                          for match in all_matches):
                    missing_skills.append(f"{rome_comp} ({category})")
        
        # 6. Contextes de travail
        contextes = self.get_contextes_travail(rome_code)
        
        result = {
            'match_score': round(min(final_score, 1.0), 2),
            'matches_by_category': matches_by_category,
            'total_matches': len(all_matches),
            'metier_competences': metier_competences,
            'missing_skills': missing_skills[:8],
            'contextes_travail': [ctx.get('libelle', '') for ctx in contextes[:5]],
            'rome_code': rome_code.upper(),
            'source': 'rome_4.0_api',
            'timestamp': datetime.now().isoformat(),
            'api_version': '4.0'
        }
        
        print(f"✅ Score final: {final_score:.2f}")
        print(f"📊 {len(all_matches)} compétences matchées sur {len(user_skills)}")
        
        return result
    
    def _similarity_score(self, str1: str, str2: str) -> float:
        """Calcul de similarité simple entre deux chaînes."""
        if not str1 or not str2:
            return 0.0
        
        # Jaccard similarity sur les mots
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _simulate_matching(self, rome_code: str, skills: List[str]) -> Dict:
        """Fallback en cas d'échec des APIs ROME 4.0."""
        print("🔄 Utilisation du fallback simulé")
        
        skills_by_rome = {
            'M1805': {
                'savoir': ['Algorithmique', 'Bases de données', 'Langages de programmation'],
                'savoir_faire': ['Développer une application', 'Tester un programme', 'Déboguer du code'],
                'savoir_etre': ['Rigueur', 'Curiosité technique', 'Travail en équipe']
            },
            'M1806': {
                'savoir': ['HTML/CSS', 'Design graphique', 'UX/UI'],
                'savoir_faire': ['Créer une interface', 'Optimiser UX', 'Intégrer du contenu'],
                'savoir_etre': ['Créativité', 'Sens esthétique', 'Adaptabilité']
            }
        }
        
        expected = skills_by_rome.get(rome_code.upper(), {
            'savoir': ['Connaissances métier'],
            'savoir_faire': ['Techniques professionnelles'],
            'savoir_etre': ['Communication', 'Autonomie']
        })
        
        user_skills_lower = [s.lower() for s in skills]
        matches = []
        
        for category_skills in expected.values():
            for exp_skill in category_skills:
                if any(user_skill in exp_skill.lower() or exp_skill.lower() in user_skill 
                       for user_skill in user_skills_lower):
                    matches.append(exp_skill)
        
        score = len(matches) / len(skills) if skills else 0
        
        return {
            'match_score': round(score, 2),
            'matching_skills': matches,
            'expected_competences': expected,
            'rome_code': rome_code.upper(),
            'source': 'simulation_rome4',
            'api_version': '4.0_fallback'
        }
