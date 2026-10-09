import Link from "next/link";
import { notFound } from "next/navigation";

import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  BrainCircuit,
  CheckCircle2,
  Clock3,
  FileText,
  HeartPulse,
  ShieldCheck,
  Wrench,
  Zap,
} from "lucide-react";

import type { ReactNode } from "react";
import {
  getDashboardIncidentDetail,
  type DashboardTimelineEvent,
} from "@/lib/aegisops";


export const instant = false;


export default async function IncidentDetailPage({
  params,
}: {
  params: Promise<{
    id: string;
  }>;
}) {
  const {
    id,
  } = await params;


  const incidentId =
    Number(id);


  if (
    !Number.isInteger(
      incidentId
    )
  ) {
    notFound();
  }


  const detail =
    await getDashboardIncidentDetail(
      incidentId
    );


  if (!detail) {
    notFound();
  }


  const incident =
    detail.incident;


  const latestInvestigation =
    detail.investigations.at(-1);


  const latestRecovery =
    detail.recovery_verifications.at(-1);


  return (
    <main className="p-6 xl:p-8">

      <div className="mx-auto max-w-[1700px]">

        <Link
          href="/incidents"
          className="
            mb-5
            inline-flex
            items-center
            gap-2
            text-sm
            font-semibold
            text-slate-600
            hover:text-slate-950
          "
        >
          <ArrowLeft className="h-4 w-4" />
          Incidents
        </Link>


        <GlassPanel className="p-6">

          <div
            className="
              flex
              flex-col
              justify-between
              gap-5
              lg:flex-row
              lg:items-start
            "
          >

            <div>

              <div className="flex items-center gap-3">

                <div
                  className="
                    flex
                    h-12
                    w-12
                    items-center
                    justify-center
                    rounded-2xl
                    bg-red-100/55
                  "
                >
                  <AlertTriangle
                    className="
                      h-6
                      w-6
                      text-red-600
                    "
                  />
                </div>

                <div>

                  <p
                    className="
                      text-xs
                      font-semibold
                      uppercase
                      tracking-wide
                      text-slate-500
                    "
                  >
                    Incident #{incident.id}
                  </p>

                  <h1
                    className="
                      mt-1
                      text-3xl
                      font-bold
                      tracking-tight
                      text-slate-950
                    "
                  >
                    {incident.title}
                  </h1>

                </div>

              </div>


              <p
                className="
                  mt-4
                  text-sm
                  text-slate-600
                "
              >
                {incident.service}
                {" · "}
                {incident.rule_key}
              </p>

            </div>


            <div className="flex gap-2">

              <Badge
                text={
                  incident.severity
                }
                tone="red"
              />

              <Badge
                text={
                  incident.status
                }
                tone={
                  incident.status ===
                  "RESOLVED"
                    ? "green"
                    : "red"
                }
              />

            </div>

          </div>


          <div
            className="
              mt-6
              grid
              gap-3
              md:grid-cols-4
            "
          >

            <InfoCard
              label="Detected"
              value={
                formatDate(
                  incident.first_detected_at
                )
              }
            />

            <InfoCard
              label="Resolved"
              value={
                formatDate(
                  incident.resolved_at
                )
              }
            />

            <InfoCard
              label="Trigger"
              value={
                formatValue(
                  incident.trigger_value
                )
              }
            />

            <InfoCard
              label="Threshold"
              value={
                formatValue(
                  incident.threshold
                )
              }
            />

          </div>

        </GlassPanel>


        <section
          className="
            mt-5
            grid
            gap-5
            xl:grid-cols-[minmax(0,1fr)_390px]
          "
        >

          <GlassPanel>

            <div
              className="
                border-b
                border-white/30
                px-6
                py-5
              "
            >
              <h2
                className="
                  text-xl
                  font-semibold
                  text-slate-950
                "
              >
                Incident Timeline
              </h2>

              <p
                className="
                  mt-1
                  text-xs
                  text-slate-500
                "
              >
                Deterministic lifecycle events
              </p>
            </div>


            <div className="p-6">

              <div className="space-y-0">

                {detail.timeline.map(
                  (
                    event,
                    index
                  ) => (
                    <TimelineItem
                      key={
                        `${event.event_type}-${event.timestamp}-${index}`
                      }
                      event={event}
                      last={
                        index ===
                        detail.timeline.length - 1
                      }
                    />
                  )
                )}

              </div>

            </div>

          </GlassPanel>


          <div className="space-y-5">

            <GlassPanel className="p-5">

              <h3
                className="
                  text-base
                  font-semibold
                  text-slate-950
                "
              >
                Latest Investigation
              </h3>


              {latestInvestigation ? (

                <>
                  <div className="mt-4">

                    <Badge
                      text={
                        latestInvestigation
                          .report
                          ?.confidence
                        ?? "UNKNOWN"
                      }
                      tone="blue"
                    />

                  </div>

                  <p
                    className="
                      mt-4
                      text-sm
                      leading-6
                      text-slate-700
                    "
                  >
                    {
                      latestInvestigation
                        .report
                        ?.summary
                      ?? "No summary available."
                    }
                  </p>

                  <p
                    className="
                      mt-4
                      text-xs
                      text-slate-500
                    "
                  >
                    {
                      latestInvestigation.model
                    }
                  </p>
                </>

              ) : (

                <EmptyText text="No investigation stored." />

              )}

            </GlassPanel>


            <GlassPanel className="p-5">

              <h3
                className="
                  text-base
                  font-semibold
                  text-slate-950
                "
              >
                Recovery
              </h3>


              {latestRecovery ? (

                <div className="mt-4">

                  <Badge
                    text={
                      latestRecovery.status
                    }
                    tone={
                      latestRecovery.status ===
                      "RECOVERED"
                        ? "green"
                        : "amber"
                    }
                  />

                  <p
                    className="
                      mt-4
                      text-sm
                      text-slate-700
                    "
                  >
                    Attempts:{" "}
                    {
                      latestRecovery
                        .attempt_count
                    }
                  </p>

                  <p
                    className="
                      mt-1
                      text-xs
                      text-slate-500
                    "
                  >
                    Verified{" "}
                    {
                      formatDate(
                        latestRecovery
                          .verified_at
                      )
                    }
                  </p>

                </div>

              ) : (

                <EmptyText text="No recovery verification stored." />

              )}

            </GlassPanel>


            <GlassPanel className="p-5">

              <h3
                className="
                  text-base
                  font-semibold
                  text-slate-950
                "
              >
                Postmortem
              </h3>


              {detail.postmortem ? (

                <>
                  <p
                    className="
                      mt-4
                      text-sm
                      leading-6
                      text-slate-700
                    "
                  >
                    {
                      detail.postmortem
                        .summary
                    }
                  </p>

                  <Link
                    href={
                      `/postmortems/${incident.id}`
                    }
                    className="
                      mt-4
                      inline-flex
                      text-sm
                      font-semibold
                      text-indigo-700
                      hover:text-indigo-900
                    "
                  >
                    Open postmortem →
                  </Link>
                </>

              ) : (

                <EmptyText text="No postmortem generated." />

              )}

            </GlassPanel>

          </div>

        </section>


        {detail.investigations.length > 0 && (

          <GlassPanel className="mt-5 p-6">

            <h2 className="text-xl font-semibold">
              Investigation Report
            </h2>


            {detail.investigations.map(
              (investigation) => (

                <div
                  key={
                    investigation.id
                  }
                  className="
                    mt-5
                    rounded-2xl
                    border
                    border-white/30
                    bg-white/15
                    p-5
                  "
                >

                  <div
                    className="
                      flex
                      justify-between
                      gap-4
                    "
                  >

                    <div>
                      <p className="font-semibold">
                        Investigation #{investigation.id}
                      </p>

                      <p
                        className="
                          mt-1
                          text-xs
                          text-slate-500
                        "
                      >
                        {formatDate(
                          investigation.created_at
                        )}
                      </p>
                    </div>

                    <Badge
                      text={
                        investigation
                          .report
                          ?.confidence
                        ?? "UNKNOWN"
                      }
                      tone="blue"
                    />

                  </div>


                  <p
                    className="
                      mt-4
                      text-sm
                      leading-6
                      text-slate-700
                    "
                  >
                    {
                      investigation
                        .report
                        ?.summary
                    }
                  </p>


                  <TextList
                    title="Observations"
                    items={
                      investigation
                        .report
                        ?.observations
                    }
                  />


                  <TextList
                    title="Recommended Checks"
                    items={
                      investigation
                        .report
                        ?.recommended_checks
                    }
                  />

                </div>

              )
            )}

          </GlassPanel>

        )}


        {detail.remediation_proposals.length > 0 && (

          <GlassPanel className="mt-5 p-6">

            <h2 className="text-xl font-semibold">
              Remediation
            </h2>


            <div
              className="
                mt-5
                grid
                gap-4
                lg:grid-cols-2
              "
            >

              {detail.remediation_proposals.map(
                (proposal) => (

                  <div
                    key={proposal.id}
                    className="
                      rounded-2xl
                      border
                      border-white/30
                      bg-white/15
                      p-5
                    "
                  >

                    <div
                      className="
                        flex
                        items-start
                        justify-between
                        gap-3
                      "
                    >

                      <div>
                        <p className="font-semibold">
                          {humanize(
                            proposal.action_key
                          )}
                        </p>

                        <p
                          className="
                            mt-1
                            text-xs
                            text-slate-500
                          "
                        >
                          {proposal.target_service}
                        </p>
                      </div>


                      <Badge
                        text={proposal.status}
                        tone={
                          proposal.status ===
                          "APPROVED"
                            ? "green"
                            : proposal.status ===
                              "REJECTED"
                              ? "red"
                              : "amber"
                        }
                      />

                    </div>


                    <p
                      className="
                        mt-4
                        text-sm
                        leading-6
                        text-slate-700
                      "
                    >
                      {proposal.rationale}
                    </p>

                  </div>

                )
              )}

            </div>

          </GlassPanel>

        )}

      </div>

    </main>
  );
}


