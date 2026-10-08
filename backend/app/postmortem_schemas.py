from typing import Literal

from pydantic import BaseModel, Field


class PreventiveAction(BaseModel):
    action: str = Field(
        min_length=5,
        max_length=500,
    )

    priority: Literal[
        "LOW",
        "MEDIUM",
        "HIGH",
    ]

    rationale: str = Field(
        min_length=5,
        max_length=500,
    )


class IncidentPostmortemReport(BaseModel):
    summary: str = Field(
        min_length=20,
        max_length=2000,
    )

    probable_root_cause: str = Field(
        min_length=5,
        max_length=1500,
    )

    root_cause_confidence: Literal[
        "LOW",
        "MEDIUM",
        "HIGH",
    ]

    impact: str = Field(
        min_length=5,
        max_length=1500,
    )

    what_went_well: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    what_could_be_improved: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    lessons_learned: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    preventive_actions: list[
        PreventiveAction
    ] = Field(
        default_factory=list,
        max_length=10,
    )

    unresolved_questions: list[str] = Field(
        default_factory=list,
        max_length=10,
    )