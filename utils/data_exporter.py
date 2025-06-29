import csv
import os
from datetime import datetime

def export_to_csv(user_email, data_to_export, report_type='report', subdirectory=None):
    """
    Exporte les données dans un fichier CSV.
    Le rapport est sauvegardé dans un dossier spécifique à l'utilisateur pour une meilleure organisation.
    Ex: reports/report_iquestra/jean_dupont_example_com/report_20231027.csv
    """
    if not data_to_export:
        print("\nAucune nouvelle donnée à exporter.")
        return

    headers = list(data_to_export[0].keys())

    # Construire le chemin du répertoire de base des rapports
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_reports_dir = os.path.join(project_root, 'reports')

    # Nettoyer l'email pour l'utiliser comme nom de dossier
    safe_email_dirname = user_email.replace('@', '_').replace('.', '_')

    # Construire le chemin du sous-dossier (ex: 'reports/report_iquestra')
    target_dir = os.path.join(base_reports_dir, subdirectory) if subdirectory else base_reports_dir

    # Ajouter le dossier spécifique à l'utilisateur
    user_specific_dir = os.path.join(target_dir, safe_email_dirname)
    os.makedirs(user_specific_dir, exist_ok=True)

    # Créer le nom de fichier (l'email n'est plus nécessaire ici)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{report_type}_{timestamp}.csv"
    filepath = os.path.join(user_specific_dir, filename)

    print(f"\nExportation des données vers {filepath}...")

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data_to_export)
        print(f"Exportation terminée. {len(data_to_export)} lignes enregistrées.")
    except IOError as e:
        print(f"Erreur lors de l'écriture du fichier CSV : {e}")
