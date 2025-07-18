#!/usr/bin/env python3
"""
Module permettant l'intégration du scraper avec la base de données
"""

import os
import sys
import importlib.util

# Détection dynamique du chemin racine du projet
def import_user_database():
    """
    Importe dynamiquement le module UserDatabase depuis la racine du projet
    quelle que soit la profondeur du script appelant
    """
    # Rechercher la racine du projet (où se trouve database/user_database.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    max_depth = 5  # Éviter une boucle infinie
    depth = 0
    root_dir = None
    
    while depth < max_depth:
        # Remonter d'un niveau à chaque itération
        if depth > 0:
            current_dir = os.path.dirname(current_dir)
        
        # Vérifier si le fichier user_database.py existe à ce niveau
        potential_db_path = os.path.join(current_dir, "database", "user_database.py")
        if os.path.exists(potential_db_path):
            root_dir = current_dir
            break
            
        depth += 1
    
    if not root_dir:
        raise ImportError("Impossible de trouver le répertoire racine du projet")
    
    # Ajouter le répertoire racine au chemin Python
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    
    # Importer dynamiquement le module
    from database.user_database import UserDatabase
    
    return UserDatabase
