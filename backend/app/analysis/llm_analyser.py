"""LLM-based analyser — calls EPAM DIAL (Azure OpenAI) to produce an AI summary."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an expert RFP (Request for Proposal) analyst. Your job is to read the \
full text of an RFP document and produce a structured analysis report.

Return your response in the following exact markdown format:

## Executive Summary
A concise 3-5 sentence overview of what the RFP is asking for.

## Key Requirements
A numbered list of the most important functional requirements found in the document.

## Constraints & Non-Functional Requirements
A numbered list of all constraints, non-functional requirements (performance, \
security, compliance, scalability, etc.) and any explicit technical standards.

## Identified Risks
A bulleted list of risks or concerns the responding organisation should be aware of \
(compliance obligations, tight timelines, ambiguous scope, legacy integrations, etc.).

Be thorough and precise. Quote or paraphrase the document directly where helpful. \
Do not add information that is not in the document.\
"""


class LLMAnalyser:
    """Uses EPAM DIAL (Azure OpenAI) to generate a full-text AI analysis of an RFP.

    The analyser is intentionally fault-tolerant: any API or network error is
    caught and logged, and ``None`` is returned so the job can still complete
    with rule-based results.
    """

    def __init__(self, api_key: str, endpoint: str, model: str) -> None:
        from openai import AzureOpenAI  # imported lazily to keep startup fast

        self._client = AzureOpenAI(
            api_key=api_key,
            api_version="2024-02-01",
            azure_endpoint=endpoint,
        )
        self._model = model

    def generate_summary(self, title: str, text: str) -> str | None:
        """Send the RFP text to the LLM and return the structured markdown response.

        Args:
            title: Human-readable title of the RFP document.
            text:  Full extracted plain text.

        Returns:
            Markdown string with sections defined in the system prompt,
            or ``None`` if the API call fails for any reason.
        """
        user_message = f"RFP Title: {title}\n\n---\n\n{text}"

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.2,
                max_tokens=2000,
            )
            content = response.choices[0].message.content
            return content.strip() if content else None
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM analysis failed (job will still complete): %s", exc)
            return None
