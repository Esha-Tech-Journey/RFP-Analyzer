"""DOCX file parser using python-docx."""

import io

import docx

from app.parsers.base_parser import BaseFileParser


class DOCXParser(BaseFileParser):
    """Extracts plain text from DOCX files using python-docx.

    Only paragraph text is extracted. Tables, headers, and footers
    are not included in this implementation.
    """

    def extract_text(self, file_bytes: bytes) -> str:
        """Extract text from all non-empty paragraphs in a DOCX document.

        Args:
            file_bytes: Raw binary content of the DOCX file.

        Returns:
            Paragraph texts joined by newlines, stripped of leading/trailing whitespace.

        Raises:
            ValueError: If the document contains no readable paragraph text.
        """
        document = docx.Document(io.BytesIO(file_bytes))

        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        if not paragraphs:
            raise ValueError("DOCX file contains no readable text.")

        return "\n".join(paragraphs).strip()
