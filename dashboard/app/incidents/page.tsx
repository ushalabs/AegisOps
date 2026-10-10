import Link from "next/link";
import { AlertTriangle, CheckCircle2, ChevronRight } from "lucide-react";
import { getDashboardIncidents } from "@/lib/aegisops";
import { MetricPill, PageTitle, Panel, StatusBadge, formatDate } from "@/components/ui";

export const instant = false;

export default async function IncidentsPage() {
  const incidents = await getDashboardIncidents(100);
  const open = incidents.filter((incident) => incident.status === "OPEN").length;
  const resolved = incidents.filter((incident) => incident.status === "RESOLVED").length;
  const high = incidents.filter((incident) => ["HIGH", "CRITICAL"].includes(incident.severity)).length;

  return (
    <div className="mx-auto max-w-[1700px]">
      <PageTitle eyebrow="Incident Operations" title="Incidents" actions={<><MetricPill label="Open" value={open} tone="red" /><MetricPill label="Resolved" value={resolved} tone="green" /><MetricPill label="High Severity" value={high} tone="amber" /></>} />
      <Panel className="overflow-hidden">
        <div className="flex items-center justify-between px-6 py-5"><div><p className="text-lg font-black">Incident History</p><p className="mt-1 text-xs text-[#8b8e96]">{incidents.length} incidents loaded</p></div><div className="hidden items-center gap-2 rounded-full bg-white px-3 py-2 text-[10px] font-black uppercase tracking-wide text-[#5f6470] sm:flex"><span className="h-2 w-2 rounded-full bg-[#55cfa0]" />Live records</div></div>
        {incidents.length === 0 ? <div className="flex min-h-[360px] items-center justify-center text-center"><div><div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#eaf8f0]"><CheckCircle2 className="h-6 w-6 text-[#16875d]" /></div><p className="mt-4 text-sm font-black">No incidents found</p></div></div> : (
          <div className="aegis-scrollbar overflow-x-auto px-4 pb-4">
            <div className="min-w-[1120px]">
              <div className="grid grid-cols-[70px_minmax(280px,1.8fr)_180px_100px_120px_175px_32px] gap-4 px-4 py-3 text-[9px] font-black uppercase tracking-[.12em] text-[#999ca3]"><div>ID</div><div>Incident</div><div>Service</div><div>Severity</div><div>Status</div><div>Detected</div><div /></div>
              <div className="space-y-2">{incidents.map((incident) => (
                <Link key={incident.id} href={`/incidents/${incident.id}`} className="group grid grid-cols-[70px_minmax(280px,1.8fr)_180px_100px_120px_175px_32px] items-center gap-4 rounded-[20px] bg-white/58 px-4 py-3.5 transition hover:bg-white hover:shadow-[0_12px_30px_rgba(30,35,55,.05)]">
                  <span className="text-xs font-bold text-[#737783]">#{incident.id}</span>
                  <div className="flex min-w-0 items-center gap-3"><div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#fff0ec]"><AlertTriangle className="h-4 w-4 text-[#e65245]" /></div><span className="truncate text-xs font-black text-[#1f2431] group-hover:text-[#5364db]">{incident.title}</span></div>
                  <span className="truncate text-xs font-semibold text-[#656a75]">{incident.service}</span>
                  <StatusBadge text={incident.severity} tone={incident.severity === "CRITICAL" || incident.severity === "HIGH" ? "red" : "amber"} />
                  <StatusBadge text={incident.status} tone={incident.status === "RESOLVED" ? "green" : "red"} />
                  <span className="text-[11px] font-semibold text-[#777b84]">{formatDate(incident.first_detected_at)}</span>
                  <ChevronRight className="h-4 w-4 text-[#b1b2b7] transition group-hover:translate-x-1 group-hover:text-[#5364db]" />
                </Link>
              ))}</div>
            </div>
          </div>
        )}
      </Panel>
    </div>
  );
}
