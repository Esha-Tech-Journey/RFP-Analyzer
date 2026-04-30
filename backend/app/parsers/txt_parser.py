"""Plain-text file parser using Python stdlib only."""

from app.parsers.base_parser import BaseFileParser


class TXTParser(BaseFileParser):
    """Extracts text from plain TXT files using Python's built-in decode.

    No third-party libraries are used. UTF-8 is attempted first,
    with latin-1 as a fallback to handle legacy encodings.
    """

    def extract_text(self, file_bytes: bytes) -> str:
        """Decode and return the content of a plain-text file.

        Args:
            file_bytes: Raw binary content of the TXT file.

        Returns:
            Decoded and stripped string content.

        Raises:
            ValueError: If the file is empty or contains only whitespace.
        """
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1")

        stripped = text.strip()

        if not stripped:
            raise ValueError("TXT file is empty.")

        return stripped