function TimelineItem({
  event,
  last,
}: {
  event:
    DashboardTimelineEvent;

  last:
    boolean;
}) {
  const config =
    getEventConfig(
      event.event_type
    );

  const Icon =
    config.icon;


  return (
    <div
      className="
        relative
        flex
        gap-4
        pb-7
      "
    >

      {!last && (
        <div
          className="
            absolute
            left-[19px]
            top-10
            bottom-0
            w-px
            bg-slate-300/60
          "
        />
      )}


      <div
        className={`
          relative
          z-10
          flex
          h-10
          w-10
          shrink-0
          items-center
          justify-center
          rounded-2xl
          ${config.background}
        `}
      >
        <Icon
          className={`
            h-5
            w-5
            ${config.color}
          `}
        />
      </div>


      <div
        className="
          min-w-0
          flex-1
          rounded-2xl
          border
          border-white/25
          bg-white/12
          px-4
          py-3
        "
      >

        <div
          className="
            flex
            justify-between
            gap-4
          "
        >

          <p
            className="
              text-sm
              font-semibold
              text-slate-900
            "
          >
            {humanize(
              event.event_type
            )}
          </p>

          <p
            className="
              whitespace-nowrap
              text-xs
              text-slate-500
            "
          >
            {formatDate(
              event.timestamp
            )}
          </p>

        </div>


        <div
          className="
            mt-2
            flex
            flex-wrap
            gap-x-4
            gap-y-1
          "
        >

          {Object.entries(
            event.details ?? {}
          )
            .slice(0, 5)
            .map(
              ([key, value]) => (

                <span
                  key={key}
                  className="
                    text-xs
                    text-slate-600
                  "
                >
                  <strong>
                    {humanize(key)}:
                  </strong>{" "}
                  {formatValue(value)}
                </span>

              )
            )}

        </div>

      </div>

    </div>
  );
}


