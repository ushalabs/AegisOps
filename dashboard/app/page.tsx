import type {
  ComponentType,
  ReactNode,
} from "react";

import Link from "next/link";

import {
  Activity,
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  Clock3,
  Server,
  Wrench,
} from "lucide-react";

import {
  SiGrafana,
  SiPostgresql,
  SiPrometheus,
  SiRedis,
} from "react-icons/si";

import TimeRangeSelector, {
  type TimeRange,
} from "../components/time-range-selector";

import {
  getDashboardIncidents,
  getDashboardOverview,
  type DashboardIncident,
  type DashboardServiceHealth,
} from "../lib/aegisops";


export const instant = false;


type DashboardIcon = ComponentType<{
  className?: string;
}>;


type TrendPoint = {
  label: string;
  detected: number;
  resolved: number;
};


const rangeHours: Record<
  TimeRange,
  number
> = {
  "1h": 1,
  "6h": 6,
  "24h": 24,
  "7d": 168,
};


const serviceVisuals = {
  "benchmark-api": {
    icon: Server,
    color: "text-indigo-600",
    background: "bg-indigo-100/60",
  },

  postgresql: {
    icon: SiPostgresql,
    color: "text-[#336791]",
    background: "bg-sky-100/60",
  },

  redis: {
    icon: SiRedis,
    color: "text-[#DC382D]",
    background: "bg-red-100/60",
  },

  prometheus: {
    icon: SiPrometheus,
    color: "text-[#E6522C]",
    background: "bg-orange-100/60",
  },

  grafana: {
    icon: SiGrafana,
    color: "text-[#F46800]",
    background: "bg-amber-100/60",
  },

  cadvisor: {
    icon: Activity,
    color: "text-cyan-600",
    background: "bg-cyan-100/60",
  },
};


const fallbackServiceVisual = {
  icon: Activity,
  color: "text-indigo-600",
  background: "bg-indigo-100/60",
};


