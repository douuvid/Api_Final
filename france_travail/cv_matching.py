"""
Système de matching CV avec intégration API France Travail

Ce module fournit une classe pour analyser et faire correspondre les compétences
d'un CV avec les offres d'emploi de l'API France Travail.
"""

import re
import json
import time
from typing import Dict, List, Optional, Any, Counter as CounterType
from datetime import datetime
from collections import Counter
import requests

class CVMatchingService:
    """Service de matching CV utilisant l'API France Travail"""
    
    def __init__(self, client_id: str, client_secret: str):
        """Initialise le service avec les identifiants API.
        
        Args:
            client_id: Identifiant client France Travail
            client_secret: Clé secrète France Travail
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://api.francetravail.io/partenaire"
        self.auth_url = "https://francetravail.io/connexion/oauth2/access_token?realm=%2Fpartenaire"
        
        # Base de données des soft skills avec mots-clés français
        self.soft_skills_db = {
            'communication': {
                'weight': 0.2,
                'keywords': [
                    'communication', 'présentation', 'écoute', 'expression', 'dialogue',
                    'rédaction', 'oral', 'écrit', 'relationnel', 'contact'
                ]
            },
            'leadership': {
                'weight': 0.18,
                'keywords': [
                    'leadership', 'management', 'encadrement', 'direction', 'guide',
                    'chef', 'responsable', 'manager', 'animateur', 'coordinateur'
                ]
            },
            'travail_equipe': {
                'weight': 0.16,
                'keywords': [
                    'équipe', 'collaboration', 'coopération', 'collectif', 'partenariat',
                    'groupe', 'team', 'collaboratif', 'ensemble', 'solidaire'
                ]
            },
            'adaptabilite': {
                'weight': 0.14,
                'keywords': [
                    'adaptation', 'flexibilité', 'polyvalence', 'évolution', 'changement',
                    'flexible', 'polyvalent', 'évolutif', 'mobile', 'agile'
                ]
            },
            'creativite': {
                'weight': 0.12,
                'keywords': [
                    'créativité', 'innovation', 'imagination', 'original', 'inventif',
                    'créatif', 'innovant', 'créatrice', 'inspiration', 'artistique'
                ]
            },
            'resolution_problemes': {
                'weight': 0.1,
                'keywords': [
                    'résolution', 'problème', 'solution', 'analyse', 'diagnostic',
                    'résoudre', 'analyser', 'diagnostiquer', 'investiguer', 'dépannage'
                ]
            },
            'organisation': {
                'weight': 0.1,
                'keywords': [
                    'organisation', 'planification', 'gestion', 'structure', 'méthode',
                    'organisé', 'planifier', 'gérer', 'structurer', 'méthodique'
                ]
            }
        }
    
    def authenticate(self) -> bool:
        """Authentification avec l'API France Travail
        
        Returns:
            bool: True si l'authentification a réussi, False sinon
        """
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'scope': 'o2dsoffre api_offresdemploiv2'
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload_str = '&'.join([f"{k}={v}" for k, v in payload.items()])
        
        try:
            response = requests.post(self.auth_url, headers=headers, data=payload_str, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                return True
            else:
                print(f"Erreur d'authentification: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Erreur de connexion lors de l'authentification: {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"Erreur lors de l'analyse de la réponse d'authentification: {e}")
            return False
    
    def search_similar_jobs(self, job_text: str, limit: int = 10) -> List[Dict]:
        """Recherche d'offres similaires basée sur le texte de l'offre
        
        Args:
            job_text: Texte de l'offre d'emploi
            limit: Nombre maximum d'offres à retourner
            
        Returns:
            Liste des offres d'emploi similaires
        """
        if not self.access_token and not self.authenticate():
            return []
        
        # Extraction des mots-clés de l'offre
        keywords = self._extract_job_keywords(job_text)
        
        url = f"{self.base_url}/offresdemploi/v2/offres/search"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        params = {
            'motsCles': keywords,
            'range': f'0-{limit-1}',
            'sort': '1'  # Tri par pertinence
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            if response.status_code in [200, 206]:
                data = response.json()
                return data.get('resultats', [])
            else:
                print(f"Erreur recherche offres: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"Erreur réseau lors de la recherche d'offres: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Erreur lors de l'analyse de la réponse des offres: {e}")
            return []
    
    def _extract_job_keywords(self, text: str) -> str:
        """Extrait les mots-clés pertinents d'une offre d'emploi
        
        Args:
            text: Texte de l'offre d'emploi
            
        Returns:
            Chaîne de mots-clés séparés par des espaces
        """
        # Mots-clés techniques et métiers communs
        technical_keywords = [
            'développeur', 'developer', 'java', 'python', 'javascript', 'react',
            'angular', 'vue', 'node', 'php', 'sql', 'mysql', 'postgresql',
            'chef de projet', 'project manager', 'scrum', 'agile',
            'commercial', 'vente', 'marketing', 'communication',
            'comptable', 'finance', 'ressources humaines', 'rh'
        ]
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in technical_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        # Limiter à 3-4 mots-clés principaux
        return ' '.join(found_keywords[:4]) if found_keywords else 'emploi'
    
    def extract_soft_skills(self, text: str) -> Dict[str, float]:
        """Extrait et quantifie les soft skills d'un texte
        
        Args:
            text: Texte à analyser (CV ou offre d'emploi)
            
        Returns:
            Dictionnaire des compétences avec leurs scores
        """
        skills_scores = {}
        text_lower = text.lower()
        
        for skill_id, skill_data in self.soft_skills_db.items():
            score = 0
            keywords = skill_data['keywords']
            
            for keyword in keywords:
                # Compte les occurrences du mot-clé
                occurrences = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                score += occurrences * 15  # Chaque occurrence = 15 points
            
            # Normalisation du score (max 100)
            skills_scores[skill_id] = min(score, 100)
        
        return skills_scores
    
    def enrich_skills_with_market_data(self, base_skills: Dict[str, float], market_jobs: List[Dict]) -> Dict[str, float]:
        """Enrichit l'analyse des compétences avec les données du marché
        
        Args:
            base_skills: Compétences de base extraites
            market_jobs: Liste des offres d'emploi du marché
            
        Returns:
            Dictionnaire des compétences enrichi avec les données du marché
        """
        enriched_skills = base_skills.copy()
        
        # Analyse des descriptions d'offres similaires
        market_skills_demand = Counter()
        
        for job in market_jobs:
            description = f"{job.get('description', '')} {job.get('intitule', '')}"
            detected_skills = self.extract_soft_skills(description)
            
            for skill, score in detected_skills.items():
                if score > 20:  # Seuil de pertinence
                    market_skills_demand[skill] += 1
        
        # Ajustement des scores basé sur la demande du marché
        total_jobs = len(market_jobs)
        if total_jobs > 0:
            for skill, demand_count in market_skills_demand.items():
                market_importance = (demand_count / total_jobs) * 100
                
                # Augmente le score si la compétence est très demandée
                if market_importance > 50:
                    enriched_skills[skill] = max(enriched_skills.get(skill, 0), market_importance)
        
        return enriched_skills
    
    def calculate_matching_rate(self, cv_skills: Dict[str, float], job_skills: Dict[str, float]) -> float:
        """Calcule le taux de matching entre CV et offre
        
        Args:
            cv_skills: Compétences extraites du CV
            job_skills: Compétences requises par l'offre
            
        Returns:
            Taux de matching en pourcentage (0-100)
        """
        total_weight = 0
        matching_score = 0
        
        for skill_id, skill_data in self.soft_skills_db.items():
            weight = skill_data['weight']
            cv_score = cv_skills.get(skill_id, 0)
            job_score = job_skills.get(skill_id, 0)
            
            if job_score > 0:  # Compétence demandée
                total_weight += weight
                # Calcul de la compatibilité (entre 0 et 1)
                compatibility = min(cv_score / job_score, 1) if job_score > 0 else 0
                matching_score += compatibility * weight
        
        return (matching_score / total_weight * 100) if total_weight > 0 else 0
    
    def generate_recommendations(self, cv_skills: Dict[str, float], job_skills: Dict[str, float]) -> List[Dict]:
        """Génère des recommandations d'amélioration
        
        Args:
            cv_skills: Compétences du CV
            job_skills: Compétences requises
            
        Returns:
            Liste des recommandations d'amélioration
        """
        recommendations = []
        
        for skill_id, job_score in job_skills.items():
            cv_score = cv_skills.get(skill_id, 0)
            skill_name = skill_id.replace('_', ' ').title()
            
            if job_score > 30 and cv_score < job_score * 0.6:  # Gap significatif
                gap_percentage = ((job_score - cv_score) / job_score) * 100
                
                recommendations.append({
                    'skill': skill_name,
                    'current_score': cv_score,
                    'required_score': job_score,
                    'gap_percentage': gap_percentage,
                    'suggestion': self._get_skill_suggestion(skill_id),
                    'priority': 'high' if gap_percentage > 50 else 'medium'
                })
        
        # Trier par priorité et gap
        recommendations.sort(key=lambda x: (x['priority'] == 'high', x['gap_percentage']), reverse=True)
        return recommendations[:5]  # Top 5 recommandations
    
    def _get_skill_suggestion(self, skill_id: str) -> str:
        """Retourne une suggestion personnalisée pour chaque compétence
        
        Args:
            skill_id: Identifiant de la compétence
            
        Returns:
            Suggestion d'amélioration pour la compétence
        """
        suggestions = {
            'communication': "Mettez en avant vos expériences de présentation, négociation ou relation client",
            'leadership': "Soulignez vos expériences d'encadrement, de coordination d'équipe ou de projet",
            'travail_equipe': "Décrivez vos projets collaboratifs et votre capacité à travailler en groupe",
            'adaptabilite': "Montrez votre capacité à évoluer dans différents environnements ou secteurs",
            'creativite': "Valorisez vos initiatives, innovations ou solutions originales apportées",
            'resolution_problemes': "Illustrez avec des exemples concrets de problèmes résolus",
            'organisation': "Démontrez vos compétences en planification et gestion de priorités"
        }
        return suggestions.get(skill_id, "Développez cette compétence dans votre présentation")
    
    def analyze_cv_job_match(self, cv_text: str, job_text: str) -> Dict[str, Any]:
        """Analyse complète du matching CV-offre avec données marché
        
        Args:
            cv_text: Texte du CV
            job_text: Texte de l'offre d'emploi
            
        Returns:
            Dictionnaire contenant les résultats de l'analyse
        """
        # Extraction des compétences de base
        cv_skills = self.extract_soft_skills(cv_text)
        job_skills = self.extract_soft_skills(job_text)
        
        # Recherche d'offres similaires pour enrichir l'analyse
        similar_jobs = self.search_similar_jobs(job_text, limit=5)
        
        # Enrichissement avec données marché
        enriched_job_skills = self.enrich_skills_with_market_data(job_skills, similar_jobs)
        
        # Calcul du taux de matching
        matching_rate = self.calculate_matching_rate(cv_skills, enriched_job_skills)
        
        # Génération des recommandations
        recommendations = self.generate_recommendations(cv_skills, enriched_job_skills)
        
        # Insights marché
        market_insights = {
            'similar_jobs_found': len(similar_jobs),
            'top_demanded_skills': self._get_top_market_skills(similar_jobs),
            'market_trend': 'high' if len(similar_jobs) > 10 else 'medium'
        }
        
        return {
            'matching_rate': round(matching_rate, 1),
            'cv_skills': cv_skills,
            'job_skills': enriched_job_skills,
            'recommendations': recommendations,
            'market_insights': market_insights,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _get_top_market_skills(self, jobs: List[Dict]) -> List[str]:
        """Identifie les compétences les plus demandées sur le marché
        
        Args:
            jobs: Liste des offres d'emploi
            
        Returns:
            Liste des compétences les plus demandées
        """
        skill_demand = Counter()
        
        for job in jobs:
            description = f"{job.get('description', '')} {job.get('intitule', '')}"
            detected_skills = self.extract_soft_skills(description)
            
            for skill, score in detected_skills.items():
                if score > 20:
                    skill_demand[skill] += 1
        
        return [skill.replace('_', ' ').title() for skill, _ in skill_demand.most_common(3)]


def analyze_cv_job_match(cv_text: str, job_text: str, client_id: str, client_secret: str) -> Dict[str, Any]:
    """Fonction utilitaire pour analyser la correspondance CV-offre
    
    Args:
        cv_text: Texte du CV
        job_text: Texte de l'offre d'emploi
        client_id: Identifiant client France Travail
        client_secret: Clé secrète France Travail
        
    Returns:
        Dictionnaire contenant les résultats de l'analyse
    """
    service = CVMatchingService(client_id, client_secret)
    return service.analyze_cv_job_match(cv_text, job_text)