function getEventConfig(
  event:
    string
) {
  if (
    event.includes(
      "INVESTIGATION"
    )
  ) {
    return {
      icon: BrainCircuit,
      color: "text-indigo-600",
      background:
        "bg-indigo-100/60",
    };
  }


  if (
    event.includes(
      "PROPOSED"
    )
  ) {
    return {
      icon: Wrench,
      color: "text-amber-600",
      background:
        "bg-amber-100/60",
    };
  }


  if (
    event.includes(
      "APPROVED"
    )
  ) {
    return {
      icon: ShieldCheck,
      color: "text-violet-600",
      background:
        "bg-violet-100/60",
    };
  }


  if (
    event.includes(
      "EXECUTION"
    ) ||
    event.includes(
      "REMEDIATION_SUCCEEDED"
    )
  ) {
    return {
      icon: Zap,
      color: "text-blue-600",
      background:
        "bg-blue-100/60",
    };
  }


  if (
    event.includes(
      "RECOVERY"
    )
  ) {
    return {
      icon: HeartPulse,
      color: "text-emerald-600",
      background:
        "bg-emerald-100/60",
    };
  }


  if (
    event.includes(
      "RESOLVED"
    )
  ) {
    return {
      icon: CheckCircle2,
      color: "text-emerald-600",
      background:
        "bg-emerald-100/60",
    };
  }


  return {
    icon: Activity,
    color: "text-red-600",
    background:
      "bg-red-100/60",
  };
}


