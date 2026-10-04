# Phase 9 — Tool Calling Layer

**Status:** Complete (standalone tool-calling prototype)
**Previous:** Phase 8 — Reranking & Context Engineering
**Next:** Phase 10 — LangGraph Investigation Agent

## Objective

Before Phase 9, AegisOps could collect a fixed snapshot of incident and Prometheus evidence, retrieve and rerank runbook sections, and ask Gemini for structured hypotheses. It could recommend further checks but could not actually gather their results during its reasoning process.

Phase 9 introduces an explicitly controlled, read-only tool interface and a bounded Gemini interaction loop. The new capability was developed and verified **outside** the existing n8n-triggered investigation endpoint so it could be understood independently before LangGraph integration.

## Architecture and responsibilities

```text
Incident ID → Gemini investigation probe
                  ↓
            Function request
                  ↓
       Strict name + Pydantic argument validation
                  ↓
       Scoped tool dispatcher (read-only)
          ├── get_incident
          ├── get_metric
          └── get_service_logs
                  ↓
       Return observed result to Gemini
                  ↓
       Another permitted request, final answer,
       or controlled execution-limit exit
```

The **model decides which allowed tool to request**, but AegisOps alone authorizes and executes it. The tool declarations are not a security boundary by themselves; validation in `execute_tool()` and the underlying allowlists enforce the boundary. No tool can perform remediation.

## Implementation

### Step 9.1 — Incident and metric tools

`backend/app/investigations/tools.py` defines the dispatcher and validated argument models. `get_incident` retrieves a known incident from the existing PostgreSQL repository, including status and timestamps. The prototype further scopes incident requests to the incident ID supplied for that investigation.

`get_metric` queries the existing Prometheus client through one of four predefined monitoring rule keys:

| Allowed metric rule | Signal |
|---|---|
| `postgresql_unavailable` | Benchmark PostgreSQL dependency availability |
| `redis_unavailable` | Benchmark Redis dependency availability |
| `http_5xx_rate_high` | Benchmark API HTTP 5xx rate |
| `api_latency_high` | Benchmark API P95 latency |

Neither arbitrary PromQL nor arbitrary SQL is accepted. The tools distinguish valid readings from missing data and query errors.

The direct tool test against incident 13 returned `tool_status: OK`, observed its stored status as `RESOLVED`, and found PostgreSQL's latest dependency reading at `1.0` (UP). A request for `execute_shell` was rejected as an unknown or disallowed tool.

### Step 9.2 — Scoped Docker logs and container state

The `get_service_logs` tool calls only `docker inspect` and `docker logs` for three explicitly allowlisted benchmark services: API, Redis and PostgreSQL. The underlying command is passed as an argument array, not through a shell, and the service name is mapped to a fixed container name. The arguments bound the log window and tail count; the command has an eight-second timeout, and returned log text is truncated to approximately 8,000 characters.

The verification returned the benchmark PostgreSQL container as running, with exit code 0 and `oom_killed: false`. Recent logs showed startup and automatic database recovery **after a later interruption**. A request to inspect the separate `aegisops-postgres` core database was rejected by the allowlist.

Container logs are untrusted external data. This phase uses only the controlled benchmark; production-grade secret redaction and log access policies remain future requirements.

### Step 9.3 — Function declarations and first exchange

`backend/app/investigations/gemini_client.py` declares the three tools using the existing Pydantic argument schemas, submits them to the Gemini Interactions API, accepts function-call steps, invokes the validated dispatcher, and sends the function results back to the model.

The first experiment called `get_incident(13)` successfully and then requested more tools instead of producing a final explanation. This was an expected outcome of the initial single-round probe, demonstrating that a real investigation may need multiple evidence-gathering steps.

### Step 9.4 — Bounded tool execution

The standalone `probe_tool_calling()` function was extended to handle additional function requests while enforcing **at most three tool-execution rounds and six total tool calls**. It returns either `COMPLETED` or `LIMIT_REACHED`, making nontermination and uncontrolled API use less likely.

The completed test executed all three allowed tools:

| Executed tool | Arguments | Result |
|---|---|---|
| `get_incident` | `incident_id=13` | OK |
| `get_metric` | `rule_key=postgresql_unavailable` | OK |
| `get_service_logs` | `service=benchmark-postgresql`, `tail=50`, `since_minutes=30` | OK |

![Bounded investigation completed with three successful allowlisted tool calls](../screenshots/phase%209/tool-calls.png)

This screenshot verifies the full round trip from model-requested function names and arguments through the dispatcher to actual observations. It also demonstrates that no arbitrary command execution was necessary.

## Final report and temporal-grounding finding

After its third tool call, Gemini produced a readable investigation report for incident 13. It identified the incident as `RESOLVED`, described its historical dependency failure, and distinguished the *current* Prometheus reading of PostgreSQL `1.0` from the prior `0.0` trigger value.

![Final Gemini report generated after incident, metric and log tool calls](../screenshots/phase%209/investigation-report.png)

**Important limitation discovered during verification:** the report characterized recovery as automatic/self-resolved. The stored incident had already resolved before the startup and recovery logs that Gemini inspected. Those later logs show a subsequent recovery event, not what ended the earlier incident. We amended the experimental prompt to require timestamp checks and prohibit claims of self-resolution without evidence excluding operator action. **The amended prompt has not yet been retested**, so that improvement is a guardrail to verify in Phase 10—not a verified outcome of Phase 9.

## Scope and safety

- All three tools are read-only; no remediation or destructive commands are exposed.
- Pydantic rejects unknown fields, unrecognized rule keys, out-of-range log parameters and services outside the benchmark allowlist.
- The incident lookup is scoped to the active probe's incident ID.
- The loop limits execution rounds and total tool calls.
- The logs and metrics returned are untrusted and may represent *current* state, not historical evidence from the incident window.
- The final response in this experiment is a plain-text model report, **not** the persisted structured report produced by the existing `/investigations/{incident_id}/run` API.

## Verification and outcome

| Check | Observed result |
|---|---|
| Incident tool | Retrieved resolved incident 13 |
| Metric tool | Retrieved PostgreSQL health reading of `1.0` |
| Service-log tool | Retrieved allowlisted benchmark PostgreSQL state and logs |
| Unauthorized tool | Arbitrary `execute_shell` request rejected |
| Unauthorized container | Core AegisOps PostgreSQL access rejected |
| Gemini function call | Requested and executed `get_incident(13)` |
| Bounded multi-tool loop | `COMPLETED` after three successful tool calls |
| Final interpretation | Generated; an unsupported historical recovery inference was identified |

**Phase 9 outcome:** AegisOps now has a verified controlled tool interface and a standalone bounded Gemini investigation experiment. **The production n8n/FastAPI investigation path still uses the Phase 8 RAG pipeline.** Phase 10 will use LangGraph to maintain investigation state, orchestrate tool decisions, validate final structured outputs, and connect the tool-using agent into the normal incident lifecycle. It will also revisit retry, quota and historical-evidence safeguards.
