"""
Package database - Gestion de la base de données de l'application de recherche d'emploi.

Ce package contient les modules pour interagir avec la base de données PostgreSQL,
y compris la gestion des utilisateurs, des profils, des compétences, etc.
"""

from .user_database import UserDatabase
from .config import DatabaseConfig

__all__ = ['UserDatabase', 'DatabaseConfig']
