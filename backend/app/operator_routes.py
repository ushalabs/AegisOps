from secrets import compare_digest
from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.responses import HTMLResponse
from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials,
)
from pydantic import BaseModel, Field

from app.core.config import settings
from app.remediation_routes import (
    ReviewProposalRequest,
    review_proposal,
)


router = APIRouter(
    prefix="/operator",
    tags=["Operator Console"],
)

security = HTTPBasic()


def require_operator(
    credentials: HTTPBasicCredentials = Depends(security),
) -> HTTPBasicCredentials:
    expected_username = settings.operator_console_username
    expected_password = settings.operator_console_password

    configured = (
        bool(expected_username)
        and bool(expected_password)
    )

    username_matches = (
        configured
        and compare_digest(
            credentials.username.encode("utf-8"),
            expected_username.encode("utf-8"),
        )
    )

    password_matches = (
        configured
        and compare_digest(
            credentials.password.encode("utf-8"),
            expected_password.encode("utf-8"),
        )
    )

    if not username_matches or not password_matches:
        raise HTTPException(
            status_code=401,
            detail="Invalid operator credentials.",
            headers={
                "WWW-Authenticate": "Basic",
            },
        )

    return credentials


class OperatorReviewRequest(BaseModel):
    decision: Literal[
        "APPROVED",
        "REJECTED",
    ]

    note: str = Field(
        min_length=5,
        max_length=1000,
    )


@router.post("/proposals/{proposal_id}/review")
def submit_operator_review(
    proposal_id: int,
    request: OperatorReviewRequest,
    credentials: HTTPBasicCredentials = Depends(
        require_operator
    ),
):
    return review_proposal(
        proposal_id=proposal_id,
        request=ReviewProposalRequest(
            decision=request.decision,
            reviewer=credentials.username,
            note=request.note,
        ),
        review_key=settings.remediation_review_key,
    )


@router.get("", response_class=HTMLResponse)
def operator_console(
    credentials: HTTPBasicCredentials = Depends(
        require_operator
    ),
):
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>AegisOps Operator Console</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family:
                Inter,
                Arial,
                sans-serif;
            background: #0f172a;
            color: #e2e8f0;
        }

        header {
            padding: 24px 32px;
            border-bottom: 1px solid #334155;
        }

        h1 {
            margin: 0;
            font-size: 26px;
        }

        .subtitle {
            margin-top: 6px;
            color: #94a3b8;
        }

        main {
            max-width: 1100px;
            margin: 0 auto;
            padding: 32px;
        }

        .status {
            margin-bottom: 22px;
            color: #94a3b8;
        }

        .proposal {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 22px;
            margin-bottom: 18px;
        }

        .proposal-header {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            align-items: flex-start;
        }

        .proposal h2 {
            margin: 0 0 6px;
            font-size: 20px;
        }

        .meta {
            color: #94a3b8;
            font-size: 14px;
        }

        .badge {
            display: inline-block;
            padding: 5px 9px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: bold;
            background: #334155;
        }

        .section {
            margin-top: 18px;
        }

        .label {
            color: #94a3b8;
            font-size: 13px;
            margin-bottom: 5px;
        }

        .value {
            line-height: 1.5;
        }

        textarea {
            width: 100%;
            min-height: 90px;
            resize: vertical;
            margin-top: 7px;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #475569;
            background: #0f172a;
            color: #e2e8f0;
            font: inherit;
        }

        .actions {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            margin-top: 16px;
        }

        button {
            border: 0;
            border-radius: 8px;
            padding: 10px 18px;
            font-weight: bold;
            cursor: pointer;
        }

        button:disabled {
            opacity: 0.45;
            cursor: not-allowed;
        }

        .approve {
            background: #22c55e;
            color: #052e16;
        }

        .reject {
            background: #ef4444;
            color: white;
        }

        .review-result {
            margin-top: 12px;
            min-height: 20px;
            font-size: 14px;
        }

        .error {
            color: #fca5a5;
        }

        .success {
            color: #86efac;
        }

        .warning {
            margin-top: 14px;
            padding: 10px 12px;
            border: 1px solid #854d0e;
            border-radius: 8px;
            background: #422006;
            color: #fde68a;
        }

        .empty {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 32px;
            text-align: center;
            color: #94a3b8;
        }
    </style>
</head>

<body>

<header>
    <h1>AegisOps Operator Console</h1>

    <div class="subtitle">
        Human review queue for remediation proposals
    </div>
</header>

<main>
    <div id="status" class="status">
        Loading pending remediation proposals...
    </div>

    <div id="proposals"></div>
</main>


<script>

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