export default async function Dashboard({
  searchParams,
}: {
  searchParams: Promise<{
    range?: string;
  }>;
}) {
  const params =
    await searchParams;


  const selectedRange: TimeRange =
    params.range === "1h" ||
    params.range === "6h" ||
    params.range === "7d"
      ? params.range
      : "24h";


  const [
    overview,
    incidents,
  ] = await Promise.all([
    getDashboardOverview(
      rangeHours[selectedRange]
    ),

    getDashboardIncidents(500),
  ]);


  const trend =
    buildTrendData(
      incidents,
      selectedRange
    );


  const allSystemsHealthy =
    overview.services.length > 0 &&
    overview.services.every(
      (service) =>
        service.status ===
        "HEALTHY"
    );


  const hasUnhealthyService =
    overview.services.some(
      (service) =>
        service.status ===
        "UNHEALTHY"
    );


  const operations = [
    {
      label: "Open Incidents",
      value:
        overview.counts
          .open_incidents,
      note: "Currently active",
      icon: AlertTriangle,
      tone: "rose" as const,
    },

    {
      label: "Investigating",
      value:
        overview.counts
          .investigating,
      note: "Agent investigations",
      icon: Clock3,
      tone: "amber" as const,
    },

    {
      label: "Pending Approval",
      value:
        overview.counts
          .pending_approval,
      note:
        "Awaiting operator review",
      icon: Wrench,
      tone: "indigo" as const,
    },

    {
      label: "Recovered",
      value:
        overview.counts
          .recovered,
      note: "Verified recoveries",
      icon: CheckCircle2,
      tone: "emerald" as const,
    },

    {
      label: "Postmortems",
      value:
        overview.counts
          .postmortems,
      note:
        "Stored incident memories",
      icon: BookOpen,
      tone: "violet" as const,
    },
  ];


  return (
    <div
      className="
        mx-auto
        w-full
        max-w-[1700px]
        space-y-5
      "
    >

      {/* ================================================= */}
      {/* SYSTEM OVERVIEW                                   */}
      {/* ================================================= */}

      <GlassCard>

        <div
          className="
            flex
            flex-col
            justify-between
            gap-4
            border-b
            border-white/25
            px-6
            py-5
            sm:flex-row
            sm:items-center
          "
        >

          <div
            className="
              flex
              items-center
              gap-4
            "
          >

            <div
              className="
                flex
                h-12
                w-12
                shrink-0
                items-center
                justify-center
                rounded-[17px]
                bg-gradient-to-br
                from-violet-500
                to-indigo-600
                shadow-[0_12px_28px_rgba(99,102,241,0.22)]
              "
            >
              <Activity
                className="
                  h-6
                  w-6
                  text-white
                "
              />
            </div>


            <div>

              <h1
                className="
                  text-[22px]
                  font-semibold
                  tracking-[-0.025em]
                  text-slate-950
                "
              >
                System Overview
              </h1>


              <p
                className="
                  mt-1
                  text-xs
                  text-slate-600
                "
              >
                Real-time infrastructure health
              </p>

            </div>

          </div>


          <SystemHealthBadge
            allHealthy={
              allSystemsHealthy
            }
            hasUnhealthy={
              hasUnhealthyService
            }
          />

        </div>


        <div
          className="
            grid
            gap-4
            px-5
            pb-5
            pt-4
            sm:grid-cols-2
            lg:grid-cols-3
            xl:grid-cols-6
          "
        >

          {overview.services.map(
            (service) => {
              const visual =
                serviceVisuals[
                  service.key as keyof typeof serviceVisuals
                ] ??
                fallbackServiceVisual;


              return (
                <ServiceCard
                  key={service.key}
                  service={service}
                  icon={visual.icon}
                  iconColor={
                    visual.color
                  }
                  iconBackground={
                    visual.background
                  }
                />
              );
            }
          )}

        </div>

      </GlassCard>


      {/* ================================================= */}
      {/* INCIDENT ACTIVITY + OPERATIONS                    */}
      {/* ================================================= */}

      <section
        className="
          grid
          gap-5
          xl:grid-cols-[minmax(0,1fr)_360px]
          xl:items-stretch
        "
      >

        {/* INCIDENT ACTIVITY */}

        <GlassCard
          className="
            flex
            min-h-[520px]
            flex-col
          "
        >

          <div
            className="
              flex
              flex-col
              justify-between
              gap-4
              border-b
              border-white/25
              px-6
              pb-4
              pt-5
              sm:flex-row
              sm:items-start
            "
          >

            <div>

              <h2
                className="
                  text-[22px]
                  font-semibold
                  tracking-[-0.025em]
                  text-slate-950
                "
              >
                Incident Activity
              </h2>


              <p
                className="
                  mt-1
                  text-xs
                  text-slate-600
                "
              >
                Detected and resolved incidents
              </p>

            </div>


            <div
              className="
                flex
                items-center
                gap-4
                text-[11px]
                font-medium
                text-slate-700
              "
            >

              <span
                className="
                  flex
                  items-center
                  gap-1.5
                "
              >
                <span
                  className="
                    h-2.5
                    w-2.5
                    rounded-full
                    bg-indigo-500
                  "
                />

                Detected
              </span>


              <span
                className="
                  flex
                  items-center
                  gap-1.5
                "
              >
                <span
                  className="
                    h-2.5
                    w-2.5
                    rounded-full
                    bg-emerald-400
                  "
                />

                Resolved
              </span>

            </div>

          </div>


          <div className="flex-1">

            <IncidentChart
              data={trend}
            />

          </div>

        </GlassCard>


        {/* OPERATIONS */}

        <GlassCard
          className="
            flex
            h-full
            flex-col
          "
        >

          <div
            className="
              border-b
              border-white/25
              px-5
              py-5
            "
          >

            <div>

              <h2
                className="
                  text-[22px]
                  font-semibold
                  tracking-[-0.025em]
                  text-slate-950
                "
              >
                Operations
              </h2>


              <p
                className="
                  mt-1
                  text-xs
                  text-slate-600
                "
              >
                Incident operations
              </p>

            </div>


            <div className="mt-4">

              <TimeRangeSelector
                value={
                  selectedRange
                }
              />

            </div>

          </div>


          <div
            className="
              flex
              flex-1
              flex-col
              justify-between
              gap-3
              p-4
            "
          >

            {operations.map(
              (operation) => (
                <OperationRow
                  key={
                    operation.label
                  }
                  {...operation}
                />
              )
            )}

          </div>

        </GlassCard>

      </section>


      {/* ================================================= */}
      {/* LOWER PANELS                                      */}
      {/* ================================================= */}

      <section
        className="
          grid
          gap-5
          xl:grid-cols-2
        "
      >

        <Panel
          title="Active Incidents"
          href="/incidents"
          action="View all"
        >

          <ActiveIncidents
            incidents={
              overview.active_incidents
            }
          />

        </Panel>


        <Panel
          title="Recent Activity"
          href="/incidents"
          action="View all"
        >

          <RecentActivity
            incidents={
              overview.recent_incidents
            }
          />

        </Panel>

      </section>

    </div>
  );
}


