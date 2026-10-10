# Phase 15 — Operator Dashboard

## Objective

Phase 15 replaces the temporary embedded operator surface with a dedicated Next.js dashboard that exposes the complete AegisOps incident lifecycle to an operator.

The dashboard is intentionally a **control surface**, not a second source of business logic.

The primary rule is:

> The browser may display state and request human review actions, but FastAPI and PostgreSQL remain authoritative.

Phase 15 therefore adds an operator-facing interface while preserving all existing boundaries around investigation, approval, execution, recovery verification, and postmortem generation.

---

## Architecture

```text
Browser
   ↓
Next.js dashboard
   ↓
Server Components / Server Actions
   ↓
authenticated FastAPI dashboard + operator endpoints
   ↓
AegisOps PostgreSQL
   ↓
existing n8n / LangGraph / remediation / recovery pipeline
```

The dashboard does not replace n8n, LangGraph, Prometheus, or the remediation backend.

It exposes their persisted and live state through one coherent operator interface.

---

## 1. Dashboard Stack

Phase 15 introduces a dedicated frontend under:

```text
dashboard/
```

Primary technologies:

```text
Next.js 16
React 19
TypeScript
Tailwind CSS
Lucide icons
React Icons
```

The application uses the App Router and server-side data retrieval.

The final local operator URL is:

```text
http://localhost:3001
```

---

## 2. Operator Navigation

The final dashboard contains five primary operator surfaces:

```text
Dashboard
Incidents
Investigations
Remediation
Postmortems
```

The navigation intentionally avoids placeholder sections that are not yet backed by meaningful Phase 15 functionality.

This keeps the operator interface focused on the actual incident lifecycle.

---

## 3. Operations Dashboard

The home dashboard provides a high-level view of the current AegisOps state.

It includes:

- open incident count
- investigation count
- pending human approvals
- verified recoveries
- postmortem count
- recent incident activity
- detected vs. resolved incident trend
- live service health
- monitored dependency status

The final design uses a fixed dark operator rail and a warm light operational canvas.

![Phase 15 operator dashboard](../screenshots/phase%2015/Home.png)

---

## 4. Live Service Health

The dashboard performs live health checks for the monitored stack.

Current services include:

```text
Benchmark API
PostgreSQL
Redis
Prometheus
Grafana
cAdvisor
```

Health can be derived from either:

- HTTP health endpoints
- Docker container state / health checks

The home page therefore gives the operator immediate infrastructure visibility independent of incident persistence.

### Important distinction

Service health and incident count represent different state.

```text
Service Health
= current infrastructure observation

Open Incidents
= incidents formally created by the incident detector
```

These values can temporarily differ.

For example, after stopping Redis and PostgreSQL, the dashboard can immediately report:

```text
4 / 6 services healthy
```

while the incident engine may still show only one newly created incident for a short period.

This is expected because the incident path includes separate cadences:

```text
dependency health check
→ benchmark metric update
→ Prometheus scrape
→ AegisOps detection worker
→ persisted incident
```

The UI therefore does not falsely treat direct infrastructure state and formal incident state as the same signal.

---

## 5. Incident Activity

The dashboard visualizes detected and resolved incidents over the selected time window.

Supported time ranges:

```text
Last 1 hour
Last 6 hours
Last 24 hours
Last 7 days
```

The chart is built from real incident timestamps:

```text
first_detected_at
resolved_at
```

No synthetic incident values are used.

---

## 6. Incident History

Route:

```text
/incidents
```

The incident page displays persisted incident records, including:

- incident ID
- title
- service
- severity
- state
- detection time
- resolution time

Rows are directly navigable to the full incident detail page.

![Phase 15 incident history](../screenshots/phase%2015/incidents.png)

---

## 7. Incident Detail & Deterministic Timeline

Route:

```text
/incidents/{incident_id}
```

The detail view connects the operator UI to the deterministic lifecycle reconstruction introduced in Phase 14.

The timeline can expose:

