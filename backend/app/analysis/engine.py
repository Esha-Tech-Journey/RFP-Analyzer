"""Analysis engine — result dataclass, abstract base, concrete engine, and factory."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.analysis.effort_estimator import EffortEstimator
from app.analysis.llm_analyser import LLMAnalyser
from app.analysis.recommender import Recommender
from app.analysis.risk_analyser import RiskAnalyser
from app.analysis.summariser import Summariser


@dataclass
class AnalysisResult:
    """Structured output produced by the analysis engine for a single RFP.

    All fields are populated by the RuleBasedAnalysisEngine before being
    written to the database by the Celery worker.
    """

    summary: list[str]
    requirements: list[str]
    risk_level: str          # "Low" | "Medium" | "High"
    risk_reasons: list[str]
    effort: str              # "Small" | "Medium" | "Large"
    recommendation: str      # "Go" | "No-Go" | "Needs Discussion"
    ai_summary: str | None = None


class BaseAnalysisEngine(ABC):
    """Contract for all analysis engine implementations.

    Concrete engines receive plain text and return a fully populated
    AnalysisResult. They have no knowledge of files, HTTP, or databases.
    """

    @abstractmethod
    def analyse(self, title: str, text: str) -> AnalysisResult:
        """Analyse an RFP document and return structured results.

        Args:
            title: Human-readable title derived from the original filename.
            text:  Full extracted plain text of the RFP document.

        Returns:
            A populated AnalysisResult dataclass instance.
        """


class RuleBasedAnalysisEngine(BaseAnalysisEngine):
    """Concrete engine that orchestrates the four analysis strategies.

    Each strategy is injected via the constructor, making this class easy
    to test and extend without modifying existing strategy code.
    """

    def __init__(
        self,
        summariser: Summariser,
        risk_analyser: RiskAnalyser,
        effort_estimator: EffortEstimator,
        recommender: Recommender,
        llm_analyser: LLMAnalyser | None = None,
    ) -> None:
        """Inject all four analysis strategy instances plus optional LLM analyser."""
        self._summariser = summariser
        self._risk_analyser = risk_analyser
        self._effort_estimator = effort_estimator
        self._recommender = recommender
        self._llm_analyser = llm_analyser

    def analyse(self, title: str, text: str) -> AnalysisResult:
        """Run all strategies and assemble the final AnalysisResult."""
        summary = self._summariser.summarise(title, text)
        risk_level, risk_reasons = self._risk_analyser.analyse_risk(text)
        effort = self._effort_estimator.estimate(text)
        recommendation = self._recommender.recommend(risk_level, effort)
        requirements = self._extract_requirements(text)

        ai_summary: str | None = None
        if self._llm_analyser is not None:
            ai_summary = self._llm_analyser.generate_summary(title, text)

        return AnalysisResult(
            summary=summary,
            requirements=requirements,
            risk_level=risk_level,
            risk_reasons=risk_reasons,
            effort=effort,
            recommendation=recommendation,
            ai_summary=ai_summary,
        )

    @staticmethod
    def _extract_requirements(text: str) -> list[str]:
        """Return sentences containing requirement-obligation keywords.

        Extracts all matching sentences (no cap), for the requirements field.
        """
        import re

        obligation_keywords = ("require", "must", "shall", "deliver", "integrate", "provide")
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        return [
            s for s in sentences
            if any(kw in s.lower() for kw in obligation_keywords)
        ]


class AnalysisEngineFactory:
    """Constructs and returns a fully wired BaseAnalysisEngine.

    This is the only place in the codebase where concrete strategy classes
    are instantiated. All other code depends on the abstract engine interface.
    """

    @classmethod
    def create(cls) -> BaseAnalysisEngine:
        """Build and return a ready-to-use RuleBasedAnalysisEngine.

        If DIAL_API_KEY is configured in settings, an LLMAnalyser is wired in
        so every job gets an AI-generated summary in addition to rule-based scoring.
        """
        from app.config import settings  # local import avoids circular deps

        llm_analyser: LLMAnalyser | None = None
        if settings.DIAL_API_KEY:
            llm_analyser = LLMAnalyser(
                api_key=settings.DIAL_API_KEY,
                endpoint=settings.DIAL_ENDPOINT,
                model=settings.DIAL_MODEL,
            )

        return RuleBasedAnalysisEngine(
            summariser=Summariser(),
            risk_analyser=RiskAnalyser(),
            effort_estimator=EffortEstimator(),
            recommender=Recommender(),
            llm_analyser=llm_analyser,
        )
