import Link from "next/link";
import { BrainCircuit, CheckCircle2, ChevronRight, DatabaseZap } from "lucide-react";
import { getDashboardInvestigations } from "@/lib/aegisops";
import { MetricPill, PageTitle, Panel, StatusBadge, formatDate } from "@/components/ui";

export const instant = false;

export default async function InvestigationsPage() {
  const investigations = await getDashboardInvestigations(100);
  const high = investigations.filter((item) => item.report?.confidence === "HIGH").length;
  const sufficient = investigations.filter((item) => item.report?.evidence_sufficient === true).length;

  return (
    <div className="mx-auto max-w-[1700px]">
      <PageTitle eyebrow="Agent Analysis" title="Investigations" actions={<><MetricPill label="Total" value={investigations.length} /><MetricPill label="High Confidence" value={high} tone="green" /><MetricPill label="Evidence Ready" value={sufficient} tone="blue" /></>} />
      <div className="grid gap-5 xl:grid-cols-2">
        {investigations.map((investigation) => (
          <Panel key={investigation.id} className="group p-6 transition hover:-translate-y-0.5 hover:shadow-[0_18px_38px_rgba(30,35,55,.055)]">
            <div className="flex items-start justify-between gap-4"><div className="flex min-w-0 gap-3"><div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[#edf0ff]"><BrainCircuit className="h-5 w-5 text-[#5364db]" /></div><div className="min-w-0"><p className="truncate text-sm font-black">{investigation.incident_title}</p><p className="mt-1 text-[10px] font-bold text-[#979aa2]">Investigation #{investigation.id} · Incident #{investigation.incident_id}</p></div></div><StatusBadge text={investigation.report?.confidence ?? "UNKNOWN"} tone={investigation.report?.confidence === "HIGH" ? "green" : investigation.report?.confidence === "MEDIUM" ? "amber" : "neutral"} /></div>
            <p className="mt-5 line-clamp-4 text-sm leading-6 text-[#5f6470]">{investigation.report?.summary ?? "No investigation summary stored."}</p>
            <div className="mt-5 flex flex-wrap items-center gap-2"><StatusBadge text={investigation.incident_severity} tone={investigation.incident_severity === "HIGH" || investigation.incident_severity === "CRITICAL" ? "red" : "amber"} /><StatusBadge text={investigation.incident_status} tone={investigation.incident_status === "RESOLVED" ? "green" : "red"} />{investigation.report?.evidence_sufficient && <span className="flex items-center gap-1 rounded-full bg-[#eaf8f0] px-2.5 py-1 text-[10px] font-black text-[#16875d]"><CheckCircle2 className="h-3 w-3" />Evidence sufficient</span>}</div>
            <div className="mt-5 flex items-center justify-between border-t border-black/[.05] pt-4"><div className="flex items-center gap-2 text-[10px] font-bold text-[#94979e]"><DatabaseZap className="h-3.5 w-3.5" />{investigation.model} · {formatDate(investigation.created_at)}</div><Link href={`/incidents/${investigation.incident_id}`} className="flex items-center gap-1 text-[10px] font-black text-[#5364db]">Open incident <ChevronRight className="h-3.5 w-3.5" /></Link></div>
          </Panel>
        ))}
      </div>
      {investigations.length === 0 && <Panel className="p-12 text-center"><BrainCircuit className="mx-auto h-8 w-8 text-[#aaa]" /><p className="mt-3 text-sm font-black">No investigations stored</p></Panel>}
    </div>
  );
}