async function loadPendingProposals() {
    const status =
        document.getElementById("status");

    const container =
        document.getElementById("proposals");

    try {
        const response = await fetch(
            "/remediations/proposals?status=PENDING",
            {
                credentials: "same-origin",
            }
        );

        if (!response.ok) {
            throw new Error(
                "Could not load remediation proposals."
            );
        }

        const proposals = await response.json();

        status.textContent =
            `Pending proposals: ${proposals.length}`;

        if (proposals.length === 0) {
            container.innerHTML = `
                <div class="empty">
                    No remediation proposals currently require review.
                </div>
            `;

            return;
        }

        container.innerHTML =
            proposals.map(proposal => {

                const incidentOpen =
                    proposal.incident_status === "OPEN";

                const warning = incidentOpen
                    ? ""
                    : `
                        <div class="warning">
                            This incident is no longer OPEN.
                            Approval will not be permitted.
                        </div>
                    `;

                return `
                    <div
                        class="proposal"
                        id="proposal-${proposal.id}"
                    >

                        <div class="proposal-header">

                            <div>
                                <h2>
                                    ${escapeHtml(
                                        proposal.incident_title
                                    )}
                                </h2>

                                <div class="meta">
                                    Proposal #${proposal.id}
                                    · Incident #${proposal.incident_id}
                                    · ${escapeHtml(
                                        proposal.target_service
                                    )}
                                </div>
                            </div>

                            <span class="badge">
                                ${escapeHtml(
                                    proposal.risk_level
                                )} RISK
                            </span>

                        </div>

                        <div class="section">
                            <div class="label">
                                Severity
                            </div>

                            <div class="value">
                                ${escapeHtml(
                                    proposal.incident_severity
                                )}
                            </div>
                        </div>

                        <div class="section">
                            <div class="label">
                                Proposed Action
                            </div>

                            <div class="value">
                                ${escapeHtml(
                                    proposal.action_key
                                )}
                            </div>
                        </div>

                        <div class="section">
                            <div class="label">
                                Investigation Rationale
                            </div>

                            <div class="value">
                                ${escapeHtml(
                                    proposal.rationale
                                )}
                            </div>
                        </div>

                        <div class="section">
                            <div class="label">
                                Expected Outcome
                            </div>

                            <div class="value">
                                ${escapeHtml(
                                    proposal.expected_outcome
                                )}
                            </div>
                        </div>

                        <div class="section">
                            <div class="label">
                                Authorization Expires
                            </div>

                            <div class="value">
                                ${escapeHtml(
                                    proposal.expires_at
                                )}
                            </div>
                        </div>

                        ${warning}

                        <div class="section">
                            <div class="label">
                                Review Note
                            </div>

                            <textarea
                                id="note-${proposal.id}"
                                placeholder="Explain your review decision..."
                            ></textarea>
                        </div>

                        <div
                            id="result-${proposal.id}"
                            class="review-result"
                        ></div>

                        <div class="actions">

                            <button
                                class="reject"
                                data-proposal-id="${proposal.id}"
                                onclick="
                                    submitReview(
                                        ${proposal.id},
                                        'REJECTED'
                                    )
                                "
                            >
                                Reject
                            </button>

                            <button
                                class="approve"
                                data-proposal-id="${proposal.id}"
                                ${incidentOpen ? "" : "disabled"}
                                onclick="
                                    submitReview(
                                        ${proposal.id},
                                        'APPROVED'
                                    )
                                "
                            >
                                Approve
                            </button>

                        </div>

                    </div>
                `;
            }).join("");

    } catch (error) {
        status.innerHTML =
            '<span class="error">' +
            'Operator console unavailable.' +
            '</span>';

        container.innerHTML = "";
    }
}


async function submitReview(
    proposalId,
    decision
) {
    const noteElement =
        document.getElementById(
            `note-${proposalId}`
        );

    const resultElement =
        document.getElementById(
            `result-${proposalId}`
        );

    const note =
        noteElement.value.trim();

    if (note.length < 5) {
        resultElement.className =
            "review-result error";

        resultElement.textContent =
            "Please provide a review note.";

        return;
    }

    const buttons =
        document.querySelectorAll(
            `[data-proposal-id="${proposalId}"]`
        );

    buttons.forEach(
        button => button.disabled = true
    );

    resultElement.className =
        "review-result";

    resultElement.textContent =
        "Submitting decision...";

    try {
        const response = await fetch(
            `/operator/proposals/${proposalId}/review`,
            {
                method: "POST",

                credentials: "same-origin",

                headers: {
                    "Content-Type":
                        "application/json",
                },

                body: JSON.stringify({
                    decision: decision,
                    note: note,
                }),
            }
        );

        const payload =
            await response.json();

        if (!response.ok) {
            const detail =
                typeof payload.detail === "string"
                    ? payload.detail
                    : JSON.stringify(
                        payload.detail
                        ?? "Review failed."
                    );

            throw new Error(detail);
        }

        resultElement.className =
            "review-result success";

        resultElement.textContent =
            `Proposal ${payload.status.toLowerCase()}.`;

        await loadPendingProposals();

    } catch (error) {
        resultElement.className =
            "review-result error";

        resultElement.textContent =
            error.message;

        buttons.forEach(
            button => button.disabled = false
        );
    }
}


loadPendingProposals();

setInterval(
    loadPendingProposals,
    5000
);

</script>

</body>
</html>
"""