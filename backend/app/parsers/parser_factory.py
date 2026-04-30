"""Factory that selects the correct parser for a given file extension."""

from app.parsers.base_parser import BaseFileParser
from app.parsers.docx_parser import DOCXParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.txt_parser import TXTParser


class ParserFactory:
    """Returns the correct BaseFileParser instance for a given file extension.

    Adding support for a new format requires only:
      1. A new concrete parser module.
      2. One new entry in _PARSERS below.
    Nothing else in the codebase changes (Open/Closed Principle).
    """

    _PARSERS: dict[str, BaseFileParser] = {
        "pdf": PDFParser(),
        "docx": DOCXParser(),
        "txt": TXTParser(),
    }

    @classmethod
    def get_parser(cls, extension: str) -> BaseFileParser:
        """Return the parser registered for the given file extension.

        Args:
            extension: Lowercase file extension without the leading dot (e.g. "pdf").

        Returns:
            The corresponding BaseFileParser instance.

        Raises:
            ValueError: If no parser is registered for the given extension.
        """
        parser = cls._PARSERS.get(extension.lower())
        if parser is None:
            raise ValueError(f"Unsupported file type: .{extension}")
        return parser
