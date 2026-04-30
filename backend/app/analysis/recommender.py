"""Recommender strategy — produces a Go/No-Go recommendation from risk and effort."""


class Recommender:
    """Produces a Go/No-Go recommendation based on risk level and effort estimate.

    Decision matrix (first matching rule wins):
      High   + Large  → "No-Go"
      High   + any    → "Needs Discussion"
      Medium + Large  → "Needs Discussion"
      any    + any    → "Go"
    """

    def recommend(self, risk_level: str, effort: str) -> str:
        """Return a recommendation string for the given risk and effort pairing.

        Args:
            risk_level: One of "Low", "Medium", or "High".
            effort:     One of "Small", "Medium", or "Large".

        Returns:
            One of "Go", "No-Go", or "Needs Discussion".
        """
        if risk_level == "High" and effort == "Large":
            return "No-Go"
        if risk_level == "High":
            return "Needs Discussion"
        if risk_level == "Medium" and effort == "Large":
            return "Needs Discussion"
        return "Go"
