# Phase 10 — LangGraph Investigation Agent

**Status:** Complete
**Previous:** Phase 9 — Tool Calling Layer
**Next:** Phase 11 — Human-in-the-Loop Remediation

## Objective

Replace the Phase 9 standalone Gemini tool loop with a stateful LangGraph investigation that reuses existing incident evidence, reranked RAG context, read-only tools and the validated structured report schema. Preserve progress using PostgreSQL checkpoints, bound tool execution and connect the working graph to the existing n8n Investigation Intake workflow without rebuilding the severity router.

The resulting agent is an **investigator, not a remediator**. It can read allowlisted data and recommend checks. It cannot run arbitrary commands, change infrastructure, or perform remediation without an explicit later approval mechanism.

## Architecture

```text
AegisOps incident → n8n severity router + live OPEN-state check
                         ↓
                Investigation Intake
                         ↓
         FastAPI POST /investigations/{id}/run-agent
                         ↓
       LangGraph state (PostgreSQL checkpoints, run ID)
                         ↓
           collect_evidence → retrieve_knowledge
                         ↓
                    gemini_decide
                  ↙              ↘
         More evidence          Completed / tool limit
              ↓                         ↓
        execute_tools              finalize_report
              ↓                         ↓
        gemini_decide          Validated structured report
                                        ↓
                          Save evidence, tool history and report
                                        ↓
                            Investigation ID returned to n8n
```

The original `POST /investigations/{incident_id}/run` endpoint remains available as a single-pass fallback. The new `run-agent` endpoint uses an explicit run ID to identify its LangGraph checkpoint thread.

## Implementation

### 10.1 — Shared investigation state

`backend/app/investigations/agent.py` defines a `StateGraph` whose typed state contains `incident_id`, evidence, RAG context, Gemini interaction ID, pending calls/results, tool-round count, tool history, completion status and execution events. The `events` and `tool_history` reducers append new observations instead of replacing prior entries.

The first two graph nodes reuse existing components:

- `collect_evidence`: retrieve incident state and a **current** Prometheus snapshot.
- `retrieve_knowledge`: retrieve up to 10 chunks from pgvector, cross-encoder rerank them and select up to three within the 2,400-character excerpt budget.

The first no-LLM graph test retrieved three PostgreSQL runbook sections for resolved incident **13**, in addition to preserving both expected graph events.

### 10.2 — Conditional Gemini reasoning and read-only tools

`gemini_decide` sends the accumulated context to Gemini and records any requested function calls. A conditional edge transfers control to `execute_tools` when the model needs more evidence. The tool node runs the existing Phase 9 allowlisted dispatcher and returns actual tool results to Gemini. A response with no further tool requests proceeds toward completion.

Supported tools are `get_incident`, `get_metric` (four predefined monitoring rules), and `get_service_logs` (approved benchmark containers only). Incident lookups are scoped to the current investigation. The graph enforces **three execution rounds and six total tool calls**; it does not permit shell or arbitrary SQL execution.

In the first LangGraph reasoning test, Gemini completed two rounds, successfully called `get_incident` and `get_service_logs`, and produced a final narrative that correctly separated later PostgreSQL restart logs from the earlier incident. The original root cause remained unproven.

### 10.3 — Validated report and database persistence

The `finalize_report` node reuses the existing `investigate_with_gemini()` and `save_investigation()` functions. It combines the initial metric snapshot, reranked runbook excerpts, actual tool history and preliminary agent summary, then produces an `InvestigationReport` with validated runbook source IDs. The structured report is saved to AegisOps PostgreSQL together with the complete supporting evidence.

The direct graph test returned `COMPLETED` and saved **investigation 7** for **incident 13**. The report referenced two retrieved PostgreSQL runbook chunks. The API subsequently returned record 7, its model and report, and listed the record under incident 13's investigation history.

#### Verified LangGraph execution

The following captured output shows the graph's execution events, three successful read-only tool calls, completed reasoning and structured investigation 7 being saved. This is the direct graph verification, before n8n integration.

![LangGraph execution events, successful tool calls and structured investigation 7 saved](../screenshots/phase%2010/langgraph-execution.png)

### 10.4 — PostgreSQL checkpointing

Installed `langgraph-checkpoint-postgres` and used `PostgresSaver` with the existing AegisOps database. A separate script, `backend/scripts/check_checkpoint.py`, compiled the graph with a pause immediately before `gemini_decide`, so persistence could be tested without additional Gemini requests.

**Two separate Python processes**—one starting and the other inspecting the same thread—returned the exact same checkpoint ID, the same two execution events, three retrieved chunks and `gemini_decide` as the next pending node. This demonstrates recovery of graph state across process exits at a known node boundary, not yet arbitrary mid-request crash recovery.

