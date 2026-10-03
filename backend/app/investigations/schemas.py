from typing import Literal

from pydantic import BaseModel, Field


class CauseHypothesis(BaseModel):
    cause: str
    supporting_evidence: list[str]
    missing_evidence: list[str]


class InvestigationReport(BaseModel):
    summary: str
    observations: list[str]
    hypotheses: list[CauseHypothesis]
    recommended_checks: list[str]

    confidence: Literal["LOW", "MEDIUM", "HIGH"]

    evidence_sufficient: bool = Field(
        description=(
            "Whether the available evidence is sufficient "
            "to support a meaningful preliminary diagnosis."
        )
    )