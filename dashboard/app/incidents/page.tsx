import Link from "next/link";

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
        min-h-[calc(100vh-82px)]
        p-6
        xl:p-8
      "
    >

      <div
        className="
          mx-auto
          w-full
          max-w-[1700px]
        "
      >

        {/* PAGE HEADER */}

        <div
          className="
            mb-6
            flex
            flex-col
            justify-between
            gap-5
            md:flex-row
            md:items-end
          "
        >

          <div>

            <h1
              className="
                text-[32px]
                font-bold
                tracking-[-0.035em]
                text-slate-950
              "
            >
              Incidents
            </h1>


            <p
              className="
                mt-1
                text-sm
                text-slate-600
              "
            >
              Detected incidents across monitored AegisOps services.
            </p>

          </div>


          {/* COUNTERS */}

          <div
            className="
              flex
              gap-3
            "
          >

            <SummaryCard
              label="Open"
              value={openCount}
              tone="red"
            />


            <SummaryCard
              label="Resolved"
              value={resolvedCount}
              tone="green"
            />

          </div>

        </div>


        {/* INCIDENT HISTORY */}

        <section
          className="
            overflow-hidden
            rounded-[30px]
            border
            border-white/30
          "
          style={{
            background:
              `
                linear-gradient(
                  135deg,
                  rgba(255,255,255,0.20),
                  rgba(255,255,255,0.09)
                )
              `,

            backdropFilter:
              "blur(22px)",

            WebkitBackdropFilter:
              "blur(22px)",

            boxShadow:
              `
                inset 0 1px 0 rgba(255,255,255,0.34),
                0 20px 60px rgba(53,42,76,0.08)
              `,
          }}
        >

          {/* SECTION HEADER */}

          <div
            className="
              flex
              items-center
              justify-between
              border-b
              border-white/22
              px-6
              py-5
            "
          >

            <div>

              <h2
                className="
                  text-lg
                  font-semibold
                  tracking-[-0.015em]
                  text-slate-950
                "
              >
                Incident History
              </h2>


              <p
                className="
                  mt-1
                  text-xs
                  text-slate-600
                "
              >
                {incidents.length} incidents loaded
              </p>

            </div>


            <div
              className="
                hidden
                items-center
                gap-2
                rounded-full
                border
                border-white/25
                bg-white/15
                px-3
                py-1.5
                text-[11px]
                font-medium
                text-slate-600
                backdrop-blur-xl
                sm:flex
              "
            >

              <span
                className="
                  h-2
                  w-2
                  rounded-full
                  bg-emerald-500
                "
              />

              Live incident records

            </div>

          </div>


          {incidents.length === 0 ? (

            <div
              className="
                flex
                min-h-[360px]
                items-center
                justify-center
                px-6
              "
            >

              <div className="text-center">

                <div
                  className="
                    mx-auto
                    flex
                    h-16
                    w-16
                    items-center
                    justify-center
                    rounded-[22px]
                    border
                    border-emerald-200/35
                    bg-emerald-100/40
                    backdrop-blur-xl
                  "
                >

                  <CheckCircle2
                    className="
                      h-8
                      w-8
                      text-emerald-600
                    "
                  />

                </div>


                <p
                  className="
                    mt-4
                    text-base
                    font-semibold
                    text-slate-800
                  "
                >
                  No incidents found
                </p>

              </div>

            </div>

          ) : (

            <div
              className="
                overflow-x-auto
                px-4
                pb-4
                pt-3
              "
            >

              <div
                className="
                  min-w-[1250px]
                "
              >

                {/* COLUMN HEADINGS */}

                <div
                  className="
                    grid
                    grid-cols-[70px_minmax(300px,1.8fr)_minmax(170px,0.9fr)_100px_120px_170px_170px]
                    items-center
                    gap-4
                    px-4
                    py-3
                    text-[11px]
                    font-semibold
                    uppercase
                    tracking-[0.06em]
                    text-slate-500
                  "
                >

                  <div>ID</div>
                  <div>Incident</div>
                  <div>Service</div>
                  <div>Severity</div>
                  <div>Status</div>
                  <div>Detected</div>
                  <div>Resolved</div>

                </div>


                {/* INCIDENT RECORDS */}

                <div className="space-y-2">

                  {incidents.map(
                    (incident) => (

                      <Link
                        key={incident.id}
                        href={`/incidents/${incident.id}`}
                        className="
                          group
                          grid
                          cursor-pointer
                          grid-cols-[70px_minmax(300px,1.8fr)_minmax(170px,0.9fr)_100px_120px_170px_170px]
                          items-center
                          gap-4
                          rounded-[20px]
                          border
                          border-white/22
                          px-4
                          py-3.5
                          transition
                          duration-200
                          hover:-translate-y-[1px]
                          hover:border-white/40
                          hover:bg-white/18
                          hover:shadow-[0_10px_26px_rgba(53,42,76,0.06)]
                          focus:outline-none
                          focus:ring-2
                          focus:ring-indigo-300/50
                        "
                        style={{
                          background:
                            "rgba(255,255,255,0.11)",

                          backdropFilter:
                            "blur(14px)",

                          WebkitBackdropFilter:
                            "blur(14px)",
                        }}
                      >

                        {/* ID */}

                        <div
                          className="
                            whitespace-nowrap
                            text-sm
                            font-medium
                            text-slate-600
                          "
                        >
                          #{incident.id}
                        </div>


                        {/* INCIDENT */}

                        <div
                          className="
                            flex
                            min-w-0
                            items-center
                            gap-3
                          "
                        >

                          <div
                            className="
                              flex
                              h-10
                              w-10
                              shrink-0
                              items-center
                              justify-center
                              rounded-[14px]
                              border
                              border-red-200/30
                              bg-red-100/42
                              transition
                              duration-200
                              group-hover:bg-red-100/60
                            "
                          >

                            <AlertTriangle
                              className="
                                h-[17px]
                                w-[17px]
                                text-red-600
                              "
                            />

                          </div>


                          <span
                            className="
                              truncate
                              text-sm
                              font-semibold
                              text-slate-950
                              transition
                              group-hover:text-indigo-950
                            "
                          >
                            {incident.title}
                          </span>

                        </div>


                        {/* SERVICE */}

                        <div
                          className="
                            truncate
                            text-sm
                            text-slate-700
                          "
                          title={incident.service}
                        >
                          {incident.service}
                        </div>


                        {/* SEVERITY */}

                        <div>

                          <SeverityBadge
                            severity={
                              incident.severity
                            }
                          />

                        </div>


                        {/* STATUS */}

                        <div>

                          <StatusBadge
                            status={
                              incident.status
                            }
                          />

                        </div>


                        {/* DETECTED */}

                        <div
                          className="
                            whitespace-nowrap
                            text-sm
                            text-slate-600
                          "
                        >
                          {formatDate(
                            incident.first_detected_at
                          )}
                        </div>


                        {/* RESOLVED */}

                        <div
                          className="
                            whitespace-nowrap
                            text-sm
                            text-slate-600
                          "
                        >
                          {formatDate(
                            incident.resolved_at
                          )}
                        </div>

                      </Link>

                    )
                  )}

                </div>

              </div>

            </div>

          )}

        </section>

      </div>

    </main>
  );
}


