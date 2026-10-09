export type DashboardIncident = {
  id: number;
  title: string;
  service: string;
  severity: string;
  status: string;

  first_detected_at:
    | string
    | null;

  last_seen_at?:
    | string
    | null;

  resolved_at?:
    | string
    | null;
};


export type ServiceHealthStatus =
  | "HEALTHY"
  | "DEGRADED"
  | "UNHEALTHY";


export type DashboardServiceHealth = {
  key: string;
  name: string;

  status:
    ServiceHealthStatus;

  detail: string;

  latency_ms:
    | number
    | null;

  checked_at: string;
};


export type DashboardOverview = {
  range_hours: number;

  counts: {
    open_incidents: number;
    investigating: number;
    pending_approval: number;
    recovered: number;
    postmortems: number;
    total_incidents: number;
  };

  services:
    DashboardServiceHealth[];

  active_incidents:
    DashboardIncident[];

  recent_incidents:
    DashboardIncident[];
};


export type DashboardIncidentsResponse = {
  incidents:
    DashboardIncident[];
};


function getRequiredEnv(
  name: string
): string {
  const value =
    process.env[name];

  if (!value) {
    throw new Error(
      `Missing required environment variable: ${name}`
    );
  }

  return value;
}


function getAuthorizationHeader():
  string {
  const username =
    getRequiredEnv(
      "AEGISOPS_OPERATOR_USERNAME"
    );

  const password =
    getRequiredEnv(
      "AEGISOPS_OPERATOR_PASSWORD"
    );


  const token =
    Buffer.from(
      `${username}:${password}`,
      "utf8"
    ).toString(
      "base64"
    );


  return `Basic ${token}`;
}


export async function getDashboardOverview(
  hours = 24
): Promise<DashboardOverview> {
  const apiUrl =
    getRequiredEnv(
      "AEGISOPS_API_URL"
    );


  const response =
    await fetch(
      (
        `${apiUrl}/dashboard/api/overview`
        + `?hours=${hours}`
      ),
      {
        method: "GET",

        headers: {
          Accept:
            "application/json",

          Authorization:
            getAuthorizationHeader(),
        },

        cache:
          "no-store",
      }
    );


  if (!response.ok) {
    const body =
      await response.text();

    throw new Error(
      (
        "AegisOps overview request "
        + `failed (${response.status}): `
        + body
      )
    );
  }


  return response.json();
}


export async function getDashboardIncidents(
  limit = 100
): Promise<DashboardIncident[]> {
  const apiUrl =
    getRequiredEnv(
      "AEGISOPS_API_URL"
    );


  const response =
    await fetch(
      (
        `${apiUrl}/dashboard/api/incidents`
        + `?limit=${limit}`
      ),
      {
        method: "GET",

        headers: {
          Accept:
            "application/json",

          Authorization:
            getAuthorizationHeader(),
        },

        cache:
          "no-store",
      }
    );


  if (!response.ok) {
    const body =
      await response.text();

    throw new Error(
      (
        "AegisOps incidents request "
        + `failed (${response.status}): `
        + body
      )
    );
  }


  const data:
    DashboardIncidentsResponse =
      await response.json();


  return data.incidents;
}

export type InvestigationReport = {
  summary?: string;
  observations?: string[];

  hypotheses?: Array<{
    cause?: string;
    supporting_evidence?: string[];
    missing_evidence?: string[];
  }>;

  recommended_checks?: string[];

  confidence?:
    | "LOW"
    | "MEDIUM"
    | "HIGH"
    | string;

  evidence_sufficient?: boolean;

  runbook_source_ids?: string[];

  [key: string]: unknown;
};


export type DashboardInvestigation = {
  id: number;
  incident_id: number;
  model: string;

  evidence_collected_at:
    | string
    | null;

  created_at:
    | string
    | null;

  report:
    InvestigationReport;

  incident_title: string;
  incident_service: string;
  incident_severity: string;
  incident_status: string;
};


export type DashboardTimelineEvent = {
  event_type: string;

  timestamp:
    | string
    | null;

  details:
    Record<
      string,
      unknown
    >;
};


export type DashboardProposal = {
  id: number;
  incident_id: number;
  investigation_id: number;

  action_key: string;
  target_service: string;
  rationale: string;
  expected_outcome: string;

  risk_level: string;
  status: string;

  created_at:
    | string
    | null;

  expires_at:
    | string
    | null;

  reviewed_by?:
    | string
    | null;

  reviewed_at?:
    | string
    | null;

  review_note?:
    | string
    | null;
};


export type DashboardExecution = {
  id: number;
  proposal_id: number;
  action_key: string;
  target_service: string;
  status: string;

  started_at:
    | string
    | null;

  finished_at:
    | string
    | null;

  exit_code?:
    | number
    | null;

  output?:
    | string
    | null;

  error?:
    | string
    | null;
};


export type DashboardRecovery = {
  id: number;
  execution_id: number;
  rule_key: string;
  status: string;

  attempt_count: number;
  consecutive_healthy: number;

  last_observed_value?:
    | number
    | string
    | null;

  evidence?:
    Record<string, unknown>;

  created_at:
    | string
    | null;

  first_checked_at:
    | string
    | null;

  last_checked_at:
    | string
    | null;

  verified_at:
    | string
    | null;
};