/* ========================================================= */
/* GLASS CARD                                                */
/* ========================================================= */


function GlassCard({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={[
        `
          overflow-hidden
          rounded-[28px]
          border
          border-white/30
        `,
        className,
      ].join(" ")}
      style={{
        background:
          `
            linear-gradient(
              135deg,
              rgba(255,255,255,0.22),
              rgba(255,255,255,0.10)
            )
          `,

        backdropFilter:
          "blur(22px)",

        WebkitBackdropFilter:
          "blur(22px)",

        boxShadow:
          `
            inset 0 1px 0 rgba(255,255,255,0.38),
            0 18px 55px rgba(53,42,76,0.08)
          `,
      }}
    >
      {children}
    </section>
  );
}


/* ========================================================= */
/* SYSTEM STATUS                                             */
/* ========================================================= */


function SystemHealthBadge({
  allHealthy,
  hasUnhealthy,
}: {
  allHealthy: boolean;
  hasUnhealthy: boolean;
}) {
  const style =
    allHealthy
      ? (
        "border-emerald-300/60 "
        + "bg-emerald-100/55 "
        + "text-emerald-800"
      )
      : hasUnhealthy
        ? (
          "border-red-300/60 "
          + "bg-red-100/55 "
          + "text-red-800"
        )
        : (
          "border-amber-300/60 "
          + "bg-amber-100/55 "
          + "text-amber-800"
        );


  const dot =
    allHealthy
      ? "bg-emerald-500"
      : hasUnhealthy
        ? "bg-red-500"
        : "bg-amber-500";


  const text =
    allHealthy
      ? "All Systems Healthy"
      : hasUnhealthy
        ? "Issues Detected"
        : "Degraded";


  return (
    <span
      className={`
        inline-flex
        items-center
        gap-2
        rounded-full
        border
        px-3.5
        py-1.5
        text-[11px]
        font-semibold
        backdrop-blur-xl
        ${style}
      `}
    >

      <span
        className={`
          h-2
          w-2
          rounded-full
          ${dot}
        `}
      />

      {text}

    </span>
  );
}


/* ========================================================= */
/* SERVICE CARD                                              */
/* ========================================================= */