```text
INCIDENT_CREATED
INVESTIGATION_COMPLETED
REMEDIATION_PROPOSED
REMEDIATION_APPROVED / REVIEWED
REMEDIATION_EXECUTION_STARTED
REMEDIATION_SUCCEEDED / FAILED
RECOVERY_VERIFICATION_STARTED
RECOVERY_CONFIRMED
RECOVERY_NOT_CONFIRMED
RECOVERY_INCONCLUSIVE
INCIDENT_RESOLVED
```

These lifecycle events come from persisted backend state.

They are not invented by the frontend or by Gemini.

The incident detail page can also show:

- latest investigation summary
- investigation confidence
- remediation proposal
- execution status
- recovery status
- linked postmortem

This gives the operator one place to inspect the full incident lifecycle.

---

## 8. Investigations

Route:

```text
/investigations
```

The Investigations page displays saved LangGraph investigation reports.

It exposes:

- linked incident
- service
- investigation model
- confidence
- evidence sufficiency
- summary
- creation time

The dashboard reads previously persisted investigation output.

Opening the page does **not** automatically invoke Gemini again.

![Phase 15 investigations](../screenshots/phase%2015/investigations.png)

---

## 9. Remediation & Human Approval

Route:

```text
/remediation
```

The remediation page exposes proposals and their execution/recovery state.

For each proposal, the operator can inspect:

- incident
- action
- target
- rationale
- expected outcome
- risk level
- review state
- execution state
- recovery state

Pending proposals expose:

```text
review note
Approve
Reject
```

![Phase 15 remediation review](../screenshots/phase%2015/remidation.png)

---

## 10. Review Security Boundary

The browser does not directly receive backend remediation secrets.

The review flow is:

```text
Browser form
   ↓
Next.js Server Action
   ↓
server-side AegisOps credentials
   ↓
POST /operator/proposals/{proposal_id}/review
   ↓
FastAPI revalidation
   ↓
PostgreSQL review state
   ↓
private n8n callback
```

This preserves the existing Phase 11/12 human-in-the-loop boundary.

The browser never receives:

- `REMEDIATION_REVIEW_KEY`
- `REMEDIATION_EXECUTION_KEY`
- operator backend password
- signed n8n callback URL

Gemini still cannot directly approve or execute remediation.

---

## 11. Postmortems

Routes:

```text
/postmortems
/postmortems/{incident_id}
```

The Postmortems page exposes canonical Phase 14 postmortems and their associated incident context.

The detail view can show:

- summary
- probable root cause
- impact
- what went well
- what could be improved
- lessons learned
- preventive actions

![Phase 15 postmortems](../screenshots/phase%2015/postmortems.png)

The frontend does not regenerate postmortems simply because an operator opens the page.

It reads canonical persisted state.

---

## 12. Dashboard Backend API

Phase 15 adds operator-facing dashboard endpoints under:

```text
/dashboard/api
```

Primary routes include:

```text
GET /dashboard/api/overview
GET /dashboard/api/incidents
GET /dashboard/api/incidents/{incident_id}/detail
GET /dashboard/api/investigations
GET /dashboard/api/remediations
GET /dashboard/api/postmortems
```

These endpoints are protected by the existing operator authentication boundary.

The dashboard uses them server-side rather than exposing credentials to the browser.

---

## 13. Next.js Data Layer

The frontend data helper is:

```text
dashboard/lib/aegisops.ts
```

Server-only environment variables:

```env
AEGISOPS_API_URL=http://127.0.0.1:8000
AEGISOPS_OPERATOR_USERNAME=
AEGISOPS_OPERATOR_PASSWORD=
```

The helper builds the backend Basic Auth header only on the server.

Dashboard pages use:

```text
cache: no-store
```

for operational data so the interface reflects current backend state instead of serving a stale cached representation.

---

## 14. Visual Design

The final interface intentionally avoids the appearance of a generic admin template.

The dashboard uses:

- fixed dark left operator rail
- full-height navigation
- warm neutral application background
- coral/red incident accent
- dark navy secondary accent
- compact operational cards
- larger readable typography
- minimal explanatory copy
- consistent rounded surfaces
- direct status labels

