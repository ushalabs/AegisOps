import type { ComponentType } from "react";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  CircleDot,
  FileText,
  ShieldCheck,
  Wrench,
} from "lucide-react";
import { SiGrafana, SiPostgresql, SiPrometheus, SiRedis } from "react-icons/si";
import TimeRangeSelector, { type TimeRange } from "@/components/time-range-selector";
import { Panel, StatusBadge } from "@/components/ui";
import {
  getDashboardIncidents,
  getDashboardOverview,
  type DashboardIncident,
  type DashboardServiceHealth,
} from "@/lib/aegisops";

export const instant = false;

type DashboardIcon = ComponentType<{ className?: string }>;
type TrendPoint = { label: string; detected: number; resolved: number };

const rangeHours: Record<TimeRange, number> = {
  "1h": 1,
  "6h": 6,
  "24h": 24,
  "7d": 168,
};

const serviceVisuals: Record<
  string,
  { icon: DashboardIcon; color: string; background: string }
> = {
  "benchmark-api": {
    icon: Activity,
    color: "text-[#6674ef]",
    background: "bg-[#edf0ff]",
  },
  postgresql: {
    icon: SiPostgresql,
    color: "text-[#336791]",
    background: "bg-[#e8f4fb]",
  },
  redis: {
    icon: SiRedis,
    color: "text-[#d74b3f]",
    background: "bg-[#fff0ec]",
  },
  prometheus: {
    icon: SiPrometheus,
    color: "text-[#e6522c]",
    background: "bg-[#fff1e7]",
  },
  grafana: {
    icon: SiGrafana,
    color: "text-[#f46800]",
    background: "bg-[#fff4dd]",
  },
  cadvisor: {
    icon: Activity,
    color: "text-[#1596a7]",
    background: "bg-[#e9f8f7]",
  },
};

