import type { ComponentType, ReactNode } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  BrainCircuit,
  CheckCircle2,
  FileText,
  HeartPulse,
  ShieldCheck,
  Wrench,
  Zap,
} from "lucide-react";
import { getDashboardIncidentDetail, type DashboardTimelineEvent } from "@/lib/aegisops";
import { Panel, StatusBadge, formatDate, formatValue, humanize } from "@/components/ui";

export const instant = false;

export default async function IncidentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const incidentId = Number(id);
  if (!Number.isInteger(incidentId)) notFound();
  const detail = await getDashboardIncidentDetail(incidentId);
  if (!detail) notFound();

  const incident = detail.incident;
  const latestInvestigation = detail.investigations.at(-1);
  const latestRecovery = detail.recovery_verifications.at(-1);

  return (
    <div className="mx-auto max-w-[1600px]">
      <Link href="/incidents" className="mb-5 inline-flex items-center gap-2 text-xs font-black text-[#6f747e] hover:text-[#111625]"><ArrowLeft className="h-4 w-4" />Back to incidents</Link>

      <Panel className="relative overflow-hidden p-7">
        <div className="absolute right-0 top-0 h-36 w-36 rounded-bl-[90px] bg-[#fde5e0]" />
        <div className="relative z-10 flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
          <div className="flex items-start gap-4"><div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-[20px] bg-[#fff0ec]"><AlertTriangle className="h-6 w-6 text-[#e65245]" /></div><div><p className="text-[10px] font-black uppercase tracking-[.16em] text-[#9a9ca3]">Incident #{incident.id}</p><h2 className="mt-1 text-[30px] font-black tracking-[-.04em]">{incident.title}</h2><p className="mt-2 text-xs font-bold text-[#747984]">{incident.service} · {incident.rule_key}</p></div></div>
          <div className="flex gap-2"><StatusBadge text={incident.severity} tone={incident.severity === "HIGH" || incident.severity === "CRITICAL" ? "red" : "amber"} /><StatusBadge text={incident.status} tone={incident.status === "RESOLVED" ? "green" : "red"} /></div>
        </div>
        <div className="relative z-10 mt-7 grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><Info label="Detected" value={formatDate(incident.first_detected_at)} /><Info label="Resolved" value={formatDate(incident.resolved_at)} /><Info label="Trigger" value={formatValue(incident.trigger_value)} /><Info label="Threshold" value={formatValue(incident.threshold)} /></div>
      </Panel>

      <section className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_390px]">
        <Panel className="overflow-hidden">
          <div className="border-b border-black/[.05] px-6 py-5"><p className="text-lg font-black">Incident Timeline</p><p className="mt-1 text-xs text-[#8b8e96]">Deterministic lifecycle events from detection through recovery</p></div>
          <div className="p-6">{detail.timeline.map((event, index) => <TimelineItem key={`${event.event_type}-${event.timestamp}-${index}`} event={event} last={index === detail.timeline.length - 1} />)}</div>
        </Panel>

        <div className="space-y-5">
          <SummaryPanel icon={BrainCircuit} title="Latest Investigation" accent="bg-[#edf0ff] text-[#5364db]">
            {latestInvestigation ? <><StatusBadge text={latestInvestigation.report?.confidence ?? "UNKNOWN"} tone="blue" /><p className="mt-4 text-sm leading-6 text-[#5f6470]">{latestInvestigation.report?.summary ?? "No summary available."}</p><p className="mt-4 text-[10px] font-bold text-[#999ca3]">{latestInvestigation.model}</p></> : <Muted>No investigation stored.</Muted>}
          </SummaryPanel>
          <SummaryPanel icon={HeartPulse} title="Recovery" accent="bg-[#eaf8f0] text-[#16875d]">
            {latestRecovery ? <><StatusBadge text={latestRecovery.status} tone={latestRecovery.status === "RECOVERED" ? "green" : "amber"} /><p className="mt-4 text-sm font-bold">{latestRecovery.attempt_count} verification attempts</p><p className="mt-1 text-[10px] text-[#9699a0]">Verified {formatDate(latestRecovery.verified_at)}</p></> : <Muted>No recovery verification stored.</Muted>}
          </SummaryPanel>
          <SummaryPanel icon={FileText} title="Postmortem" accent="bg-[#fdebf5] text-[#c73f82]">
            {detail.postmortem ? <><p className="text-sm leading-6 text-[#5f6470]">{detail.postmortem.summary}</p><Link href={`/postmortems/${incident.id}`} className="mt-4 inline-flex text-xs font-black text-[#c73f82]">Open postmortem →</Link></> : <Muted>No postmortem generated.</Muted>}
          </SummaryPanel>
        </div>
      </section>

      {detail.investigations.length > 0 && <Panel className="mt-5 p-6"><p className="text-lg font-black">Investigation Reports</p><div className="mt-5 grid gap-4 lg:grid-cols-2">{detail.investigations.map((investigation) => <div key={investigation.id} className="rounded-[22px] bg-white/58 p-5"><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-black">Investigation #{investigation.id}</p><p className="mt-1 text-[10px] font-bold text-[#999ca3]">{formatDate(investigation.created_at)}</p></div><StatusBadge text={investigation.report?.confidence ?? "UNKNOWN"} tone="blue" /></div><p className="mt-4 text-sm leading-6 text-[#5f6470]">{investigation.report?.summary ?? "No summary stored."}</p><TextList title="Observations" items={investigation.report?.observations} /><TextList title="Recommended Checks" items={investigation.report?.recommended_checks} /></div>)}</div></Panel>}

      {detail.remediation_proposals.length > 0 && <Panel className="mt-5 p-6"><p className="text-lg font-black">Remediation History</p><div className="mt-5 grid gap-4 lg:grid-cols-2">{detail.remediation_proposals.map((proposal) => <div key={proposal.id} className="rounded-[22px] bg-white/58 p-5"><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-black">{humanize(proposal.action_key)}</p><p className="mt-1 text-[10px] font-bold text-[#999ca3]">{proposal.target_service}</p></div><StatusBadge text={proposal.status} tone={proposal.status === "APPROVED" ? "green" : proposal.status === "REJECTED" ? "red" : "amber"} /></div><p className="mt-4 text-sm leading-6 text-[#5f6470]">{proposal.rationale}</p></div>)}</div></Panel>}
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) { return <div className="rounded-2xl bg-white/62 p-4"><p className="text-[9px] font-black uppercase tracking-[.12em] text-[#9a9ca3]">{label}</p><p className="mt-2 text-xs font-black text-[#242936]">{value}</p></div>; }

function TimelineItem({ event, last }: { event: DashboardTimelineEvent; last: boolean }) {
  const config = getEventConfig(event.event_type); const Icon = config.icon;
  return <div className="relative flex gap-4 pb-7">{!last && <div className="absolute bottom-0 left-[19px] top-10 w-px bg-[#d8d4cd]" />}<div className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl ${config.background}`}><Icon className={`h-4.5 w-4.5 ${config.color}`} /></div><div className="min-w-0 flex-1 rounded-2xl bg-white/58 px-4 py-3"><div className="flex flex-col justify-between gap-1 sm:flex-row sm:items-center"><p className="text-xs font-black">{humanize(event.event_type)}</p><p className="text-[10px] font-bold text-[#999ca3]">{formatDate(event.timestamp)}</p></div><div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">{Object.entries(event.details ?? {}).slice(0, 5).map(([key, value]) => <span key={key} className="text-[10px] text-[#777b84]"><strong>{humanize(key)}:</strong> {formatValue(value)}</span>)}</div></div></div>;
}

function getEventConfig(event: string): { icon: ComponentType<{ className?: string }>; color: string; background: string } {
  if (event.includes("INVESTIGATION")) return { icon: BrainCircuit, color: "text-[#5364db]", background: "bg-[#edf0ff]" };
  if (event.includes("PROPOSED")) return { icon: Wrench, color: "text-[#a56a08]", background: "bg-[#fff4d1]" };
  if (event.includes("APPROVED")) return { icon: ShieldCheck, color: "text-[#c73f82]", background: "bg-[#fdebf5]" };
  if (event.includes("EXECUTION") || event.includes("REMEDIATION_SUCCEEDED")) return { icon: Zap, color: "text-[#5364db]", background: "bg-[#edf0ff]" };
  if (event.includes("RECOVERY") || event.includes("RESOLVED")) return { icon: CheckCircle2, color: "text-[#16875d]", background: "bg-[#eaf8f0]" };
  return { icon: Activity, color: "text-[#e65245]", background: "bg-[#fff0ec]" };
}

function SummaryPanel({ icon: Icon, title, accent, children }: { icon: ComponentType<{ className?: string }>; title: string; accent: string; children: ReactNode }) { return <Panel className="p-5"><div className="flex items-center gap-3"><div className={`flex h-10 w-10 items-center justify-center rounded-2xl ${accent}`}><Icon className="h-4.5 w-4.5" /></div><p className="text-sm font-black">{title}</p></div><div className="mt-4">{children}</div></Panel>; }
function Muted({ children }: { children: ReactNode }) { return <p className="text-xs text-[#94979e]">{children}</p>; }
function TextList({ title, items }: { title: string; items?: string[] }) { if (!items?.length) return null; return <div className="mt-4"><p className="text-[9px] font-black uppercase tracking-[.12em] text-[#999ca3]">{title}</p><div className="mt-2 space-y-1.5">{items.map((item, index) => <p key={index} className="text-xs leading-5 text-[#656a75]">• {item}</p>)}</div></div>; }