The sidebar remains visible while page content scrolls.

This keeps core navigation available even on long incident, investigation, or postmortem pages.

---

## 15. Real Data Requirement

Phase 15 does not hardcode operational values for presentation.

The UI consumes real data from:

```text
incidents
investigations
remediation_proposals
remediation_executions
recovery_verifications
incident_postmortems
live service checks
```

Examples include:

```text
open incident count
pending approval count
verified recovery count
postmortem count
service health
incident trend
```

The frontend styling can change without changing the underlying operational truth.

---

## 16. Controlled Failure Validation

Phase 15 was validated against controlled benchmark dependency failures.

During the final test, benchmark Redis and PostgreSQL were intentionally stopped.

The dashboard correctly reflected degraded infrastructure health:

```text
Benchmark API   HEALTHY
PostgreSQL      UNHEALTHY
Redis           UNHEALTHY
Prometheus      HEALTHY
Grafana         HEALTHY
cAdvisor        HEALTHY
```

which produced:

```text
4 / 6 services healthy
```

The operator dashboard also surfaced formal incident and approval state generated by the existing detector and orchestration pipeline.

This test exposed an important and correct distinction:

```text
direct health degradation can appear before
formal incident persistence catches up
```

because the two paths operate independently.

---

## 17. Human Approval Validation

The remediation surface was used to expose the pending human-review stage rather than bypassing it.

The expected approval path remains:

```text
incident detected
→ investigation saved
→ allowlisted remediation proposal
→ PENDING
→ operator review
→ backend APPROVED / REJECTED
→ approved only
→ execution
→ recovery verification
```

The dashboard therefore makes Phase 11's safety requirement usable without weakening it.

---

## 18. Phase 15 Files

Primary Phase 15 frontend files include:

```text
dashboard/app/page.tsx

dashboard/app/incidents/page.tsx
dashboard/app/incidents/[id]/page.tsx

dashboard/app/investigations/page.tsx

dashboard/app/remediation/page.tsx
dashboard/app/remediation/actions.ts

dashboard/app/postmortems/page.tsx
dashboard/app/postmortems/[id]/page.tsx

dashboard/app/layout.tsx
dashboard/app/globals.css

dashboard/components/dashboard-shell.tsx
dashboard/components/time-range-selector.tsx

dashboard/lib/aegisops.ts
```

Backend dashboard integration is primarily implemented in:

```text
backend/app/dashboard_routes.py
```

No new database migration was required for Phase 15.

The dashboard reads state already introduced by previous phases.

---

## 19. Verification Evidence

Final screenshots:

```text
docs/screenshots/phase 15/Home.png
docs/screenshots/phase 15/incidents.png
docs/screenshots/phase 15/investigations.png
docs/screenshots/phase 15/remidation.png
docs/screenshots/phase 15/postmortems.png
```

The screenshots verify the major operator-facing surfaces:

```text
Home.png
= live operations dashboard and service health

incidents.png
= persisted incident history

investigations.png
= saved investigation reports

remidation.png
= human remediation review surface

postmortems.png
= resolved incident learning / postmortems
```

---

## 20. Preserved Trust Boundaries

Phase 15 does not weaken the controls established in previous phases.

The following remain true:

```text
Gemini cannot execute infrastructure actions.

n8n cannot invent arbitrary remediation commands.

The browser cannot receive execution credentials.

The browser cannot directly execute Docker actions.

The backend revalidates approval, incident state,
action key and target before execution.

Recovery verification remains independent of command success.

Historical incident similarity remains reference material,
not current root-cause proof.
```

This is the central architectural requirement of the dashboard implementation.

---

## Result

Phase 15 is complete.

AegisOps now has a dedicated operator-facing interface covering the persisted operational lifecycle:

```text
observe
→ detect
→ inspect
→ investigate
→ review
→ remediate
→ verify
→ analyze
→ remember
```

The dashboard makes the system understandable and operable without duplicating the backend's authorization, execution, recovery, or reasoning responsibilities.

**Next: Phase 16 — Evals & Observability.**
