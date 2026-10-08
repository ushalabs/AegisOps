import {
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";

import {
  getDashboardIncidents,
} from "@/lib/aegisops";


export const instant = false;


export default async function IncidentsPage() {
  const incidents =
    await getDashboardIncidents(
      100
    );


  const openCount =
    incidents.filter(
      (incident) =>
        incident.status ===
        "OPEN"
    ).length;


  const resolvedCount =
    incidents.filter(
      (incident) =>
        incident.status ===
        "RESOLVED"
    ).length;


  return (
    <main
      className="
        min-h-[calc(100vh-70px)]
        p-6 xl:p-8
      "
    >

      <div
        className="
          mb-6
          flex
          flex-col
          justify-between
          gap-4
          md:flex-row
          md:items-end
        "
      >

        <div>

          <h1
            className="
              text-3xl
              font-bold
              tracking-tight
            "
          >
            Incidents
          </h1>

          <p
            className="
              mt-1
              text-sm
              text-slate-500
            "
          >
            Detected incidents
            across monitored
            AegisOps services.
          </p>

        </div>


        <div
          className="
            flex gap-3
          "
        >

          <div
            className="
              rounded-xl
              border
              border-red-100
              bg-red-50
              px-4 py-3
            "
          >

            <p
              className="
                text-xs
                font-medium
                text-red-600
              "
            >
              Open
            </p>

            <p
              className="
                mt-1
                text-xl
                font-bold
                text-slate-900
              "
            >
              {openCount}
            </p>

          </div>


          <div
            className="
              rounded-xl
              border
              border-emerald-100
              bg-emerald-50
              px-4 py-3
            "
          >

            <p
              className="
                text-xs
                font-medium
                text-emerald-600
              "
            >
              Resolved
            </p>

            <p
              className="
                mt-1
                text-xl
                font-bold
                text-slate-900
              "
            >
              {resolvedCount}
            </p>

          </div>

        </div>

      </div>


      <section
        className="
          overflow-hidden
          rounded-2xl
          border
          border-slate-200
          bg-white
          shadow-sm
        "
      >

        <div
          className="
            border-b
            border-slate-100
            px-6 py-5
          "
        >

          <h2 className="font-semibold">
            Incident History
          </h2>

          <p
            className="
              mt-1
              text-xs
              text-slate-500
            "
          >
            {incidents.length}
            {" "}
            incidents loaded
          </p>

        </div>


        {incidents.length === 0 ? (

          <div
            className="
              flex h-64
              items-center
              justify-center
            "
          >

            <div className="text-center">

              <CheckCircle2
                className="
                  mx-auto
                  h-10 w-10
                  text-emerald-400
                "
              />

              <p
                className="
                  mt-3
                  text-sm
                  font-medium
                  text-slate-700
                "
              >
                No incidents found
              </p>

            </div>

          </div>

        ) : (

          <div className="overflow-x-auto">

            <table
              className="
                w-full
                text-left
                text-sm
              "
            >

              <thead
                className="
                  border-b
                  border-slate-100
                  bg-slate-50/70
                  text-xs
                  uppercase
                  tracking-wide
                  text-slate-500
                "
              >

                <tr>

                  <th className="px-6 py-4">
                    ID
                  </th>

                  <th className="px-6 py-4">
                    Incident
                  </th>

                  <th className="px-6 py-4">
                    Service
                  </th>

                  <th className="px-6 py-4">
                    Severity
                  </th>

                  <th className="px-6 py-4">
                    Status
                  </th>

                  <th className="px-6 py-4">
                    Detected
                  </th>

                  <th className="px-6 py-4">
                    Resolved
                  </th>

                </tr>

              </thead>


              <tbody
                className="
                  divide-y
                  divide-slate-100
                "
              >

                {incidents.map(
                  (incident) => (

                    <tr
                      key={
                        incident.id
                      }
                      className="
                        transition
                        hover:bg-slate-50
                      "
                    >

                      <td
                        className="
                          whitespace-nowrap
                          px-6 py-4
                          font-medium
                          text-slate-500
                        "
                      >
                        #
                        {incident.id}
                      </td>


                      <td className="px-6 py-4">

                        <div
                          className="
                            flex
                            items-center
                            gap-3
                          "
                        >

                          <div
                            className="
                              flex
                              h-9 w-9
                              shrink-0
                              items-center
                              justify-center
                              rounded-lg
                              bg-red-50
                            "
                          >
                            <AlertTriangle
                              className="
                                h-4 w-4
                                text-red-600
                              "
                            />
                          </div>

                          <span
                            className="
                              font-semibold
                              text-slate-900
                            "
                          >
                            {incident.title}
                          </span>

                        </div>

                      </td>


                      <td
                        className="
                          whitespace-nowrap
                          px-6 py-4
                          text-slate-600
                        "
                      >
                        {incident.service}
                      </td>


                      <td className="px-6 py-4">

                        <SeverityBadge
                          severity={
                            incident.severity
                          }
                        />

                      </td>


                      <td className="px-6 py-4">

                        <StatusBadge
                          status={
                            incident.status
                          }
                        />

                      </td>


                      <td
                        className="
                          whitespace-nowrap
                          px-6 py-4
                          text-slate-500
                        "
                      >
                        {formatDate(
                          incident.first_detected_at
                        )}
                      </td>


                      <td
                        className="
                          whitespace-nowrap
                          px-6 py-4
                          text-slate-500
                        "
                      >
                        {formatDate(
                          incident.resolved_at
                        )}
                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        )}

      </section>

    </main>
  );
}


function SeverityBadge({
  severity,
}: {
  severity: string;
}) {
  const normalized =
    severity.toUpperCase();


  const style =
    normalized ===
    "CRITICAL"
      ? "bg-red-100 text-red-700"

      : normalized ===
        "HIGH"
        ? "bg-red-50 text-red-700"

        : normalized ===
          "MEDIUM"
          ? "bg-amber-50 text-amber-700"

          : "bg-blue-50 text-blue-700";


  return (
    <span
      className={`
        rounded-full
        px-2.5 py-1
        text-xs
        font-semibold
        ${style}
      `}
    >
      {severity}
    </span>
  );
}


function StatusBadge({
  status,
}: {
  status: string;
}) {
  const normalized =
    status.toUpperCase();


  const style =
    normalized === "OPEN"
      ? "bg-red-50 text-red-700"

      : normalized ===
        "RESOLVED"
        ? "bg-emerald-50 text-emerald-700"

        : "bg-blue-50 text-blue-700";


  return (
    <span
      className={`
        rounded-full
        px-2.5 py-1
        text-xs
        font-semibold
        ${style}
      `}
    >
      {status}
    </span>
  );
}


function formatDate(
  value:
    | string
    | null
    | undefined
) {
  if (!value) {
    return "—";
  }


  return new Intl.DateTimeFormat(
    "en",
    {
      dateStyle:
        "medium",

      timeStyle:
        "short",
    }
  ).format(
    new Date(value)
  );
}