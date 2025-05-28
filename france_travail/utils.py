"""
Utilitaires pour le client API France Travail.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import textwrap

def format_date(date_str: Optional[str]) -> str:
    """Formate une date ISO en format lisible."""
    if not date_str:
        return "Non spécifiée"
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime('%d/%m/%Y')
    except (ValueError, AttributeError):
        return date_str or "Non spécifiée"

def format_salary(salary_info: Optional[Dict]) -> str:
    """Formate les informations de salaire."""
    if not salary_info:
        return "Non spécifié"
    
    parts = []
    if 'libelle' in salary_info:
        parts.append(salary_info['libelle'])
    if 'commentaire' in salary_info:
        parts.append(f"({salary_info['commentaire']})")
    
    return ' '.join(parts) if parts else "Non spécifié"

def format_competences(competences: Optional[List[Dict]]) -> str:
    """Formate la liste des compétences."""
    if not competences:
        return "Aucune compétence spécifiée"
    return "\n- " + "\n- ".join(comp.get('libelle', '') for comp in competences if comp.get('libelle'))

def format_offre(offre: Dict[str, Any], show_details: bool = False) -> str:
    """
    Formate une offre d'emploi de manière lisible.
    
    Args:
        offre: Dictionnaire contenant les données de l'offre
        show_details: Si True, affiche plus de détails
        
    Returns:
        Chaîne formatée représentant l'offre
    """
    if not offre:
        return "Aucune information sur l'offre"
    
    # En-tête
    output = [
        "=" * 80,
        f"OFFRE: {offre.get('intitule', 'Sans titre').upper()}",
        "=" * 80
    ]
    
    # Informations de base
    infos_base = [
        f"Entreprise: {offre.get('entreprise', {}).get('nom', 'Non spécifié')}",
        f"Lieu: {offre.get('lieuTravail', {}).get('libelle', 'Non spécifié')}",
        f"Type de contrat: {offre.get('typeContrat', 'Non spécifié')}",
        f"Date de publication: {format_date(offre.get('dateCreation'))}",
        f"Salaire: {format_salary(offre.get('salaire'))}",
        f"Expérience: {offre.get('experienceLibelle', 'Non spécifiée')}",
        f"Durée du travail: {offre.get('dureeTravailLibelle', 'Non spécifiée')}"
    ]
    
    output.extend(infos_base)
    
    if show_details:
        # Description détaillée
        description = offre.get('description', '').strip()
        if description:
            wrapped_desc = textwrap.fill(
                description,
                width=78,
                initial_indent="  ",
                subsequent_indent="  ",
                replace_whitespace=False
            )
            output.extend(["\nDESCRIPTION:", wrapped_desc])
        
        # Compétences requises
        competences = offre.get('competences', [])
        if competences:
            output.extend(["\nCOMPÉTENCES REQUISES:", format_competences(competences)])
        
        # Origine de l'offre
        origine = offre.get('origineOffre', {})
        if origine:
            output.extend([
                "\nORIGINE DE L'OFFRE:",
                f"- Origine: {origine.get('origine', 'Non spécifiée')}",
                f"- URL: {origine.get('urlOrigine', 'Non spécifiée')}"
            ])
    
    # Lien vers l'offre
    offre_id = offre.get('id')
    if offre_id:
        output.append(f"\nPOUR POSTULER: https://candidat.pole-emploi.fr/offres/emploi/detail/{offre_id}")
    
    return "\n".join(output)

def afficher_offres(offres: List[Dict], limit: int = 5, show_details: bool = False) -> None:
    """
    Affiche une liste d'offres de manière lisible.
    
    Args:
        offres: Liste des offres à afficher
        limit: Nombre maximum d'offres à afficher
        show_details: Si True, affiche plus de détails pour chaque offre
    """
    if not offres:
        print("Aucune offre trouvée.")
        return
    
    print(f"\n{'='*30} RÉSULTATS ({min(len(offres), limit)}/{len(offres)}) {'='*30}")
    
    for i, offre in enumerate(offres[:limit], 1):
        print(f"\n{'='*5} OFFRE {i} {'='*60}")
        print(format_offre(offre, show_details=show_details))
        print("\n" + "-"*80)
    
    if len(offres) > limit:
        print(f"\n... et {len(offres) - limit} offres supplémentaires (limité à {limit} affichages).")
