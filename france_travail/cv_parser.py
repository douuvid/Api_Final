import PyPDF2
import docx

class CVParser:
    """Classe pour extraire le texte brut de fichiers CV (PDF, DOCX, TXT)."""

    def extract_text_from_file(self, file_path: str) -> str:
        """
        Extrait le texte d'un fichier en fonction de son extension.
        """
        if file_path.endswith('.pdf'):
            return self._extract_from_pdf(file_path)
        elif file_path.endswith('.docx'):
            return self._extract_from_docx(file_path)
        elif file_path.endswith('.txt'):
            return self._extract_from_txt(file_path)
        else:
            raise ValueError("Format de fichier non supporté. Utilisez .txt, .pdf, ou .docx.")

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extrait le texte d'un fichier PDF."""
        try:
            with open(file_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            print(f"Erreur lors de la lecture du PDF {file_path}: {e}")
            return ""

    def _extract_from_docx(self, file_path: str) -> str:
        """Extrait le texte d'un fichier DOCX."""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            print(f"Erreur lors de la lecture du DOCX {file_path}: {e}")
            return ""

    def _extract_from_txt(self, file_path: str) -> str:
        """Lit le contenu d'un fichier texte."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Erreur lors de la lecture du TXT {file_path}: {e}")
            return ""
