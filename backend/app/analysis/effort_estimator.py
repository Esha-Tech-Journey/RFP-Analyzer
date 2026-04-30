"""Effort estimator strategy — derives effort size from word count and requirement density."""

import re

# Word count thresholds for base effort classification.
_SMALL_THRESHOLD = 200
_LARGE_THRESHOLD = 600

# Minimum number of detected requirement lines to trigger a size bump.
_REQUIREMENT_LINE_BUMP_THRESHOLD = 8

# Ordered effort levels (used for bumping up one level).
_EFFORT_LEVELS: tuple[str, ...] = ("Small", "Medium", "Large")

# Regex that matches lines beginning with a list marker.
_REQUIREMENT_LINE_PATTERN = re.compile(r"^\s*(-|•|\d+\.)\s+", re.MULTILINE)


class EffortEstimator:
    """Estimates the implementation effort required for an RFP.

    Base classification is by word count:
      < 200 words  → "Small"
      200-600      → "Medium"
      > 600        → "Large"

    If more than 8 list-style requirement lines are found, the estimate
    is bumped up one size level (Small→Medium, Medium→Large, Large stays Large).
    """

    def estimate(self, text: str) -> str:
        """Return an effort estimate string for the given RFP text.

        Args:
            text: Full extracted plain text of the RFP document.

        Returns:
            One of "Small", "Medium", or "Large".
        """
        word_count = len(text.split())
        base_effort = self._classify_by_word_count(word_count)

        requirement_line_count = self._count_requirement_lines(text)
        if requirement_line_count > _REQUIREMENT_LINE_BUMP_THRESHOLD:
            base_effort = self._bump_up(base_effort)

        return base_effort

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_by_word_count(word_count: int) -> str:
        """Map word count to a base effort level."""
        if word_count < _SMALL_THRESHOLD:
            return "Small"
        if word_count <= _LARGE_THRESHOLD:
            return "Medium"
        return "Large"

    @staticmethod
    def _count_requirement_lines(text: str) -> int:
        """Count lines that start with a list marker (-, •, or digit+period)."""
        return len(_REQUIREMENT_LINE_PATTERN.findall(text))

    @staticmethod
    def _bump_up(effort: str) -> str:
        """Return the next effort level up, capped at 'Large'."""
        current_index = _EFFORT_LEVELS.index(effort)
        next_index = min(current_index + 1, len(_EFFORT_LEVELS) - 1)
        return _EFFORT_LEVELS[next_index]
