"""Summariser strategy — produces 4-5 bullet points from RFP text."""

import re


# Keywords that identify requirement-bearing sentences.
_REQUIREMENT_KEYWORDS: tuple[str, ...] = (
    "require",
    "must",
    "shall",
    "deliver",
    "integrate",
    "provide",
)


class Summariser:
    """Produces a concise bullet-point summary of an RFP document.

    Rules (applied in order):
      1. The first non-empty sentence becomes bullet 1.
      2. Up to 3 sentences that contain a requirement keyword become bullets 2-4.
      3. The final bullet reports the approximate word count.
    """

    def summarise(self, title: str, text: str) -> list[str]:
        """Return 4-5 summary bullets extracted from the document text.

        Args:
            title: Human-readable title derived from the original filename.
            text:  Full extracted plain text of the RFP document.

        Returns:
            A list of 4-5 non-empty summary string bullets.
        """
        sentences = self._split_sentences(text)
        bullets: list[str] = []

        first_sentence = self._first_non_empty(sentences)
        if first_sentence:
            bullets.append(first_sentence)

        requirement_bullets = self._find_requirement_sentences(sentences, limit=3)
        bullets.extend(requirement_bullets)

        word_count = len(text.split())
        bullets.append(f"Document contains approximately {word_count} words.")

        return bullets

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into individual sentences on '.', '!', or '?'."""
        raw = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in raw if s.strip()]

    @staticmethod
    def _first_non_empty(sentences: list[str]) -> str | None:
        """Return the first sentence that contains at least one word."""
        for sentence in sentences:
            if sentence:
                return sentence
        return None

    @staticmethod
    def _find_requirement_sentences(
        sentences: list[str], limit: int
    ) -> list[str]:
        """Return up to `limit` sentences that contain a requirement keyword."""
        results: list[str] = []
        for sentence in sentences:
            if len(results) >= limit:
                break
            lowered = sentence.lower()
            if any(keyword in lowered for keyword in _REQUIREMENT_KEYWORDS):
                results.append(sentence)
        return results
