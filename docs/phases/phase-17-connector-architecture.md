# Phase 17 — Connector Architecture

## Objective

Phase 17 decouples the AegisOps incident-response core from the local benchmark environment.

Before this phase, core modules directly knew about benchmark-specific Prometheus queries, Docker container names, Docker log commands, Docker Compose restart actions, and service mappings. That worked for local validation, but it would make AWS, Velora, and future integrations require provider-specific logic throughout the codebase.

Phase 17 introduces a connector boundary:

```text
AegisOps Core
    ↓
Connector Registry
    ↓
Environment Connector
    ├── telemetry
    ├── logs
    └── approved remediation execution
```

The benchmark environment becomes the first concrete connector implementation.

---

## 1. Connector Package

The new connector layer lives under:

```text
backend/app/connectors/
├── __init__.py
├── base.py
├── models.py
├── registry.py
└── benchmark.py
```

The package separates shared contracts from environment-specific implementation details.

---

## 2. Connector Contracts

`base.py` defines the connector interface used by the AegisOps core.

The current contract exposes:

```text
supports_service()
get_signal()
get_logs()
execute_action()
```

Connectors retrieve telemetry, retrieve bounded logs, and execute predefined approved actions.

They do not decide whether an incident exists, whether remediation is authorized, or whether recovery is complete. Those policies remain in the AegisOps core.

---

## 3. Shared Models

`models.py` normalizes connector output through:

```text
ConnectorStatus
SignalReading
SignalResult
LogResult
ActionResult
```

`ConnectorStatus` distinguishes:

```text
OK
NO_DATA
ERROR
```

This prevents core modules from depending directly on Prometheus response shapes, Docker process output, or future provider-specific formats.

---

## 4. Connector Registry

`registry.py` introduces `ConnectorRegistry`.

The registry can:

```text
register a connector
resolve by connector key and service
resolve by service ownership
list registered connector keys
```

The benchmark connector registers as:

```text
benchmark
```

The registry rejects unknown connectors, unsupported services, duplicate registrations, and ambiguous service ownership.

---

## 5. Benchmark Connector

`benchmark.py` implements:

```text
BenchmarkConnector
```

It owns the benchmark-specific details that previously leaked into core modules:

```text
benchmark service allowlist
Prometheus signal definitions
Docker container mappings
Docker log retrieval
Docker container state inspection
Docker Compose restart actions
```

Supported services remain:

```text
benchmark-api
benchmark-redis
benchmark-postgresql
```

No arbitrary command execution was introduced.

---

## 6. Connector-Aware Incident Rules

`IncidentRule` now includes:

```text
connector_key
```

The current benchmark rules use:

```text
connector_key="benchmark"
```

PromQL was removed from the core incident-rule model.

Core incident rules now describe policy:

```text
rule key
title
service
connector
severity
operator
threshold
```

The benchmark connector owns the provider-specific Prometheus query behind each signal key.

---

## 7. Connector-Based Detection

The incident detector no longer imports the Prometheus client directly.

Detection now follows:

```text
IncidentRule
→ Connector Registry
→ BenchmarkConnector
→ normalized signal
→ deterministic threshold evaluation
```

AegisOps still owns incident thresholds, severity, deduplication, persistence, and resolution policy.

If telemetry is unavailable, the detector keeps the state unknown rather than creating or resolving an incident from missing evidence.

---

## 8. Connector-Backed Investigation Tools

The LangGraph tool names remain unchanged:

```text
get_incident
get_metric
get_service_logs
```

`get_metric` now resolves the connector declared by the incident rule.

`get_service_logs` resolves the connector that owns the requested service.

The model still receives bounded, validated tool results, but the investigation tool layer no longer contains benchmark container names or direct Prometheus logic.

---

## 9. Connector-Based Evidence Collection

The first end-to-end regression exposed one remaining direct dependency in:

```text
backend/app/investigations/evidence.py
```

The old evidence collector still referenced:

```text
rule.promql
```

and queried Prometheus directly.

That failed immediately after PromQL was correctly removed from `IncidentRule`, revealing a hidden coupling.

The evidence collector was then moved behind the connector registry:

