"""
Client alternatif pour l'API France Travail.

Ce module fournit une implémentation alternative qui utilise les API disponibles
de France Travail pour effectuer du matching de compétences basé sur l'analyse
des offres d'emploi.
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re

class FranceTravailAlternativeAPI:
    """
    Solution alternative utilisant les APIs disponibles de France Travail
    pour créer un système de matching des compétences.
    """
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = None
        
        # URLs confirmées comme fonctionnelles
        self.auth_url = "https://entreprise.pole-emploi.fr/connexion/oauth2/access_token"
        self.base_url = "https://api.francetravail.io/partenaire"
        
        # Cache pour éviter les appels répétés
        self.cache = {
            'metiers': {},
            'appellations': {},
            'competences': {}
        }
    
    def authenticate(self) -> bool:
        """Authentification avec le scope qui fonctionne."""
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
        
        data = {
            'grant_type': 'client_credentials',
            'scope': 'api_offresdemploiv2 o2dsoffre',
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
                from datetime import datetime, timedelta
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
                print("✅ Authentification réussie")
                return True
            else:
                print(f"❌ Erreur d'authentification: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        return False
    
    def is_token_valid(self) -> bool:
        """Vérifie la validité du token."""
        if not self.access_token or not self.token_expiry:
            return False
        return datetime.now() < self.token_expiry
    
    def get_job_details_by_rome(self, rome_code: str) -> Dict:
        """
        Récupère les détails d'un métier via le code ROME.
        Utilise les APIs disponibles pour construire un profil de compétences.
        """
        if not self.authenticate():
            return {}
        
        if rome_code in self.cache['metiers']:
            return self.cache['metiers'][rome_code]
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        # Essayons plusieurs endpoints pour récupérer des infos
        job_data = {}
        
        # 1. Essai avec l'API des offres (pour récupérer des exemples)
        try:
            search_url = f"{self.base_url}/offresdemploi/v2/offres/search"
            # Paramètres de base pour la recherche
            params = {
                'codeROME': rome_code,
                'range': '0-9'  # Limite à 10 résultats
            }
            
            # Ajout des headers nécessaires
            headers.update({
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            })
            
            print(f"🔍 Recherche d'offres pour ROME {rome_code}...")
            response = requests.get(search_url, headers=headers, params=params, timeout=15)
            
            # Gestion des réponses partielles (206) et complètes (200)
            if response.status_code in (200, 206):
                try:
                    offers_data = response.json()
                    job_data['offers_sample'] = offers_data.get('resultats', [])
                    
                    if response.status_code == 206:
                        print(f"⚠️ Réponse partielle (206) - {len(job_data['offers_sample'])} offres récupérées pour {rome_code}")
                    else:
                        print(f"✅ Récupéré {len(job_data['offers_sample'])} offres pour {rome_code}")
                    
                    # Si pas d'offres, essayer sans le code ROME pour élargir la recherche
                    if not job_data['offers_sample']:
                        print("⚠️ Aucune offre avec ce code ROME, élargissement de la recherche...")
                        del params['codeROME']
                        response = requests.get(search_url, headers=headers, params=params, timeout=15)
                        if response.status_code in (200, 206):
                            try:
                                offers_data = response.json()
                                job_data['offers_sample'] = offers_data.get('resultats', [])
                                print(f"✅ Récupéré {len(job_data['offers_sample'])} offres (recherche élargie)")
                            except Exception as e:
                                print(f"❌ Erreur décodage JSON (recherche élargie): {e}")
                except Exception as e:
                    print(f"❌ Erreur décodage JSON: {e}")
                    job_data['offers_sample'] = []
            else:
                print(f"⚠️ Erreur API: {response.status_code} - {response.text[:200]}")
                job_data['offers_sample'] = []
                
        except Exception as e:
            print(f"❌ Erreur récupération offres: {e}")
        
        # Cache le résultat
        self.cache['metiers'][rome_code] = job_data
        return job_data
    
    def extract_skills_from_offers(self, offers: List[Dict]) -> List[str]:
        """
        Extrait les compétences mentionnées dans les offres d'emploi.
        """
        import re
        from collections import Counter
        
        # Dictionnaire de compétences techniques avec leurs variantes
        tech_skills = {
            'python': ['python', 'django', 'flask', 'pandas', 'numpy', 'pytorch'],
            'javascript': ['javascript', 'js', 'ecmascript', 'typescript', 'ts', 'react', 'angular', 'vue', 'node', 'express'],
            'java': ['java', 'spring', 'hibernate', 'j2ee', 'jsp', 'junit'],
            'sql': ['sql', 'mysql', 'postgresql', 'oracle', 'sql server', 'pl/sql', 't-sql'],
            'devops': ['docker', 'kubernetes', 'jenkins', 'gitlab ci', 'github actions', 'ansible', 'terraform'],
            'cloud': ['aws', 'azure', 'gcp', 'google cloud', 'amazon web services'],
            'mobile': ['android', 'ios', 'swift', 'kotlin', 'react native', 'flutter'],
            'data': ['big data', 'data science', 'machine learning', 'ai', 'artificial intelligence', 'tensorflow'],
            'web': ['html', 'css', 'sass', 'less', 'bootstrap', 'responsive design'],
            'agile': ['scrum', 'kanban', 'sprint', 'agile', 'safe']
        }
        
        # Compétences douces (soft skills)
        soft_skills = [
            'communication', 'leadership', 'travail d\'équipe', 'autonomie',
            'rigueur', 'organisation', 'créativité', 'adaptation', 'initiative',
            'relationnel', 'analyse', 'synthèse', 'négociation', 'pédagogie',
            'gestion du stress', 'résolution de problèmes', 'esprit critique',
            'curiosité', 'flexibilité', 'résilience', 'empathie', 'intelligence émotionnelle'
        ]
        
        # Initialiser les compteurs
        skill_counter = Counter()
        
        for offer in offers:
            # Préparation du texte à analyser
            description = str(offer.get('description', '')).lower()
            title = str(offer.get('intitule', '')).lower()
            full_text = f"{title} {description}"
            
            # Nettoyage du texte
            full_text = re.sub(r'[^\w\s]', ' ', full_text)  # Supprimer la ponctuation
            
            # Recherche des compétences techniques
            for main_skill, variants in tech_skills.items():
                for variant in variants:
                    if re.search(r'\b' + re.escape(variant) + r'\b', full_text):
                        skill_counter[main_skill] += 1
                        break  # On compte chaque compétence principale une seule fois par offre
            
            # Recherche des compétences douces
            for skill in soft_skills:
                if re.search(r'\b' + re.escape(skill) + r'\b', full_text):
                    skill_counter[skill] += 1
        
        # Sélectionner les compétences les plus fréquentes
        most_common = skill_counter.most_common(15)  # Top 15 des compétences
        
        # Formater le résultat
        skills = [skill for skill, count in most_common if count > 0]
        
        # Si pas assez de compétences, ajouter des compétences par défaut
        if len(skills) < 5:
            default_skills = ['communication', 'travail d\'équipe', 'autonomie', 'rigueur', 'anglais']
            for skill in default_skills:
                if skill not in skills:
                    skills.append(skill)
        
        return skills[:10]  # Retourne au maximum 10 compétences
        
        return list(skills)
    
    def match_soft_skills(self, rome_code: str, user_skills: List[str]) -> Dict:
        """
        Implémentation améliorée du matching des compétences.
        Utilise les données d'offres d'emploi pour déterminer les compétences requises.
        """
        
        print(f"🔍 Matching des compétences pour {rome_code}")
        
        # 1. Récupérer les données du métier
        job_data = self.get_job_details_by_rome(rome_code)
        
        if not job_data.get('offers_sample'):
            print("⚠️ Pas de données d'offres, utilisation de la simulation")
            return self._simulate_matching(rome_code, user_skills)
        
        # 2. Extraire les compétences des offres
        market_skills = self.extract_skills_from_offers(job_data['offers_sample'])
        
        if not market_skills:
            print("⚠️ Pas de compétences extraites, utilisation de la simulation")
            return self._simulate_matching(rome_code, user_skills)
        
        # 3. Normaliser les compétences
        user_skills_lower = [skill.lower().strip() for skill in user_skills if skill.strip()]
        market_skills_lower = [skill.lower().strip() for skill in market_skills if skill.strip()]
        
        # 4. Calculer les correspondances avec un seuil de similarité
        matches = []
        missing_skills = []
        
        # Pour chaque compétence du marché, vérifier si elle est couverte par l'utilisateur
        for market_skill in market_skills_lower:
            matched = False
            
            for user_skill in user_skills_lower:
                # Vérifier la similarité avec la distance de Levenshtein
                if self._similarity_score(user_skill, market_skill) > 0.7:  # Seuil de similarité de 70%
                    matches.append({
                        'competence': market_skill,
                        'niveau': 'fort' if user_skill == market_skill else 'moyen',
                        'correspondance': user_skill
                    })
                    matched = True
                    break
            
            if not matched:
                missing_skills.append(market_skill)
        
        # 5. Calculer le score global
        total_skills = len(market_skills_lower)
        matched_count = len(matches)
        
        if total_skills > 0:
            match_score = min(matched_count / total_skills, 1.0)  # Score entre 0 et 1
        else:
            match_score = 0.0
        
        # 6. Préparer le résultat
        result = {
            'match_score': round(match_score, 2),
            'total_skills': total_skills,
            'matched_skills': matched_count,
            'matches': matches,
            'missing_skills': missing_skills[:5],  # Limiter à 5 compétences manquantes
            'rome_code': rome_code,
            'source': 'api_offres_analysees',
        }
        
        print(f"✅ Score de correspondance: {match_score*100:.1f}% ({matched_count}/{total_skills} compétences)")
        
        return result
        return result
    
    def _similarity_score(self, str1: str, str2: str) -> float:
        """
        Calcule la similarité entre deux chaînes en utilisant la distance de Levenshtein.
        Retourne un score entre 0.0 (pas de similarité) et 1.0 (chaînes identiques).
        """
        if not str1 or not str2:
            return 0.0
            
        # Convertir en minuscules pour la comparaison insensible à la casse
        str1 = str1.lower()
        str2 = str2.lower()
        
        # Si les chaînes sont identiques, similarité parfaite
        if str1 == str2:
            return 1.0
            
        # Si une chaîne est vide et pas l'autre, similarité nulle
        if not str1 or not str2:
            return 0.0
            
        # Calcul de la distance de Levenshtein
        def levenshtein_distance(s1, s2):
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
                
            if len(s2) == 0:
                return len(s1)
                
            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
                
            return previous_row[-1]
        
        distance = levenshtein_distance(str1, str2)
        max_len = max(len(str1), len(str2))
        
        # Calcul du score de similarité (0.0 à 1.0)
        if max_len == 0:
            return 1.0
            
        return 1.0 - (distance / max_len)
        
    def _simulate_matching(self, rome_code: str, skills: List[str]) -> Dict:
        """Simulation locale améliorée basée sur des données réelles."""
        
        # Base de données simplifiée par métier
        skills_by_rome = {
            'M1805': ['python', 'java', 'sql', 'javascript', 'git', 'travail d\'équipe', 'analyse'],
            'M1806': ['html', 'css', 'javascript', 'ux/ui', 'photoshop', 'créativité'],
            'M1810': ['project management', 'agile', 'scrum', 'leadership', 'communication'],
            'E1103': ['vente', 'relationnel', 'négociation', 'communication', 'autonomie'],
        }
        
        expected_skills = skills_by_rome.get(rome_code.upper(), 
                                           ['communication', 'travail d\'équipe', 'autonomie'])
        
        user_skills_lower = [s.lower() for s in skills]
        expected_skills_lower = [s.lower() for s in expected_skills]
        
        matches = [skill for skill in user_skills_lower 
                  if any(exp in skill or skill in exp for exp in expected_skills_lower)]
        
        score = len(matches) / len(skills) if skills else 0
        
        return {
            'match_score': round(score, 2),
            'matching_skills': matches,
            'expected_skills': expected_skills,
            'rome_code': rome_code.upper(),
            'source': 'simulation_enrichie',
            'timestamp': datetime.now().isoformat()
        }


def test_alternative_api():
    """Test de l'API alternative."""
    
    api = FranceTravailAlternativeAPI(
        client_id="PAR_cv_9137520f2b833ef0ce2913e412a819ddf8191bb97dd1b09f1a20f0e21c451deb",
        client_secret="cbc8a7310a011f18566360ce3865c7bffa995b11acc18b5ab844a61bc7954050"
    )
    
    print("=== TEST DE L'API ALTERNATIVE ===")
    
    # Test du matching
    result = api.match_soft_skills(
        rome_code="M1805",  # Développeur
        user_skills=["python", "travail d'équipe", "javascript", "communication"]
    )
    
    print("\n📊 RÉSULTAT DU MATCHING:")
    print(f"Score: {result['match_score']}")
    print(f"Compétences matchées: {result['matching_skills']}")
    print(f"Source: {result['source']}")
    
    if 'offers_analyzed' in result:
        print(f"Offres analysées: {result['offers_analyzed']}")
    
    return result


if __name__ == "__main__":
    test_alternative_api()