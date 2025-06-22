"""
Basic usage example for the France Travail API client.

This script demonstrates how to use the FranceTravailAPI class to search for jobs
and retrieve job details.
"""
import os
from dotenv import load_dotenv
from france_travail import FranceTravailAPI

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API credentials from environment variables
    client_id = os.getenv("FRANCE_TRAVAIL_CLIENT_ID")
    client_secret = os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("Error: Please set FRANCE_TRAVAIL_CLIENT_ID and FRANCE_TRAVAIL_CLIENT_SECRET in .env file")
        return
    
    # Initialize the client
    print("Initializing France Travail API client...")
    api = FranceTravailAPI(client_id, client_secret)
    
    # Authenticate
    print("Authenticating...")
    if not api.authenticate():
        print("Authentication failed. Please check your credentials.")
        return
    
    # Search for jobs
    print("\nSearching for Python developer jobs...")
    search_params = {
        'motsCles': 'développeur python',
        'typeContrat': 'CDI',
        'range': '0-4'  # First 5 results
    }
    
    jobs = api.search_jobs(search_params)
    
    if not jobs:
        print("No jobs found or an error occurred.")
        return
    
    # Display search results
    job_list = jobs.get('resultats', {}).get('offre', [])
    print(f"\nFound {len(job_list)} jobs:")
    
    for i, job in enumerate(job_list, 1):
        print(f"\n--- Job {i} ---")
        print(f"Title: {job.get('intitule')}")
        print(f"Company: {job.get('entreprise', {}).get('nom', 'N/A')}")
        print(f"Location: {job.get('lieuTravail', {}).get('libelle', 'N/A')}")
        print(f"Contract: {job.get('typeContrat', 'N/A')}")
        print(f"ID: {job.get('id')}")
    
    # Get details for the first job
    if job_list:
        first_job_id = job_list[0].get('id')
        print(f"\nFetching details for job ID: {first_job_id}")
        
        job_details = api.get_job_details(first_job_id)
        
        if job_details:
            print("\n--- Job Details ---")
            print(f"Title: {job_details.get('intitule')}")
            print(f"Company: {job_details.get('entreprise', {}).get('nom', 'N/A')}")
            print(f"Location: {job_details.get('lieuTravail', {}).get('libelle', 'N/A')}")
            print(f"Contract: {job_details.get('typeContrat', 'N/A')}")
            print(f"Posted on: {job_details.get('dateCreation', 'N/A')}")
            print(f"Description: {job_details.get('description', 'N/A')[:300]}...")

if __name__ == "__main__":
    main()
