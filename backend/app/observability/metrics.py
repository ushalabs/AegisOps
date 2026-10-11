from prometheus_client import (
    Counter,
    Histogram,
)


INVESTIGATION_RUNS = Counter(
    "aegisops_investigation_runs_total",
    "Total LangGraph investigation runs.",
    ["outcome"],
)


INVESTIGATION_DURATION = Histogram(
    "aegisops_investigation_duration_seconds",
    "End-to-end LangGraph investigation duration.",
    ["outcome"],
    buckets=(
        5,
        10,
        20,
        30,
        45,
        60,
        90,
        120,
    ),
)


GEMINI_CALLS = Counter(
    "aegisops_gemini_calls_total",
    "Total Gemini calls made by AegisOps.",
    ["stage", "outcome"],
)


GEMINI_DURATION = Histogram(
    "aegisops_gemini_call_duration_seconds",
    "Gemini request duration.",
    ["stage", "outcome"],
    buckets=(
        0.5,
        1,
        2,
        3,
        5,
        7.5,
        10,
        15,
        20,
        30,
    ),
)


TOOL_CALLS = Counter(
    "aegisops_tool_calls_total",
    "Diagnostic tool calls made by the investigation agent.",
    ["tool", "status"],
)


TOOL_ROUNDS = Counter(
    "aegisops_tool_rounds_total",
    "Total diagnostic tool execution rounds.",
)


INVESTIGATION_LIMIT_REACHED = Counter(
    "aegisops_investigation_limit_reached_total",
    (
        "Investigations stopped because the "
        "agent tool budget was reached."
    ),
)


RAG_CHUNKS_SELECTED = Histogram(
    "aegisops_rag_chunks_selected",
    "Number of runbook chunks selected for an investigation.",
    buckets=(
        0,
        1,
        2,
        3,
        4,
        5,
        10,
    ),
)


HISTORICAL_INCIDENTS_SELECTED = Histogram(
    "aegisops_historical_incidents_selected",
    (
        "Number of historical incident memories "
        "supplied to an investigation."
    ),
    buckets=(
        0,
        1,
        2,
        3,
        4,
        5,
        10,
    ),
)