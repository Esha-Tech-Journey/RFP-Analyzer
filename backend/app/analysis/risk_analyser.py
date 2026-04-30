"""Risk analyser strategy — scores RFP text and returns a risk level with reasons."""

import re

# Keywords that contribute to the overall risk score.
# Each tuple is (keyword, score_contribution).
_HIGH_RISK_KEYWORDS: tuple[tuple[str, int], ...] = (
    ("compliance", 2),
    ("regulation", 2),
    ("gdpr", 2),
    ("migration", 2),
    ("legacy", 2),
    ("real-time", 2),
    ("sla", 2),
    ("penalty", 2),
    ("audit", 2),
    ("security", 2),
    ("encryption", 2),
    ("hipaa", 2),
    ("pci", 2),
)

_MEDIUM_RISK_KEYWORDS: tuple[tuple[str, int], ...] = (
    ("integration", 1),
    ("api", 1),
    ("third-party", 1),
    ("custom", 1),
    ("timeline", 1),
    ("budget", 1),
    ("offshore", 1),
    ("vendor", 1),
    ("deadline", 1),
)

_ALL_KEYWORDS: tuple[tuple[str, int], ...] = _HIGH_RISK_KEYWORDS + _MEDIUM_RISK_KEYWORDS


class RiskAnalyser:
    """Assigns a risk level to an RFP by scoring keyword matches.

    Scoring thresholds:
      >= 4  → "High"
      2–3   → "Medium"
      < 2   → "Low"
    """

    def analyse_risk(self, text: str) -> tuple[str, list[str]]:
        """Return a (risk_level, reasons) tuple based on keyword scoring.

        Args:
            text: Full extracted plain text of the RFP document.

        Returns:
            A tuple of:
              - risk_level: One of "Low", "Medium", or "High".
              - reasons: Deduplicated list of matched keyword strings.
        """
        lowered = text.lower()
        score = 0
        matched: list[str] = []

        for keyword, weight in _ALL_KEYWORDS:
            if self._keyword_present(keyword, lowered):
                score += weight
                if keyword not in matched:
                    matched.append(keyword)

        risk_level = self._score_to_level(score)
        return risk_level, matched

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _keyword_present(keyword: str, lowered_text: str) -> bool:
        """Return True if the keyword appears as a whole word (or phrase)."""
        pattern = re.escape(keyword)
        return bool(re.search(pattern, lowered_text))

    @staticmethod
    def _score_to_level(score: int) -> str:
        """Map a numeric score to a risk level string."""
        if score >= 4:
            return "High"
        if score >= 2:
            return "Medium"
        return "Low"
