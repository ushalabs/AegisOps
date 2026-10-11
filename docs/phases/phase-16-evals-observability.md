# Phase 16 — Evals & Observability

## Objective

Phase 16 adds measurable quality checks and runtime visibility to the AegisOps investigation agent.

The phase answers two questions:

1. Is a persisted investigation behaving safely and correctly?
2. What actually happened while the LangGraph investigation was running?

Evaluation is deterministic where possible. Runtime behavior is exported through Prometheus and visualized in Grafana.

---

## 1. Evaluation Persistence

Phase 16 adds PostgreSQL-backed evaluation history through:

```text
backend/sql/011_create_eval_tables.sql
```

The migration creates:

```text
eval_runs
eval_results
```

`eval_runs` stores suite-level execution state:

```text
suite name
status
total cases
passed cases
failed cases
start time
finish time
metadata
```

`eval_results` stores case-level results:

```text
case key
incident ID
investigation ID
pass/fail state
numeric score
individual checks
```

This keeps evaluation results auditable instead of leaving them only in terminal output.

---

## 2. Deterministic Investigation Evaluator

Evaluation code lives under:

```text
backend/app/evals/
```

The evaluator reads an already persisted investigation and validates it without making another Gemini request.

Current checks include:

```text
report schema validity
incident/evidence consistency
valid runbook source references
allowlisted tool usage
incident scope enforcement
tool-call budget enforcement
rejected tool requests
tool execution health
confidence/evidence consistency
tool-budget exhaustion
```

Critical failures can fail an evaluation even when the numeric score remains high.

---

## 3. Golden Investigation Cases

Golden behavior definitions are stored in:

```text
backend/app/evals/golden_cases.json
```

The current suite covers:

```text
PostgreSQL unavailable
Redis unavailable
HTTP 5xx rate elevated
API latency elevated
```

Golden cases validate expected behavior rather than exact generated wording.

Checks include:

```text
matching incident rule
expected severity
allowed confidence
useful diagnostic tool usage
forbidden tool usage
```

This avoids brittle tests based on exact LLM prose.

---

## 4. Evaluation Verification

A persisted PostgreSQL-unavailable investigation was evaluated against the golden suite.

Result:

```text
score: 0.9333
passed: true
checks passed: 14 / 15
```

The only failed check was:

```text
completed_without_budget_exhaustion
```

The investigation had reached the configured tool-round limit.

The result was intentionally retained rather than hidden or automatically relaxed. The purpose of the evaluator is to expose behavior that deserves inspection.

---

## 5. Prometheus Metrics Endpoint

The AegisOps FastAPI backend now exposes runtime metrics through:

```text
GET /metrics
```

Primary AegisOps metrics include:

```text
aegisops_investigation_runs_total
aegisops_investigation_duration_seconds
aegisops_gemini_calls_total
aegisops_gemini_call_duration_seconds
aegisops_tool_calls_total
aegisops_tool_rounds_total
aegisops_investigation_limit_reached_total
aegisops_rag_chunks_selected
aegisops_historical_incidents_selected
```

---

## 6. Investigation Runtime Observability

LangGraph investigation execution is measured without changing its authority or safety model.

AegisOps records:

```text
investigation outcome
end-to-end investigation duration
tool execution rounds
tool-call count and status
tool-budget exhaustion
```

Completed checkpoint reuse is not counted as a new investigation run.

---

## 7. Gemini Observability

Gemini calls are measured separately by stage.

Current stages include:

```text
agent_decision
structured_report
tool_probe
```

For each stage AegisOps records:

```text
success/error outcome
request count
request duration
```

This makes it possible to distinguish model latency from the rest of the investigation workflow.

---

## 8. Tool Observability

Diagnostic execution remains restricted to the existing read-only allowlist:

```text
get_incident
get_metric
get_service_logs
```

Phase 16 records:

```text
tool name
tool status
tool-call count
tool execution rounds
```

Observability does not grant new tool capability and does not weaken incident scoping.

---

## 9. RAG and Historical-Memory Observability

Each investigation records how much context was selected.

Measured values include:

```text
selected runbook chunks
selected historical incident memories
```

Historical incidents remain reference material and are never treated as proof of the current root cause.

---

## 10. Prometheus Integration

Prometheus now scrapes the AegisOps API in addition to the benchmark service and cAdvisor.

The local Docker Prometheus container reaches the host FastAPI process through:

```text
host.docker.internal:8000
```

Verification confirmed:

```text
up{job="aegisops-api"} = 1
```

A real agent metric was also successfully queried through Prometheus:

```text
aegisops_investigation_runs_total{outcome="COMPLETED"} = 1
```

This proves:

```text
LangGraph / Gemini / tools
        ↓
AegisOps /metrics
        ↓
Prometheus
```

---

## 11. Grafana Agent Observability

A dedicated engineering dashboard was added:

```text
AegisOps Agent Observability
```

It visualizes:

```text
investigation runs
average investigation duration
tool rounds
budget-limit events
Gemini calls
Gemini latency
diagnostic tool usage
RAG chunk count
historical incident-memory count
```

A real Redis outage populated the dashboard with actual execution data:

```text
Investigation runs: 1
Average duration: ~32 seconds
Tool rounds: 2
Budget limits reached: 0
Gemini agent-decision calls: 3
Structured-report calls: 1
Diagnostic tool calls: 2
Average RAG chunks: 3
Average historical memories: 3
```

![AegisOps Agent Observability](../screenshots/phase%2016/grafana.png)

---

## 12. Operator UI vs Engineering Observability

AegisOps deliberately keeps the product/operator dashboard and Grafana separate.

```text
Next.js Operator Dashboard
→ incidents
→ investigations
→ remediation review
→ execution/recovery visibility
→ postmortems

Grafana
→ infrastructure telemetry
→ agent execution telemetry
→ Gemini latency
→ diagnostic tool behavior
→ RAG and historical-memory usage
```

Grafana is not a second operator dashboard.

The Next.js application remains the primary human control surface, while Grafana is the engineering observability surface.

---

## 13. Phase 16 Result

Phase 16 adds both sides required for measurable agent quality:

```text
Deterministic evaluation
+
Runtime observability
```

AegisOps can now:

```text
evaluate persisted investigations
validate grounding and safety constraints
compare behavior against golden cases
persist evaluation results
measure LangGraph execution
measure Gemini latency and call volume
measure tool usage and failures
measure RAG and historical-memory context
export metrics through Prometheus
visualize agent behavior in Grafana
```

The investigation, remediation, approval, and recovery trust boundaries remain unchanged.

Phase 16 prepares AegisOps for Phase 17 — Connector Architecture.
