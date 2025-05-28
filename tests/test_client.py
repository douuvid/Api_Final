"""
Tests for the FranceTravailAPI client.
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from france_travail import FranceTravailAPI

class TestFranceTravailAPI(unittest.TestCase):
    """Test cases for FranceTravailAPI."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client_id = "test_client_id"
        self.client_secret = "test_client_secret"
        self.api = FranceTravailAPI(self.client_id, self.client_secret)
    
    @patch('requests.post')
    def test_authenticate_success(self, mock_post):
        """Test successful authentication."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'token_type': 'bearer',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response
        
        # Call the method
        result = self.api.authenticate()
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(self.api.access_token, 'test_access_token')
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_authenticate_failure(self, mock_post):
        """Test failed authentication."""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_post.return_value = mock_response
        
        # Call the method
        result = self.api.authenticate()
        
        # Assertions
        self.assertFalse(result)
        self.assertIsNone(self.api.access_token)
    
    @patch('requests.get')
    @patch.object(FranceTravailAPI, 'authenticate')
    def test_search_jobs_success(self, mock_authenticate, mock_get):
        """Test successful job search."""
        # Setup
        self.api.access_token = 'test_token'
        mock_authenticate.return_value = True
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'resultats': {
                'offre': [
                    {'id': '1', 'intitule': 'Développeur Python'},
                    {'id': '2', 'intitule': 'Data Scientist'}
                ],
                'totalCount': 2
            }
        }
        mock_get.return_value = mock_response
        
        # Call the method
        params = {'motsCles': 'python'}
        result = self.api.search_jobs(params)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(len(result['resultats']['offre']), 2)
        mock_get.assert_called_once()
    
    @patch('requests.get')
    @patch.object(FranceTravailAPI, 'authenticate')
    def test_get_job_details_success(self, mock_authenticate, mock_get):
        """Test successful job details retrieval."""
        # Setup
        self.api.access_token = 'test_token'
        mock_authenticate.return_value = True
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': '123',
            'intitule': 'Développeur Python Senior',
            'description': 'Description du poste...',
            'entreprise': {'nom': 'Acme Inc'},
            'lieuTravail': {'libelle': 'Paris (75)'},
            'typeContrat': 'CDI',
            'dateCreation': '2025-05-28T10:00:00Z'
        }
        mock_get.return_value = mock_response
        
        # Call the method
        job_id = '123'
        result = self.api.get_job_details(job_id)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['intitule'], 'Développeur Python Senior')
        mock_get.assert_called_once()

if __name__ == '__main__':
    unittest.main()