```text
LangGraph
→ collect_incident_evidence()
→ IncidentRule.connector_key
→ Connector Registry
→ BenchmarkConnector
→ normalized signal result
```

The collected evidence continues to record signal identity, service, connector, threshold, operator, readings, and data status.

---

## 10. Connector-Based Remediation

The AegisOps remediation catalog remains authoritative.

Each remediation action now declares:

```text
action key
target service
connector key
description
risk level
```

Execution follows:

```text
approved proposal
→ AegisOps remediation catalog
→ Connector Registry
→ BenchmarkConnector
→ predefined concrete action
```

Proposal validation, human approval, target validation, execution authorization, and idempotency remain in the backend.

---

## 11. Defense-in-Depth

Phase 17 preserves two action allowlists:

```text
AegisOps REMEDIATION_CATALOG
        ↓
authorizes the logical action

BenchmarkConnector BENCHMARK_ACTIONS
        ↓
validates the concrete action and target
```

The connector refuses unknown action keys, unsupported services, and mismatched targets.

The model never receives authority to provide arbitrary shell commands.

---

## 12. Connector-Based Recovery Verification

Recovery uses the same connector-backed incident signal used by detection.

```text
Recovery policy
→ evaluate_rule()
→ Connector Registry
→ BenchmarkConnector
→ current telemetry
→ deterministic health decision
```

A successful remediation command is still not proof of recovery.

The existing policy remains:

```text
maximum attempts: 3
required consecutive healthy checks: 2
```

Terminal states remain:

```text
RECOVERED
NOT_RECOVERED
INCONCLUSIVE
```

---

## 13. Core vs Connector Responsibilities

AegisOps core still owns:

```text
incident rules and thresholds
incident persistence and deduplication
LangGraph control flow
RAG and historical memory
tool budgets
remediation proposal policy
human approval
execution authorization
recovery policy
postmortems
incident memory
operator APIs
```

Connectors own:

```text
environment-specific telemetry retrieval
environment-specific log retrieval
concrete allowlisted action execution
provider-specific service mappings
```

The connector layer is an infrastructure adapter, not a new source of policy or authorization.

---

## 14. End-to-End Regression

Phase 17 was validated with a fresh Redis outage after the refactor.

The incident result was:

```text
incident_id: 66
rule_key: redis_unavailable
service: benchmark-redis
severity: HIGH
trigger_value: 0.0
final status: RESOLVED
```

The persisted investigation was:

```text
investigation_id: 28
model: gemini-3.5-flash-lite
confidence: HIGH
status: COMPLETED
```

The investigation correctly reported that the Redis container had exited cleanly after receiving SIGTERM, while the final postmortem kept the root cause as:

```text
Undetermined from available evidence.
```

The remediation lifecycle produced:

```text
proposal_id: 17
action_key: restart_benchmark_redis
risk_level: MEDIUM
decision: APPROVED
reviewed_by: aegisops-operator
execution_id: 13
execution status: SUCCEEDED
exit_code: 0
```

Recovery verification produced:

```text
verification_id: 23
status: RECOVERED
attempt_count: 2
consecutive_healthy: 2
last_observed_value: 1.0
```

The postmortem was persisted as:

```text
postmortem_id: 9
```

The complete verified lifecycle was:

```text
Redis stopped
→ connector-backed detection
→ incident created
→ n8n orchestration
→ connector-backed evidence collection
→ LangGraph investigation
→ connector-backed diagnostic tools
→ investigation persisted
→ remediation proposed
→ human approval
→ connector-backed execution
→ independent connector-backed recovery verification
→ incident resolved
→ postmortem generated
```

This proves that the connector refactor preserved the full incident-response workflow.

---

## 15. Phase 17 Result

Phase 17 establishes a reusable boundary between the AegisOps core and target infrastructure.

AegisOps can now:

```text
route telemetry through connectors
retrieve diagnostic logs through connectors
collect LangGraph evidence through connectors
execute approved remediation through connectors
verify recovery through the same connector signal path
keep authorization and policy in the core backend
add new environment integrations without rewriting the incident lifecycle
```

The local benchmark remains fully functional through `BenchmarkConnector`.

**Next: Phase 18 — AWS Integration & Real Test Case.**
