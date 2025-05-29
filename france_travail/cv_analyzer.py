"""
Module d'analyse de CV

Ce module fournit des fonctions pour analyser des CV au format texte ou binaire (PDF/DOCX).
"""

import re
from typing import Dict, List, Optional, Union
import spacy

# Charger le modèle de langue française
nlp = spacy.load('fr_core_news_sm')

class CVAnalyzer:
    """Classe pour analyser les CV et en extraire les compétences clés"""
    
    def __init__(self):
        # Liste de compétences techniques courantes (à compléter)
        self.technical_skills = {
            'programmation': ['python', 'javascript', 'java', 'c#', 'php', 'ruby', 'go', 'rust'],
            'frontend': ['react', 'angular', 'vue', 'sass', 'css', 'html', 'typescript'],
            'backend': ['node.js', 'django', 'flask', 'spring', 'laravel', 'express'],
            'bdd': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis'],
            'devops': ['docker', 'kubernetes', 'aws', 'azure', 'git', 'ci/cd', 'jenkins'],
            'data': ['pandas', 'numpy', 'tensorflow', 'pytorch', 'machine learning', 'ai']
        }
        
        # Compétences douces courantes
        self.soft_skills = [
            'travail d\'équipe', 'communication', 'leadership', 'gestion du temps',
            'résolution de problèmes', 'créativité', 'adaptabilité', 'autonomie',
            'esprit d\'analyse', 'organisation', 'rigueur', 'curiosité', 'réactivité'
        ]
    
    def extract_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extrait les compétences d'un CV texte"""
        if not text or not isinstance(text, str):
            return {"competences_techniques": [], "competences_douces": []}
        
        text = text.lower()
        
        # Extraire les compétences techniques
        competences_techniques = []
        for category, skills in self.technical_skills.items():
            for skill in skills:
                if re.search(r'\b' + re.escape(skill) + r'\b', text):
                    competences_techniques.append(skill)
        
        # Extraire les compétences douces
        competences_douces = []
        for skill in self.soft_skills:
            if skill in text:
                competences_douces.append(skill)
        
        # Extraire les langues (ex: "Anglais (courant)")
        langues = re.findall(r'([A-Za-zÀ-ÿ]+)\s*\(([^)]+)\)', text)
        if langues:
            competences_douces.extend([f"{lang[0].capitalize()} ({lang[1]})" for lang in langues])
        
        # Nettoyer et dédupliquer
        competences_techniques = list(set(competences_techniques))
        competences_douces = list(set(competences_douces))
        
        return {
            "competences_techniques": competences_techniques,
            "competences_douces": competences_douces,
            "competences_toutes": competences_techniques + competences_douces
        }
    
    def extract_from_pdf(self, file_path: str) -> Dict[str, List[str]]:
        """À implémenter: Extraction de PDF"""
        # TODO: Implémenter l'extraction de texte depuis PDF
        # Pour l'instant, on retourne un dictionnaire vide
        return {"competences_techniques": [], "competences_douces": []}
    
    def extract_from_docx(self, file_path: str) -> Dict[str, List[str]]:
        """À implémenter: Extraction de DOCX"""
        # TODO: Implémenter l'extraction de texte depuis DOCX
        return {"competences_techniques": [], "competences_douces": []}
    
    def analyze(self, input_data: Union[str, bytes], content_type: str = 'text') -> Dict[str, List[str]]:
        """
        Analyse le CV et retourne les compétences
        
        Args:
            input_data: Soit le texte du CV, soit le contenu binaire du fichier
            content_type: 'text', 'pdf', ou 'docx'
            
        Returns:
            Dictionnaire avec les compétences techniques et douces
        """
        if content_type == 'text':
            return self.extract_from_text(input_data)
        elif content_type == 'pdf':
            return self.extract_from_pdf(input_data)
        elif content_type == 'docx':
            return self.extract_from_docx(input_data)
        else:
            raise ValueError("Type de contenu non supporté. Utilisez 'text', 'pdf' ou 'docx'.")

# Fonction utilitaire pour faciliter l'utilisation
analyze_cv = CVAnalyzer().analyze