function GlassPanel({
  children,
  className = "",
}: {
  children:
    ReactNode;

  className?:
    string;
}) {
  return (
    <section
      className={`
        overflow-hidden
        rounded-[28px]
        border
        border-white/40
        ${className}
      `}
      style={{
        background:
          "rgba(255,255,255,.30)",

        backdropFilter:
          "blur(22px)",

        WebkitBackdropFilter:
          "blur(22px)",
      }}
    >
      {children}
    </section>
  );
}


function InfoCard({
  label,
  value,
}: {
  label:
    string;

  value:
    string;
}) {
  return (
    <div
      className="
        rounded-2xl
        border
        border-white/30
        bg-white/15
        p-4
      "
    >
      <p className="text-xs text-slate-500">
        {label}
      </p>

      <p
        className="
          mt-2
          text-sm
          font-semibold
          text-slate-900
        "
      >
        {value}
      </p>
    </div>
  );
}


function Badge({
  text,
  tone,
}: {
  text:
    string;

  tone:
    "red"
    | "green"
    | "blue"
    | "amber";
}) {
  const styles = {
    red:
      "bg-red-100/55 text-red-700 border-red-200/50",

    green:
      "bg-emerald-100/55 text-emerald-700 border-emerald-200/50",

    blue:
      "bg-indigo-100/55 text-indigo-700 border-indigo-200/50",

    amber:
      "bg-amber-100/55 text-amber-700 border-amber-200/50",
  };


  return (
    <span
      className={`
        inline-flex
        rounded-full
        border
        px-3
        py-1
        text-xs
        font-semibold
        ${styles[tone]}
      `}
    >
      {text}
    </span>
  );
}


function TextList({
  title,
  items,
}: {
  title:
    string;

  items?:
    string[];
}) {
  if (
    !items ||
    items.length === 0
  ) {
    return null;
  }


  return (
    <div className="mt-5">

      <p
        className="
          text-xs
          font-semibold
          uppercase
          tracking-wide
          text-slate-500
        "
      >
        {title}
      </p>


      <div className="mt-2 space-y-2">

        {items.map(
          (
            item,
            index
          ) => (
            <p
              key={index}
              className="
                text-sm
                leading-6
                text-slate-700
              "
            >
              • {item}
            </p>
          )
        )}

      </div>

    </div>
  );
}


function EmptyText({
  text,
}: {
  text:
    string;
}) {
  return (
    <p
      className="
        mt-4
        text-sm
        text-slate-500
      "
    >
      {text}
    </p>
  );
}


function humanize(
  value:
    string
) {
  return value
    .replaceAll(
      "_",
      " "
    )
    .toLowerCase()
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase()
    );
}


function formatValue(
  value:
    unknown
): string {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }


  if (
    typeof value ===
    "object"
  ) {
    return JSON.stringify(
      value
    );
  }


  return String(value);
}


function formatDate(
  value:
    string
    | null
    | undefined
) {
  if (!value) {
    return "—";
  }


  return new Intl.DateTimeFormat(
    "en",
    {
      dateStyle: "medium",
      timeStyle: "short",
    }
  ).format(
    new Date(value)
  );
}