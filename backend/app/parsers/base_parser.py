"""Abstract base class that all file format parsers must implement."""

from abc import ABC, abstractmethod


class BaseFileParser(ABC):
    """Contract for all file format parsers.

    Each concrete parser handles exactly one file format and exposes
    a single method. Parsers have no knowledge of HTTP, databases, or jobs.
    """

    @abstractmethod
    def extract_text(self, file_bytes: bytes) -> str:
        """Extract and return all readable text from the given file bytes.

        Args:
            file_bytes: Raw binary content of the uploaded file.

        Returns:
            A plain-text string containing all extractable content.

        Raises:
            ValueError: If the file contains no extractable text.
        """
