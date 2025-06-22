"""
Tests pour la fonctionnalité de matching par soft skills de l'API France Travail.

Ces tests vérifient que la méthode match_soft_skills fonctionne correctement
avec différents types d'entrées et gère correctement les erreurs.
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Ajouter le répertoire parent au chemin d'import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from france_travail import FranceTravailAPI


class TestSoftSkillsMatching(unittest.TestCase):    
    """Tests pour la fonctionnalité de matching par soft skills."""
    
    def setUp(self):
        """Préparation avant chaque test."""
        self.client_id = "test_client_id"
        self.client_secret = "test_client_secret"
        self.api = FranceTravailAPI(self.client_id, self.client_secret)
        self.api.access_token = "test_access_token"  # Éviter une vraie authentification
    
    @patch('requests.post')
    def test_match_soft_skills_success(self, mock_post):
        """Test un appel réussi à l'API de matching par soft skills."""
        # Configuration du mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "match_score": 0.85,
            "matching_skills": [
                {"name": "communication", "relevance": 0.9},
                {"name": "travail d'équipe", "relevance": 0.8}
            ],
            "missing_skills": [
                {"name": "gestion de projet", "importance": 0.7}
            ],
            "recommendations": [
                "Développez vos compétences en gestion de projet"
            ]
        }
        mock_post.return_value = mock_response
        
        # Appel de la méthode à tester
        rome_code = "M1805"
        skills = ["communication", "travail d'équipe", "autonomie"]
        result = self.api.match_soft_skills(rome_code, skills)
        
        # Vérifications
        self.assertIsNotNone(result)
        self.assertEqual(result["match_score"], 0.85)
        self.assertEqual(len(result["matching_skills"]), 2)
        self.assertEqual(len(result["missing_skills"]), 1)
        self.assertEqual(len(result["recommendations"]), 1)
        
        # Vérification de l'appel API
        expected_url = f"{self.api.base_url}/match-soft-skills/v1/match"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], expected_url)
        self.assertEqual(kwargs['json']['rome_code'], rome_code)
        self.assertEqual(kwargs['json']['skills'], skills)
    
    @patch('requests.post')
    def test_match_soft_skills_unauthorized(self, mock_post):
        """Test la gestion d'une erreur d'authentification."""
        # Configuration du mock pour simuler une erreur 401
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        # Appel de la méthode à tester
        result = self.api.match_soft_skills("M1805", ["communication"])
        
        # Vérification
        self.assertIsNone(result)
    
    def test_match_soft_skills_invalid_input(self):
        """Test la validation des entrées."""
        # Test avec code ROME invalide
        with self.assertRaises(ValueError):
            self.api.match_soft_skills("", ["communication"])
        
        # Test avec liste de compétences vide
        with self.assertRaises(ValueError):
            self.api.match_soft_skills("M1805", [])
        
        # Test avec compétence non-string
        with self.assertRaises(ValueError):
            self.api.match_soft_skills("M1805", ["communication", 123])


if __name__ == "__main__":
    unittest.main()
