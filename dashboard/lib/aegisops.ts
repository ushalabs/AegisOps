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