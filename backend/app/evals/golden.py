import json
from pathlib import Path
from typing import Any


GOLDEN_FILE = (
    Path(__file__)
    .resolve()
    .with_name("golden_cases.json")
)


def load_golden_suite() -> dict[str, Any]:
    with GOLDEN_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def find_case_for_investigation(
    investigation: dict[str, Any],
) -> dict[str, Any] | None:
    suite = load_golden_suite()

    evidence = (
        investigation.get("evidence")
        or {}
    )

    incident = (
        evidence.get("incident")
        or {}
    )

    rule_key = incident.get(
        "rule_key"
    )

    service = incident.get(
        "service"
    )


    for case in suite["cases"]:
        if (
            case["rule_key"] == rule_key
            and case["service"] == service
        ):
            return case

    return None