/* ========================================================= */
/* SUMMARY CARDS                                             */
/* ========================================================= */


function SummaryCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "red" | "green";
}) {
  const styles =
    tone === "red"
      ? {
          border:
            "border-red-200/40",

          background:
            "rgba(254,226,226,0.32)",

          label:
            "text-red-700",

          dot:
            "bg-red-500",
        }

      : {
          border:
            "border-emerald-200/40",

          background:
            "rgba(209,250,229,0.32)",

          label:
            "text-emerald-700",

          dot:
            "bg-emerald-500",
        };


  return (
    <div
      className={`
        min-w-[92px]
        rounded-[18px]
        border
        px-4
        py-3
        backdrop-blur-xl
        ${styles.border}
      `}
      style={{
        background:
          styles.background,

        boxShadow:
          `
            inset 0 1px 0 rgba(255,255,255,0.28),
            0 8px 22px rgba(53,42,76,0.04)
          `,
      }}
    >

      <p
        className={`
          flex
          items-center
          gap-1.5
          text-[11px]
          font-semibold
          ${styles.label}
        `}
      >

        <span
          className={`
            h-1.5
            w-1.5
            rounded-full
            ${styles.dot}
          `}
        />

        {label}

      </p>


      <p
        className="
          mt-1
          text-xl
          font-bold
          text-slate-950
        "
      >
        {value}
      </p>

    </div>
  );
}


/* ========================================================= */
/* SEVERITY                                                  */
/* ========================================================= */


function SeverityBadge({
  severity,
}: {
  severity: string;
}) {
  const normalized =
    severity.toUpperCase();


  const style =
    normalized === "CRITICAL"
      ? (
        "border-red-300/45 "
        + "bg-red-100/50 "
        + "text-red-800"
      )

      : normalized === "HIGH"
        ? (
          "border-red-200/40 "
          + "bg-red-100/38 "
          + "text-red-700"
        )

        : normalized === "MEDIUM"
          ? (
            "border-amber-200/45 "
            + "bg-amber-100/42 "
            + "text-amber-700"
          )

          : (
            "border-blue-200/40 "
            + "bg-blue-100/40 "
            + "text-blue-700"
          );


  return (
    <span
      className={`
        inline-flex
        rounded-full
        border
        px-2.5
        py-1
        text-[10px]
        font-semibold
        backdrop-blur-lg
        ${style}
      `}
    >
      {severity}
    </span>
  );
}


/* ========================================================= */
/* STATUS                                                    */
/* ========================================================= */


function StatusBadge({
  status,
}: {
  status: string;
}) {
  const normalized =
    status.toUpperCase();


  const style =
    normalized === "OPEN"
      ? (
        "border-red-200/40 "
        + "bg-red-100/40 "
        + "text-red-700"
      )

      : normalized === "RESOLVED"
        ? (
          "border-emerald-200/40 "
          + "bg-emerald-100/40 "
          + "text-emerald-700"
        )

        : (
          "border-blue-200/40 "
          + "bg-blue-100/40 "
          + "text-blue-700"
        );


  return (
    <span
      className={`
        inline-flex
        rounded-full
        border
        px-2.5
        py-1
        text-[10px]
        font-semibold
        backdrop-blur-lg
        ${style}
      `}
    >
      {status}
    </span>
  );
}


/* ========================================================= */
/* DATE                                                      */
/* ========================================================= */


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