function ServiceCard({
  service,
  icon: Icon,
  iconColor,
  iconBackground,
}: {
  service: DashboardServiceHealth;
  icon: DashboardIcon;
  iconColor: string;
  iconBackground: string;
}) {
  const healthy =
    service.status ===
    "HEALTHY";


  const degraded =
    service.status ===
    "DEGRADED";


  const statusText =
    healthy
      ? "Healthy"
      : degraded
        ? "Degraded"
        : "Unhealthy";


  const statusColor =
    healthy
      ? "text-emerald-700"
      : degraded
        ? "text-amber-700"
        : "text-red-700";


  const dotColor =
    healthy
      ? "bg-emerald-500"
      : degraded
        ? "bg-amber-500"
        : "bg-red-500";


  const footerBackground =
    healthy
      ? "bg-emerald-50/28"
      : degraded
        ? "bg-amber-50/30"
        : "bg-red-50/30";


  return (
    <div
      className="
        flex
        min-h-[150px]
        flex-col
        justify-between
        rounded-[24px]
        border
        border-white/28
        px-4
        py-4
        transition
        duration-300
        hover:-translate-y-1
        hover:border-white/45
        hover:bg-white/22
        hover:shadow-[0_16px_34px_rgba(53,42,76,0.10)]
      "
      style={{
        background:
          "rgba(255,255,255,0.14)",

        backdropFilter:
          "blur(16px)",

        WebkitBackdropFilter:
          "blur(16px)",

        boxShadow:
          `
            inset 0 1px 0 rgba(255,255,255,0.24)
          `,
      }}
    >

      <div>

        <div
          className="
            flex
            items-start
            justify-between
            gap-3
          "
        >

          <div
            className={`
              flex
              h-[52px]
              w-[52px]
              shrink-0
              items-center
              justify-center
              rounded-[18px]
              ${iconBackground}
            `}
          >

            <Icon
              className={`
                h-7
                w-7
                ${iconColor}
              `}
            />

          </div>


          <span
            className={`
              mt-1
              flex
              shrink-0
              items-center
              gap-1.5
              rounded-full
              bg-white/18
              px-2.5
              py-1.5
              text-[10px]
              font-semibold
              backdrop-blur-xl
              ${statusColor}
            `}
          >

            <span
              className={`
                h-2
                w-2
                rounded-full
                ${dotColor}
              `}
            />

            {statusText}

          </span>

        </div>


        <p
          className="
            mt-4
            truncate
            text-[15px]
            font-semibold
            tracking-[-0.01em]
            text-slate-900
          "
        >
          {service.name}
        </p>

      </div>


      <div
        className={`
          mt-4
          rounded-[14px]
          border
          border-white/25
          px-3
          py-2.5
          backdrop-blur-lg
          ${footerBackground}
        `}
      >

        <p
          className="
            truncate
            text-[11px]
            font-medium
            text-slate-600
          "
          title={
            service.detail
          }
        >
          {service.detail}
        </p>

      </div>

    </div>
  );
}


/* ========================================================= */
/* OPERATIONS                                                */
/* ========================================================= */


function OperationRow({
  label,
  value,
  note,
  icon: Icon,
  tone,
}: {
  label: string;
  value: number;
  note: string;
  icon: DashboardIcon;

  tone:
    | "rose"
    | "amber"
    | "indigo"
    | "emerald"
    | "violet";
}) {
  const tones = {
    rose: {
      icon:
        "text-rose-600",

      iconBackground:
        "bg-rose-100/60",

      accent:
        "bg-rose-400",
    },

    amber: {
      icon:
        "text-amber-600",

      iconBackground:
        "bg-amber-100/60",

      accent:
        "bg-amber-400",
    },

    indigo: {
      icon:
        "text-indigo-600",

      iconBackground:
        "bg-indigo-100/60",

      accent:
        "bg-indigo-500",
    },

    emerald: {
      icon:
        "text-emerald-600",

      iconBackground:
        "bg-emerald-100/60",

      accent:
        "bg-emerald-400",
    },

    violet: {
      icon:
        "text-violet-600",

      iconBackground:
        "bg-violet-100/60",

      accent:
        "bg-violet-500",
    },
  };


  const style =
    tones[tone];


  return (
    <div
      className="
        group
        relative
        overflow-hidden
        rounded-[20px]
        border
        border-white/25
        px-4
        py-3.5
        transition
        duration-300
        hover:border-white/40
        hover:bg-white/20
      "
      style={{
        background:
          "rgba(255,255,255,0.13)",

        backdropFilter:
          "blur(14px)",

        WebkitBackdropFilter:
          "blur(14px)",
      }}
    >

      <div
        className={`
          absolute
          bottom-0
          left-0
          top-0
          w-[3px]
          opacity-75
          ${style.accent}
        `}
      />


      <div
        className="
          flex
          items-center
          gap-3
        "
      >

        <div
          className={`
            flex
            h-11
            w-11
            shrink-0
            items-center
            justify-center
            rounded-[15px]
            ${style.iconBackground}
          `}
        >

          <Icon
            className={`
              h-5
              w-5
              ${style.icon}
            `}
          />

        </div>


        <div
          className="
            min-w-0
            flex-1
          "
        >

          <div
            className="
              flex
              items-center
              justify-between
              gap-3
            "
          >

            <p
              className="
                truncate
                text-[12px]
                font-medium
                text-slate-700
              "
            >
              {label}
            </p>


            <p
              className="
                text-[25px]
                font-semibold
                leading-none
                tracking-tight
                text-slate-950
              "
            >
              {value}
            </p>

          </div>


          <p
            className="
              mt-1
              truncate
              text-[10px]
              text-slate-600
            "
          >
            {note}
          </p>

        </div>

      </div>

    </div>
  );
}


