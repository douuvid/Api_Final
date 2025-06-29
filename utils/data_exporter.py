import csv
import os
from datetime import datetime

def export_to_csv(user_email, data_to_export, report_type='report', subdirectory=None):
    """
    Exporte les données dans un fichier CSV propre à l'utilisateur.
    Le fichier est nommé avec l'email, le type de rapport et la date/heure.
    Peut sauvegarder dans un sous-dossier de 'reports'.
    """
    if not data_to_export:
        print("\nAucune nouvelle donnée à exporter.")
        return

    headers = list(data_to_export[0].keys())

    # Construire le chemin du répertoire de base des rapports
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_reports_dir = os.path.join(project_root, 'reports')

    # Ajouter le sous-dossier si spécifié
    final_reports_dir = os.path.join(base_reports_dir, subdirectory) if subdirectory else base_reports_dir
    os.makedirs(final_reports_dir, exist_ok=True)

    # Nettoyer l'email pour l'utiliser dans le nom de fichier
    safe_email = user_email.replace('@', '_').replace('.', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{report_type}_{safe_email}_{timestamp}.csv"
    filepath = os.path.join(final_reports_dir, filename)

    print(f"\nExportation des données vers {filepath}...")

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data_to_export)
        print(f"Exportation terminée. {len(data_to_export)} lignes enregistrées.")
    except IOError as e:
        print(f"Erreur lors de l'écriture du fichier CSV : {e}")
