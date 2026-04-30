"""PDF file parser using pdfplumber."""

import io
import re

import pdfplumber

from app.parsers.base_parser import BaseFileParser

# Matches PDF CID artifacts like (cid:127), (cid:32), etc.
_CID_PATTERN = re.compile(r"\(cid:\d+\)")


def _clean(text: str) -> str:
    """Replace CID encoding artifacts with bullet points and normalise whitespace."""
    text = _CID_PATTERN.sub("•", text)
    return text


class PDFParser(BaseFileParser):
    """Extracts plain text from PDF files using pdfplumber.

    Scanned image-only PDFs (no embedded text layer) are not supported
    and will raise a ValueError.
    """

    def extract_text(self, file_bytes: bytes) -> str:
        """Extract text from all pages of a PDF.

        Args:
            file_bytes: Raw binary content of the PDF file.

        Returns:
            All page texts joined by double newlines, stripped of leading/trailing whitespace.

        Raises:
            ValueError: If no extractable text is found across all pages.
        """
        page_texts: list[str] = []

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    page_texts.append(_clean(text))

        if not page_texts:
            raise ValueError(
                "PDF contains no extractable text. "
                "Scanned image PDFs are not supported."
            )

        return "\n\n".join(page_texts).strip()