/* ========================================================= */
/* INCIDENT CHART                                            */
/* ========================================================= */


function IncidentChart({
  data,
}: {
  data: TrendPoint[];
}) {
  const max = Math.max(
    1,

    ...data.flatMap(
      (point) => [
        point.detected,
        point.resolved,
      ]
    )
  );


  const detectedTotal =
    data.reduce(
      (
        total,
        item
      ) =>
        total +
        item.detected,
      0
    );


  const resolvedTotal =
    data.reduce(
      (
        total,
        item
      ) =>
        total +
        item.resolved,
      0
    );


  return (
    <div
      className="
        px-6
        pb-6
        pt-4
      "
    >

      <div
        className="
          mb-5
          flex
          items-end
          gap-8
        "
      >

        <div>

          <p
            className="
              text-xs
              text-slate-600
            "
          >
            Detected
          </p>


          <p
            className="
              mt-1
              text-[28px]
              font-semibold
              tracking-tight
              text-slate-950
            "
          >
            {detectedTotal}
          </p>

        </div>


        <div>

          <p
            className="
              text-xs
              text-slate-600
            "
          >
            Resolved
          </p>


          <p
            className="
              mt-1
              text-[28px]
              font-semibold
              tracking-tight
              text-slate-950
            "
          >
            {resolvedTotal}
          </p>

        </div>

      </div>


      <div
        className="
          relative
          h-[330px]
        "
      >

        <div
          className="
            absolute
            inset-0
            flex
            flex-col
            justify-between
          "
        >

          {[0, 1, 2, 3].map(
            (line) => (
              <div
                key={line}
                className="
                  border-t
                  border-dashed
                  border-slate-400/35
                "
              />
            )
          )}

        </div>


        <div
          className="
            absolute
            inset-0
            flex
            items-end
            gap-3
            pt-6
          "
        >

          {data.map(
            (
              point,
              index
            ) => {
              const detectedHeight =
                point.detected === 0
                  ? 2
                  : Math.max(
                      10,
                      (
                        point.detected /
                        max
                      ) * 100
                    );


              const resolvedHeight =
                point.resolved === 0
                  ? 2
                  : Math.max(
                      10,
                      (
                        point.resolved /
                        max
                      ) * 100
                    );


              return (
                <div
                  key={
                    `${point.label}-${index}`
                  }
                  className="
                    flex
                    h-full
                    min-w-0
                    flex-1
                    flex-col
                    justify-end
                  "
                >

                  <div
                    className="
                      flex
                      flex-1
                      items-end
                      justify-center
                      gap-1.5
                    "
                  >

                    <div
                      className="
                        w-[34%]
                        max-w-[42px]
                        rounded-t-[10px]
                        bg-gradient-to-t
                        from-indigo-600
                        to-violet-300
                        shadow-[0_7px_18px_rgba(99,102,241,0.18)]
                      "
                      style={{
                        height:
                          `${detectedHeight}%`,
                      }}
                    />


                    <div
                      className="
                        w-[34%]
                        max-w-[42px]
                        rounded-t-[10px]
                        bg-gradient-to-t
                        from-emerald-500
                        to-emerald-200
                      "
                      style={{
                        height:
                          `${resolvedHeight}%`,
                      }}
                    />

                  </div>


                  <p
                    className="
                      mt-2
                      truncate
                      text-center
                      text-[10px]
                      text-slate-600
                    "
                  >
                    {point.label}
                  </p>

                </div>
              );
            }
          )}

        </div>

      </div>

    </div>
  );
}