export type DashboardPostmortem = {
  id: number;
  incident_id: number;

  summary: string;
  root_cause?: string | null;
  impact?: string | null;

  what_went_well:
    string[];

  what_went_wrong:
    string[];

  lessons_learned:
    string[];

  preventive_actions:
    Array<
      | string
      | {
          action?: string;
          priority?: string;
          rationale?: string;
        }
    >;

  model: string;

  created_at:
    | string
    | null;

  updated_at:
    | string
    | null;

  incident_title?: string;
  incident_service?: string;
  incident_severity?: string;
  incident_status?: string;

  resolved_at?:
    | string
    | null;
};


export type DashboardIncidentDetail = {
  incident: DashboardIncident & {
    fingerprint: string;
    rule_key: string;

    trigger_value?:
      | number
      | string
      | null;

    threshold?:
      | number
      | string
      | null;
  };

  timeline:
    DashboardTimelineEvent[];

  investigations:
    Array<
      DashboardInvestigation & {
        evidence?:
          Record<string, unknown>;
      }
    >;

  remediation_proposals:
    DashboardProposal[];

  remediation_executions:
    DashboardExecution[];

  recovery_verifications:
    DashboardRecovery[];

  postmortem:
    DashboardPostmortem
    | null;
};


export type DashboardRemediation = {
  id: number;
  incident_id: number;
  investigation_id: number;

  action_key: string;
  target_service: string;

  rationale: string;
  expected_outcome: string;

  risk_level: string;
  status: string;

  created_at:
    | string
    | null;

  expires_at:
    | string
    | null;

  reviewed_by?:
    | string
    | null;

  reviewed_at?:
    | string
    | null;

  review_note?:
    | string
    | null;

  incident_title: string;
  incident_severity: string;
  incident_status: string;

  execution_id?:
    | number
    | null;

  execution_status?:
    | string
    | null;

  execution_started_at?:
    | string
    | null;

  execution_finished_at?:
    | string
    | null;

  execution_exit_code?:
    | number
    | null;

  recovery_id?:
    | number
    | null;

  recovery_status?:
    | string
    | null;

  recovery_attempt_count?:
    | number
    | null;

  recovery_verified_at?:
    | string
    | null;
};


async function dashboardRequest<T>(
  path: string,
  allow404 = false
): Promise<T | null> {
  const apiUrl =
    getRequiredEnv(
      "AEGISOPS_API_URL"
    );


  const response =
    await fetch(
      `${apiUrl}${path}`,
      {
        headers: {
          Accept:
            "application/json",

          Authorization:
            getAuthorizationHeader(),
        },

        cache:
          "no-store",
      }
    );


  if (
    allow404 &&
    response.status === 404
  ) {
    return null;
  }


  if (!response.ok) {
    const body =
      await response.text();

    throw new Error(
      `AegisOps request failed (${response.status}): ${body}`
    );
  }


  return response.json();
}


export async function getDashboardIncidentDetail(
  incidentId: number
): Promise<
  DashboardIncidentDetail
  | null
> {
  return dashboardRequest<
    DashboardIncidentDetail
  >(
    `/dashboard/api/incidents/${incidentId}/detail`,
    true
  );
}


export async function getDashboardInvestigations(
  limit = 100
): Promise<
  DashboardInvestigation[]
> {
  const data =
    await dashboardRequest<{
      investigations:
        DashboardInvestigation[];
    }>(
      `/dashboard/api/investigations?limit=${limit}`
    );


  return (
    data?.investigations
    ?? []
  );
}


export async function getDashboardRemediations(
  limit = 100
): Promise<
  DashboardRemediation[]
> {
  const data =
    await dashboardRequest<{
      remediations:
        DashboardRemediation[];
    }>(
      `/dashboard/api/remediations?limit=${limit}`
    );


  return (
    data?.remediations
    ?? []
  );
}


export async function getDashboardPostmortems(
  limit = 100
): Promise<
  DashboardPostmortem[]
> {
  const data =
    await dashboardRequest<{
      postmortems:
        DashboardPostmortem[];
    }>(
      `/dashboard/api/postmortems?limit=${limit}`
    );


  return (
    data?.postmortems
    ?? []
  );
}


export async function reviewRemediationProposal(
  proposalId: number,
  decision:
    | "APPROVED"
    | "REJECTED",
  note: string
) {
  const apiUrl =
    getRequiredEnv(
      "AEGISOPS_API_URL"
    );


  const response =
    await fetch(
      `${apiUrl}/operator/proposals/${proposalId}/review`,
      {
        method: "POST",

        headers: {
          Accept:
            "application/json",

          "Content-Type":
            "application/json",

          Authorization:
            getAuthorizationHeader(),
        },

        body:
          JSON.stringify({
            decision,
            note,
          }),

        cache:
          "no-store",
      }
    );


  if (!response.ok) {
    const body =
      await response.text();

    throw new Error(
      `Review failed (${response.status}): ${body}`
    );
  }


  return response.json();
}