### 10.5–10.7 — Checkpoint-aware FastAPI and budget-aware finalization

The new `POST /investigations/{incident_id}/run-agent?run_id={uuid}` endpoint compiles the graph with a PostgreSQL checkpointer. A new run ID starts an investigation; an existing ID loads its saved state. A completed run returns its existing investigation ID instead of generating a duplicate report when the same ID is requested again.

The initial endpoint test reached the three-round tool budget and returned `LIMIT_REACHED` without a saved report. Resubmitting its same run ID returned that same terminal state, demonstrating checkpoint reuse. The graph was then updated so both `COMPLETED` and `LIMIT_REACHED` route to structured finalization. A budget-exhausted report records `agent_termination=TOOL_BUDGET_REACHED` and is returned as `COMPLETED_WITH_LIMIT`.

The subsequent test saved **investigation 8** for incident 13 using `gemini-3.5-flash-lite`. Its evidence recorded `TOOL_BUDGET_REACHED`, and a second request with the same run ID returned **the same investigation ID 8**. The returned report was a best-effort conclusion from the available evidence, not a verified root-cause determination.

### 10.8–10.9 — Real n8n integration

Updated the existing **AegisOps Investigation Intake** sub-workflow to use the new LangGraph endpoint in its `Run LangGraph Investigation` HTTP Request node. Its run ID remains stable for a given n8n execution, allowing checkpoint reuse. The main severity router, status recheck and recovered-incident skip path did not need to be rebuilt.

For the final integration test, stopping the benchmark Redis container triggered a fresh **HIGH-severity incident 15**. The published main workflow routed the active incident to Investigation Intake. The agent produced saved **investigation 9** with model `gemini-3.5-flash-lite`, and the API returned record 9 linked to incident 15. Its saved evidence confirmed `agent_termination=TOOL_BUDGET_REACHED`, all three successful calls (`get_incident`, `get_metric`, `get_service_logs`), and the `vector_search_then_reranking` strategy.

#### Verified n8n-to-LangGraph execution

Place the locally downloaded Investigation Intake execution screenshot as `docs/screenshots/phase 10/n8n-integration.png` in the repository. It documents the handoff from n8n to the LangGraph FastAPI endpoint; the API and saved evidence independently confirm the resulting investigation record.

![n8n Investigation Intake successfully handing a real incident to LangGraph](../screenshots/phase%2010/n8n-integration.png)

## Verification summary

| Check | Observed outcome |
|---|---|
| Shared graph state | Evidence and reranked knowledge preserved across nodes |
| Conditional tool loop | Gemini performed multiple evidence-gathering rounds |
| Tool restrictions | Incident/metric/log tools read only, validated and scoped |
| Structured report | Investigation 7 saved and retrieved from the API |
| PostgreSQL checkpoints | Identical checkpoint read by two separate Python processes |
| Endpoint run-ID reuse | Previous terminal run reused without repeating execution |
| Bounded finalization | Investigation 8 saved with `COMPLETED_WITH_LIMIT` |
| End-to-end n8n | Redis incident 15 resulted in LangGraph investigation 9 |
| Saved n8n investigation evidence | Three successful tool calls and reranked RAG strategy |

## Design boundaries and outstanding reliability work

- **Current telemetry is not incident-time telemetry.** Later service logs can support present-state checks without establishing what caused the original outage. The model must not assume the recovery mechanism or operator involvement without evidence.
- **Budget-aware reports are qualified conclusions.** `COMPLETED_WITH_LIMIT` means the agent finished using available evidence after reaching its read-only tool budget; it does not prove the root cause.
- **Checkpointing is not exactly-once execution.** A crash after the report commit but before the next graph checkpoint could produce a duplicate record on retry. Overlapping requests using the same run ID also need concurrency protection before production use.
- **Gemini service availability and quota remain external dependencies.** Temporary model failures may interrupt a run; the saved checkpoint supports recovery only from successfully committed graph boundaries.
- **Local Docker log access is development-only.** Production environments require dedicated connector permissions, log redaction, access controls and a robust treatment of untrusted log content.
- **No remediation action is authorized.** The graph only reads evidence and generates reports; production authentication and approval-gated write actions are deferred.

## Result and next phase

Phase 10 closed the loop from a real benchmark outage to a **checkpointed, stateful LangGraph investigation**, integrating RAG, safe tool requests, controlled finalization, PostgreSQL evidence persistence and the existing n8n orchestration.

**Next: Phase 11 — Human-in-the-Loop Remediation.** The following phase will introduce explicit, auditable approval of proposed recovery actions. No destructive operation should execute without authorization.