/* ========================================================= */
/* LOWER PANELS                                              */
/* ========================================================= */


function Panel({
  title,
  href,
  action,
  children,
}: {
  title: string;
  href: string;
  action: string;
  children: ReactNode;
}) {
  return (
    <GlassCard>

      <div
        className="
          flex
          items-center
          justify-between
          border-b
          border-white/25
          px-5
          py-4
        "
      >

        <h2
          className="
            text-base
            font-semibold
            text-slate-950
          "
        >
          {title}
        </h2>


        <Link
          href={href}
          className="
            rounded-full
            border
            border-white/25
            bg-white/16
            px-3
            py-1.5
            text-[11px]
            font-semibold
            text-slate-700
            backdrop-blur-lg
            transition
            hover:bg-white/28
          "
        >
          {action} →
        </Link>

      </div>


      {children}

    </GlassCard>
  );
}


/* ========================================================= */
/* ACTIVE INCIDENTS                                          */
/* ========================================================= */


function ActiveIncidents({
  incidents,
}: {
  incidents:
    DashboardIncident[];
}) {
  if (
    incidents.length === 0
  ) {
    return (
      <div
        className="
          flex
          min-h-[200px]
          items-center
          justify-center
          px-6
        "
      >

        <div
          className="
            text-center
          "
        >

          <div
            className="
              mx-auto
              flex
              h-12
              w-12
              items-center
              justify-center
              rounded-full
              border
              border-emerald-200/40
              bg-emerald-100/45
              backdrop-blur-lg
            "
          >

            <CheckCircle2
              className="
                h-6
                w-6
                text-emerald-600
              "
            />

          </div>


          <p
            className="
              mt-3
              text-sm
              font-semibold
              text-slate-800
            "
          >
            No active incidents
          </p>


          <p
            className="
              mt-1
              text-xs
              text-slate-600
            "
          >
            All monitored systems are currently resolved.
          </p>

        </div>

      </div>
    );
  }


  return (
    <div
      className="
        divide-y
        divide-white/20
      "
    >

      {incidents
        .slice(0, 5)
        .map(
          (incident) => (
            <div
              key={
                incident.id
              }
              className="
                flex
                items-center
                justify-between
                gap-4
                px-5
                py-4
                transition
                hover:bg-white/12
              "
            >

              <div
                className="
                  min-w-0
                "
              >

                <p
                  className="
                    truncate
                    text-sm
                    font-semibold
                    text-slate-900
                  "
                >
                  {incident.title}
                </p>


                <p
                  className="
                    mt-1
                    truncate
                    text-xs
                    text-slate-600
                  "
                >
                  #{incident.id}
                  {" · "}
                  {incident.service}
                </p>

              </div>


              <IncidentStatusBadge
                status={
                  incident.status
                }
              />

            </div>
          )
        )}

    </div>
  );
}


/* ========================================================= */
/* RECENT ACTIVITY                                           */
/* ========================================================= */


