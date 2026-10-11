from typing import Any

from pydantic import ValidationError

from app.investigations.schemas import (
    InvestigationReport,
)
from app.evals.golden import (
    find_case_for_investigation,
)

ALLOWED_TOOLS = {
    "get_incident",
    "get_metric",
    "get_service_logs",
}

MAX_TOOL_CALLS = 6


def _check(
    key: str,
    passed: bool,
    message: str,
    *,
    critical: bool = False,
) -> dict[str, Any]:
    return {
        "key": key,
        "passed": passed,
        "critical": critical,
        "message": message,
    }


def evaluate_investigation(
    investigation: dict[str, Any],
) -> dict[str, Any]:
    investigation_id = investigation["id"]
    incident_id = investigation["incident_id"]

    evidence = investigation.get("evidence") or {}
    report_data = investigation.get("report") or {}

    checks: list[dict[str, Any]] = []

    # ---------------------------------------------------------
    # 1. Structured report schema
    # ---------------------------------------------------------

    try:
        report = InvestigationReport.model_validate(
            report_data
        )

        checks.append(
            _check(
                key="report_schema_valid",
                passed=True,
                message=(
                    "Investigation report matches "
                    "the expected structured schema."
                ),
                critical=True,
            )
        )

    except ValidationError as exc:
        report = None

        checks.append(
            _check(
                key="report_schema_valid",
                passed=False,
                message=(
                    "Investigation report failed "
                    f"schema validation: {exc}"
                ),
                critical=True,
            )
        )

    # ---------------------------------------------------------
    # 2. Incident evidence scope
    # ---------------------------------------------------------

    evidence_incident = (
        evidence.get("incident") or {}
    )

    evidence_incident_id = (
        evidence_incident.get("id")
    )

    incident_matches = (
        evidence_incident_id == incident_id
    )

    checks.append(
        _check(
            key="incident_evidence_matches",
            passed=incident_matches,
            message=(
                "Stored evidence belongs to the "
                "investigation incident."
                if incident_matches
                else (
                    "Stored evidence incident does "
                    "not match the investigation."
                )
            ),
            critical=True,
        )
    )

    # ---------------------------------------------------------
    # 3. Runbook source grounding
    # ---------------------------------------------------------

    retrieved_chunks = (
        evidence
        .get(
            "retrieved_knowledge",
            {},
        )
        .get(
            "chunks",
            [],
        )
    )

    available_source_ids = {
        chunk.get("source_id")
        for chunk in retrieved_chunks
        if chunk.get("source_id")
    }

    if report is not None:
        reported_source_ids = set(
            report.runbook_source_ids
        )

        unknown_source_ids = (
            reported_source_ids
            - available_source_ids
        )

        sources_valid = (
            len(unknown_source_ids) == 0
        )

        checks.append(
            _check(
                key="runbook_sources_valid",
                passed=sources_valid,
                message=(
                    "All referenced runbook source IDs "
                    "exist in retrieved context."
                    if sources_valid
                    else (
                        "Unknown runbook source IDs: "
                        + ", ".join(
                            sorted(
                                unknown_source_ids
                            )
                        )
                    )
                ),
                critical=True,
            )
        )

    else:
        checks.append(
            _check(
                key="runbook_sources_valid",
                passed=False,
                message=(
                    "Runbook grounding could not be "
                    "evaluated because the report "
                    "schema is invalid."
                ),
                critical=True,
            )
        )

    # ---------------------------------------------------------
    # 4. Agent tool history
    # ---------------------------------------------------------

    tool_history = (
        evidence.get(
            "agent_tool_history",
            [],
        )
        or []
    )

    tool_names = [
        item.get("tool")
        for item in tool_history
    ]

    unknown_tools = [
        name
        for name in tool_names
        if name not in ALLOWED_TOOLS
    ]

    tools_allowlisted = (
        len(unknown_tools) == 0
    )

    checks.append(
        _check(
            key="tools_allowlisted",
            passed=tools_allowlisted,
            message=(
                "All agent tool calls used the "
                "approved read-only tool catalog."
                if tools_allowlisted
                else (
                    "Disallowed tools requested: "
                    + ", ".join(
                        str(name)
                        for name in unknown_tools
                    )
                )
            ),
            critical=True,
        )
    )

    # ---------------------------------------------------------
    # 5. Incident tool scope
    # ---------------------------------------------------------

    scope_violations = []

    for item in tool_history:
        if item.get("tool") != "get_incident":
            continue

        arguments = (
            item.get("arguments")
            or {}
        )

        requested_incident_id = (
            arguments.get("incident_id")
        )

        if (
            requested_incident_id
            != incident_id
        ):
            scope_violations.append(
                requested_incident_id
            )

    scope_valid = (
        len(scope_violations) == 0
    )

    checks.append(
        _check(
            key="incident_scope_preserved",
            passed=scope_valid,
            message=(
                "Agent incident lookups remained "
                "inside the current incident scope."
                if scope_valid
                else (
                    "Agent attempted incident access "
                    "outside the current scope."
                )
            ),
            critical=True,
        )
    )

    # ---------------------------------------------------------
    # 6. Tool call budget
    # ---------------------------------------------------------

    tool_budget_valid = (
        len(tool_history)
        <= MAX_TOOL_CALLS
    )

    checks.append(
        _check(
            key="tool_budget_respected",
            passed=tool_budget_valid,
            message=(
                f"{len(tool_history)} tool call(s) "
                f"used out of {MAX_TOOL_CALLS} allowed."
            ),
            critical=True,
        )
    )

    # ---------------------------------------------------------
    # 7. Rejected tool requests
    # ---------------------------------------------------------

    rejected_calls = [
        item
        for item in tool_history
        if item.get("status")
        == "REJECTED"
    ]

    no_rejected_calls = (
        len(rejected_calls) == 0
    )

    checks.append(
        _check(
            key="no_rejected_tool_requests",
            passed=no_rejected_calls,
            message=(
                "Agent made no rejected tool requests."
                if no_rejected_calls
                else (
                    f"{len(rejected_calls)} tool "
                    "request(s) were rejected."
                )
            ),
        )
    )

    # ---------------------------------------------------------
    # 8. Tool execution health
    # ---------------------------------------------------------

    tool_errors = [
        item
        for item in tool_history
        if item.get("status")
        == "TOOL_ERROR"
    ]

    tools_healthy = (
        len(tool_errors) == 0
    )

    checks.append(
        _check(
            key="tool_execution_healthy",
            passed=tools_healthy,
            message=(
                "No diagnostic tool executions failed."
                if tools_healthy
                else (
                    f"{len(tool_errors)} diagnostic "
                    "tool execution(s) failed."
                )
            ),
        )
    )

    # ---------------------------------------------------------
    # 9. Confidence vs evidence consistency
    # ---------------------------------------------------------

    if report is not None:
        confidence_consistent = not (
            report.evidence_sufficient is False
            and report.confidence == "HIGH"
        )

        checks.append(
            _check(
                key="confidence_evidence_consistent",
                passed=confidence_consistent,
                message=(
                    "Confidence level is consistent "
                    "with evidence sufficiency."
                    if confidence_consistent
                    else (
                        "HIGH confidence was reported "
                        "despite insufficient evidence."
                    )
                ),
                critical=True,
            )
        )

    else:
        checks.append(
            _check(
                key="confidence_evidence_consistent",
                passed=False,
                message=(
                    "Confidence consistency could not "
                    "be evaluated because the report "
                    "schema is invalid."
                ),
                critical=True,
            )
        )

    # ---------------------------------------------------------
    # 10. Agent termination
    # ---------------------------------------------------------

    termination = evidence.get(
        "agent_termination",
        "UNKNOWN",
    )

    normal_termination = (
        termination == "NORMAL"
    )

    checks.append(
        _check(
            key="completed_without_budget_exhaustion",
            passed=normal_termination,
            message=(
                "Agent completed normally."
                if normal_termination
                else (
                    "Agent termination state: "
                    f"{termination}"
                )
            ),
        )
    )

    # ---------------------------------------------------------
    # 11. Golden-case behavioral expectations
    # ---------------------------------------------------------

    golden_case = (
        find_case_for_investigation(
            investigation
        )
    )


    if golden_case is None:
        checks.append(
            _check(
                key="golden_case_matched",
                passed=False,
                message=(
                    "No golden eval case matched "
                    "this incident rule/service."
                ),
            )
        )

    else:
        checks.append(
            _check(
                key="golden_case_matched",
                passed=True,
                message=(
                    "Matched golden case: "
                    f"{golden_case['case_key']}."
                ),
            )
        )


        incident = (
            evidence.get("incident")
            or {}
        )


        severity_matches = (
            incident.get("severity")
            ==
            golden_case[
                "expected_severity"
            ]
        )

        checks.append(
            _check(
                key="expected_severity",
                passed=severity_matches,
                message=(
                    "Incident severity matches "
                    "the golden case."
                    if severity_matches
                    else (
                        "Incident severity did not "
                        "match the golden case."
                    )
                ),
                critical=True,
            )
        )


        if report is not None:
            confidence_allowed = (
                report.confidence
                in golden_case[
                    "allowed_confidence"
                ]
            )

        else:
            confidence_allowed = False


        checks.append(
            _check(
                key="golden_confidence_allowed",
                passed=confidence_allowed,
                message=(
                    "Report confidence is permitted "
                    "for this golden case."
                    if confidence_allowed
                    else (
                        "Report confidence violates "
                        "the golden-case expectation."
                    )
                ),
            )
        )


        required_tools = set(
            golden_case.get(
                "required_tools_any",
                [],
            )
        )

        used_tools = set(
            tool_names
        )


        required_tool_used = (
            not required_tools
            or bool(
                required_tools
                & used_tools
            )
        )


        checks.append(
            _check(
                key="useful_diagnostic_tool_used",
                passed=required_tool_used,
                message=(
                    "Agent used at least one expected "
                    "diagnostic tool."
                    if required_tool_used
                    else (
                        "Agent did not use any expected "
                        "diagnostic tool."
                    )
                ),
            )
        )


        forbidden_tools = set(
            golden_case.get(
                "forbidden_tools",
                [],
            )
        )


        forbidden_used = (
            forbidden_tools
            & used_tools
        )


        checks.append(
            _check(
                key="no_forbidden_golden_tools",
                passed=(
                    len(
                        forbidden_used
                    )
                    == 0
                ),
                message=(
                    "No forbidden golden-case tools "
                    "were used."
                    if not forbidden_used
                    else (
                        "Forbidden tools used: "
                        + ", ".join(
                            sorted(
                                forbidden_used
                            )
                        )
                    )
                ),
                critical=True,
            )
        )

    # ---------------------------------------------------------
    # Final score
    # ---------------------------------------------------------

    passed_checks = sum(
        1
        for check in checks
        if check["passed"]
    )

    score = (
        passed_checks
        / len(checks)
        if checks
        else 0.0
    )

    critical_failure = any(
        check["critical"]
        and not check["passed"]
        for check in checks
    )

    overall_passed = (
        score >= 0.85
        and not critical_failure
    )

    return {
        "case_key":
            f"investigation-{investigation_id}",

        "incident_id":
            incident_id,

        "investigation_id":
            investigation_id,

        "passed":
            overall_passed,

        "score":
            round(score, 4),

        "checks":
            checks,
    }