export default async function Dashboard({
  searchParams,
}: {
  searchParams: Promise<{ range?: string }>;
}) {
  const params = await searchParams;

  const selectedRange: TimeRange =
    params.range === "1h" || params.range === "6h" || params.range === "7d"
      ? params.range
      : "24h";

  const [overview, incidents] = await Promise.all([
    getDashboardOverview(rangeHours[selectedRange]),
    getDashboardIncidents(500),
  ]);

  const trend = buildTrendData(incidents, selectedRange);
  const healthyServices = overview.services.filter(
    (service) => service.status === "HEALTHY"
  ).length;
  const closedIncidents = Math.max(
    0,
    overview.counts.total_incidents - overview.counts.open_incidents
  );
  const pipelineTotal = Math.max(
    1,
    overview.counts.investigating +
      overview.counts.pending_approval +
      overview.counts.recovered
  );

  return (
    <div className="w-full px-5 pb-8 sm:px-6 xl:px-9">
      <div className="mb-5 flex justify-end">
        <TimeRangeSelector value={selectedRange} />
      </div>

      <section className="grid gap-5 xl:grid-cols-12">
        <div className="space-y-5 xl:col-span-8">
          <div className="grid gap-5 lg:grid-cols-2">
            <div className="relative overflow-hidden rounded-[30px] bg-gradient-to-br from-[#ff765f] via-[#f65c75] to-[#e849a0] p-7 text-white shadow-[0_22px_46px_rgba(232,73,160,.17)]">
              <div className="absolute -right-8 -top-10 h-40 w-40 rounded-full border-[22px] border-white/10" />

              <div className="relative z-10">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-[19px] text-white">Operations Pulse</p>
                    <p className="mt-5 text-[52px] leading-none tracking-[-.05em]">
                      {overview.counts.open_incidents}
                    </p>
                    <p className="mt-2 text-[13px] text-white/80">open incidents right now</p>
                  </div>

                  <span className="rounded-full bg-white/18 px-3 py-1.5 text-[11px] uppercase tracking-wide">
                    Live
                  </span>
                </div>

                <TrendLines data={trend} />

                <div className="mt-5 grid grid-cols-3 divide-x divide-white/25 border-t border-white/20 pt-4">
                  <HeroMetric label="Investigating" value={overview.counts.investigating} />
                  <HeroMetric label="Approvals" value={overview.counts.pending_approval} />
                  <HeroMetric label="Closed" value={closedIncidents} />
                </div>
              </div>
            </div>

            <Panel className="p-7">
              <div className="flex items-start justify-between">
                <p className="text-[22px] text-[#171b27]">Response Pipeline</p>
                <CircleDot className="h-5 w-5 text-[#aaa7a0]" />
              </div>

              <div className="mt-7 flex items-center justify-between gap-5">
                <PipelineRing
                  investigating={overview.counts.investigating}
                  pending={overview.counts.pending_approval}
                  recovered={overview.counts.recovered}
                  total={pipelineTotal}
                />

                <div className="min-w-[145px] space-y-4">
                  <LegendRow
                    color="bg-[#ff765f]"
                    label="Investigating"
                    value={overview.counts.investigating}
                  />
                  <LegendRow
                    color="bg-[#f5bd3b]"
                    label="Approval"
                    value={overview.counts.pending_approval}
                  />
                  <LegendRow
                    color="bg-[#55cfa0]"
                    label="Recovered"
                    value={overview.counts.recovered}
                  />
                </div>
              </div>
            </Panel>
          </div>

          <Panel className="overflow-hidden">
            <div className="flex flex-col justify-between gap-4 px-6 pb-2 pt-6 sm:flex-row sm:items-start">
              <p className="text-[22px] text-[#111625]">Incident Activity</p>

              <div className="flex gap-4 text-[11px] text-[#777b84]">
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-[#ef4e91]" />
                  Detected
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-[#111625]" />
                  Resolved
                </span>
              </div>
            </div>

            <IncidentChart data={trend} />
          </Panel>
        </div>

        <div className="space-y-5 xl:col-span-4">
          <div className="grid grid-cols-2 gap-5">
            <Panel className="p-4 sm:p-5">
              <div className="flex items-center gap-3">
                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-[20px] bg-[#f8cecb]">
                  <ShieldCheck className="h-6 w-6 text-[#111625]" />
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-[27px] tracking-[-.04em]">
                      {healthyServices}/{overview.services.length}
                    </p>
                    <span className="hidden text-[11px] text-[#55a87f] sm:inline">LIVE</span>
                  </div>
                  <p className="text-[14px] text-[#111625]">Services Healthy</p>
                </div>
              </div>

              <div className="mt-4 h-2 overflow-hidden rounded-full bg-white">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-[#ef4e91] to-[#ff755f]"
                  style={{
                    width: `${
                      overview.services.length
                        ? (healthyServices / overview.services.length) * 100
                        : 0
                    }%`,
                  }}
                />
              </div>
            </Panel>

            <Panel className="flex items-center gap-3 p-4 sm:p-5">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-[20px] bg-[#e6eafc]">
                <FileText className="h-6 w-6 text-[#5364db]" />
              </div>

              <div className="min-w-0 flex-1">
                <p className="text-[27px] tracking-[-.04em]">
                  {overview.counts.postmortems}
                </p>
                <p className="text-[14px] text-[#111625]">Postmortems</p>
              </div>
            </Panel>
          </div>

          <Panel className="p-6">
            <div className="flex items-center justify-between">
              <p className="text-[22px] text-[#111625]">Service Status</p>
              <Activity className="h-5 w-5 text-[#aaa7a0]" />
            </div>

            <div className="mt-5 space-y-3">
              {overview.services.map((service) => (
                <ServiceRow key={service.key} service={service} />
              ))}
            </div>
          </Panel>
        </div>
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-12">
        <Panel className="overflow-hidden xl:col-span-8">
          <div className="flex items-center justify-between px-6 py-5">
            <p className="text-[22px] text-[#111625]">Recent Incidents</p>

            <Link
              href="/incidents"
              className="flex items-center gap-1 text-[13px] text-[#ef4e91]"
            >
              View all
              <ArrowUpRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="px-4 pb-4">
            {overview.recent_incidents.length ? (
              overview.recent_incidents
                .slice(0, 5)
                .map((incident) => <RecentIncident key={incident.id} incident={incident} />)
            ) : (
              <div className="rounded-2xl bg-white/60 p-8 text-center text-sm text-[#8b8e96]">
                No recent incidents in this window.
              </div>
            )}
          </div>
        </Panel>

        <Panel className="relative overflow-hidden p-6 xl:col-span-4">
          <div className="absolute -bottom-16 -right-10 h-44 w-44 rounded-full bg-[#ffd5c9]" />

          <div className="relative z-10">
            <div className="flex items-center justify-between">
              <p className="text-[22px] text-[#111625]">Recovery Summary</p>
              <CheckCircle2 className="h-5 w-5 text-[#55a87f]" />
            </div>

            <p className="mt-8 text-[56px] leading-none tracking-[-.05em]">
              {overview.counts.recovered}
            </p>
            <p className="mt-2 text-[15px] text-[#4b505c]">verified recoveries</p>

            <div className="mt-7 flex items-center gap-3 rounded-2xl bg-white/65 p-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#eaf8f0]">
                <Wrench className="h-4 w-4 text-[#16875d]" />
              </div>
              <p className="text-[14px] text-[#111625]">Human approval preserved</p>
            </div>
          </div>
        </Panel>
      </section>
    </div>
  );
}

function HeroMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="px-3 first:pl-0">
      <p className="text-[11px] text-white/75">{label}</p>
      <p className="mt-1 text-[22px]">{value}</p>
    </div>
  );
}

function TrendLines({ data }: { data: TrendPoint[] }) {
  const max = Math.max(1, ...data.flatMap((point) => [point.detected, point.resolved]));

  const points = (key: "detected" | "resolved") =>
    data
      .map(
        (point, index) =>
          `${(index / Math.max(1, data.length - 1)) * 100},${34 - (point[key] / max) * 26}`
      )
      .join(" ");

  return (
    <svg viewBox="0 0 100 40" className="mt-7 h-20 w-full overflow-visible">
      <polyline
        points={points("detected")}
        fill="none"
        stroke="rgba(255,255,255,.95)"
        strokeWidth="1.1"
        vectorEffect="non-scaling-stroke"
      />
      <polyline
        points={points("resolved")}
        fill="none"
        stroke="rgba(70,38,127,.72)"
        strokeWidth="1.1"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

function PipelineRing({
  investigating,
  pending,
  recovered,
  total,
}: {
  investigating: number;
  pending: number;
  recovered: number;
  total: number;
}) {
  const a = (investigating / total) * 100;
  const b = (pending / total) * 100;

  return (
    <div
      className="relative h-[170px] w-[170px] shrink-0 rounded-full"
      style={{
        background: `conic-gradient(#ff765f 0 ${a}%, #f5bd3b ${a}% ${a + b}%, #55cfa0 ${a + b}% 100%)`,
      }}
    >
      <div className="absolute inset-[14px] flex flex-col items-center justify-center rounded-full bg-[#faf8f4]">
        <p className="text-[32px] tracking-[-.04em]">
          {investigating + pending + recovered}
        </p>
        <p className="text-[11px] uppercase tracking-wide text-[#95989f]">pipeline events</p>
      </div>
    </div>
  );
}

function LegendRow({
  color,
  label,
  value,
}: {
  color: string;
  label: string;
  value: number;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="flex items-center gap-2 text-[13px] text-[#626771]">
        <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
        {label}
      </span>
      <span className="text-[15px]">{value}</span>
    </div>
  );
}

function IncidentChart({ data }: { data: TrendPoint[] }) {
  const max = Math.max(1, ...data.flatMap((point) => [point.detected, point.resolved]));

  return (
    <div className="px-6 pb-6 pt-4">
      <div className="relative h-[280px]">
        <div className="absolute inset-0 flex flex-col justify-between">
          {[0, 1, 2, 3].map((line) => (
            <div key={line} className="border-t border-[#ddd9d1]" />
          ))}
        </div>

        <div className="absolute inset-0 flex items-end gap-3 pt-4">
          {data.map((point, index) => (
            <div
              key={`${point.label}-${index}`}
              className="flex h-full min-w-0 flex-1 flex-col justify-end"
            >
              <div className="flex flex-1 items-end justify-center gap-1.5">
                <div
                  className="w-[26%] max-w-[34px] rounded-t-[10px] bg-gradient-to-t from-[#ef4e91] to-[#ff8a68]"
                  style={{
                    height: `${
                      point.detected === 0
                        ? 2
                        : Math.max(9, (point.detected / max) * 100)
                    }%`,
                  }}
                />
                <div
                  className="w-[26%] max-w-[34px] rounded-t-[10px] bg-[#111625]"
                  style={{
                    height: `${
                      point.resolved === 0
                        ? 2
                        : Math.max(9, (point.resolved / max) * 100)
                    }%`,
                  }}
                />
              </div>
              <p className="mt-2 truncate text-center text-[10px] text-[#94979e]">
                {point.label}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ServiceRow({ service }: { service: DashboardServiceHealth }) {
  const visual = serviceVisuals[service.key] ?? serviceVisuals["benchmark-api"];
  const Icon = visual.icon;
  const tone =
    service.status === "HEALTHY"
      ? "green"
      : service.status === "DEGRADED"
        ? "amber"
        : "red";

  return (
    <div className="flex items-center gap-3 rounded-2xl bg-white/58 p-3.5">
      <div
        className={`flex h-10 w-10 items-center justify-center rounded-xl ${visual.background}`}
      >
        <Icon className={`h-5 w-5 ${visual.color}`} />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <p className="truncate text-[14px] text-[#111625]">{service.name}</p>
          <StatusBadge text={service.status} tone={tone} />
        </div>
        <p className="mt-1 truncate text-[11px] text-[#90939a]">{service.detail}</p>
      </div>
    </div>
  );
}

function RecentIncident({ incident }: { incident: DashboardIncident }) {
  return (
    <Link
      href={`/incidents/${incident.id}`}
      className="group grid grid-cols-[44px_minmax(0,1fr)_130px_100px] items-center gap-3 rounded-2xl px-3 py-3.5 transition hover:bg-white/70"
    >
      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#fff0ec]">
        <AlertTriangle className="h-4 w-4 text-[#e65245]" />
      </div>

      <div className="min-w-0">
        <p className="truncate text-[14px] text-[#111625] group-hover:text-[#ef4e91]">
          {incident.title}
        </p>
        <p className="mt-1 truncate text-[11px] text-[#94979e]">
          #{incident.id} · {incident.service}
        </p>
      </div>

      <StatusBadge
        text={incident.severity}
        tone={incident.severity === "HIGH" || incident.severity === "CRITICAL" ? "red" : "amber"}
      />

      <StatusBadge
        text={incident.status}
        tone={incident.status === "RESOLVED" ? "green" : "red"}
      />
    </Link>
  );
}

function buildTrendData(incidents: DashboardIncident[], range: TimeRange): TrendPoint[] {
  const now = Date.now();
  const config = {
    "1h": { hours: 1, buckets: 6 },
    "6h": { hours: 6, buckets: 6 },
    "24h": { hours: 24, buckets: 8 },
    "7d": { hours: 168, buckets: 7 },
  }[range];

  const start = now - config.hours * 60 * 60 * 1000;
  const bucketSize = (now - start) / config.buckets;

  const result = Array.from({ length: config.buckets }, (_, index) => {
    const date = new Date(start + bucketSize * index);

    return {
      label:
        range === "7d"
          ? new Intl.DateTimeFormat("en", { weekday: "short" }).format(date)
          : new Intl.DateTimeFormat("en", {
              hour: "numeric",
              minute: range === "1h" ? "2-digit" : undefined,
            }).format(date),
      detected: 0,
      resolved: 0,
    };
  });

  const getIndex = (value: string | null | undefined) => {
    if (!value) return null;

    const timestamp = new Date(value).getTime();
    if (timestamp < start || timestamp > now) return null;

    return Math.min(
      config.buckets - 1,
      Math.floor((timestamp - start) / bucketSize)
    );
  };

  for (const incident of incidents) {
    const detected = getIndex(incident.first_detected_at);
    if (detected !== null) result[detected].detected += 1;

    const resolved = getIndex(incident.resolved_at);
    if (resolved !== null) result[resolved].resolved += 1;
  }

  return result;
}