function RecentActivity({
  incidents,
}: {
  incidents:
    DashboardIncident[];
}) {
  if (
    incidents.length === 0
  ) {
    return (
      <div
        className="
          flex
          min-h-[200px]
          items-center
          justify-center
          px-6
        "
      >

        <div
          className="text-center">

          <div
            className="
              mx-auto
              flex
              h-12
              w-12
              items-center
              justify-center
              rounded-full
              border
              border-indigo-200/35
              bg-indigo-100/42
              backdrop-blur-lg
            "
          >

            <Activity
              className="
                h-6
                w-6
                text-indigo-600
              "
            />

          </div>


          <p
            className="
              mt-3
              text-sm
              font-semibold
              text-slate-800
            "
          >
            No recent activity
          </p>

        </div>

      </div>
    );
  }


  return (
    <div
      className="
        divide-y
        divide-white/20
      "
    >

      {incidents
        .slice(0, 5)
        .map(
          (incident) => (
            <div
              key={
                incident.id
              }
              className="
                flex
                items-center
                justify-between
                gap-4
                px-5
                py-4
                transition
                hover:bg-white/12
              "
            >

              <div
                className="
                  min-w-0
                "
              >

                <p
                  className="
                    truncate
                    text-sm
                    font-semibold
                    text-slate-900
                  "
                >
                  {incident.title}
                </p>


                <p
                  className="
                    mt-1
                    truncate
                    text-xs
                    text-slate-600
                  "
                >
                  #{incident.id}
                  {" · "}
                  {incident.service}
                </p>

              </div>


              <IncidentStatusBadge
                status={
                  incident.status
                }
              />

            </div>
          )
        )}

    </div>
  );
}


/* ========================================================= */
/* INCIDENT STATUS                                           */
/* ========================================================= */


function IncidentStatusBadge({
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
        + "bg-red-100/42 "
        + "text-red-700"
      )
      : normalized === "RESOLVED"
        ? (
          "border-emerald-200/40 "
          + "bg-emerald-100/42 "
          + "text-emerald-700"
        )
        : (
          "border-indigo-200/40 "
          + "bg-indigo-100/42 "
          + "text-indigo-700"
        );


  return (
    <span
      className={`
        shrink-0
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
/* TREND DATA                                                */
/* ========================================================= */


function buildTrendData(
  incidents:
    DashboardIncident[],

  range:
    TimeRange
): TrendPoint[] {
  const now =
    Date.now();


  const config = {
    "1h": {
      hours: 1,
      buckets: 6,
    },

    "6h": {
      hours: 6,
      buckets: 6,
    },

    "24h": {
      hours: 24,
      buckets: 8,
    },

    "7d": {
      hours: 168,
      buckets: 7,
    },
  }[range];


  const start =
    now -
    config.hours *
      60 *
      60 *
      1000;


  const bucketSize =
    (
      now -
      start
    ) /
    config.buckets;


  const result:
    TrendPoint[] =
      Array.from(
        {
          length:
            config.buckets,
        },

        (
          _,
          index
        ) => {
          const bucketStart =
            start +
            bucketSize *
              index;


          const date =
            new Date(
              bucketStart
            );


          const label =
            range === "7d"
              ? new Intl.DateTimeFormat(
                  "en",
                  {
                    weekday:
                      "short",
                  }
                ).format(
                  date
                )
              : new Intl.DateTimeFormat(
                  "en",
                  {
                    hour:
                      "numeric",

                    minute:
                      range ===
                      "1h"
                        ? "2-digit"
                        : undefined,
                  }
                ).format(
                  date
                );


          return {
            label,
            detected: 0,
            resolved: 0,
          };
        }
      );


  function getIndex(
    value:
      | string
      | null
      | undefined
  ) {
    if (!value) {
      return null;
    }


    const timestamp =
      new Date(
        value
      ).getTime();


    if (
      timestamp < start ||
      timestamp > now
    ) {
      return null;
    }


    return Math.min(
      config.buckets - 1,

      Math.floor(
        (
          timestamp -
          start
        ) /
          bucketSize
      )
    );
  }


  for (
    const incident
    of incidents
  ) {
    const detectedIndex =
      getIndex(
        incident
          .first_detected_at
      );


    if (
      detectedIndex !== null
    ) {
      result[
        detectedIndex
      ].detected += 1;
    }


    const resolvedIndex =
      getIndex(
        incident
          .resolved_at
      );


    if (
      resolvedIndex !== null
    ) {
      result[
        resolvedIndex
      ].resolved += 1;
    }
  }


  return result;
}