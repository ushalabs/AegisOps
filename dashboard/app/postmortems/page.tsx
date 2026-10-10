import Link from "next/link";
import { BookOpen, ChevronRight, FileText, Lightbulb } from "lucide-react";
import { getDashboardPostmortems } from "@/lib/aegisops";
import { MetricPill, PageTitle, Panel, StatusBadge, formatDate } from "@/components/ui";

export const instant = false;

export default async function PostmortemsPage() {
  const postmortems = await getDashboardPostmortems(100);
  const highSeverity = postmortems.filter((item) => item.incident_severity === "HIGH" || item.incident_severity === "CRITICAL").length;
  const preventiveActions = postmortems.reduce((total, item) => total + (item.preventive_actions?.length ?? 0), 0);

  return (
    <div className="mx-auto max-w-[1700px]">
      <PageTitle eyebrow="Incident Memory" title="Postmortems" actions={<><MetricPill label="Stored" value={postmortems.length} tone="blue" /><MetricPill label="High Severity" value={highSeverity} tone="red" /><MetricPill label="Actions" value={preventiveActions} tone="green" /></>} />
      <div className="grid gap-5 xl:grid-cols-2">
        {postmortems.map((postmortem) => (
          <Link key={postmortem.id} href={`/postmortems/${postmortem.incident_id}`} className="group block">
            <Panel className="h-full p-6 transition group-hover:-translate-y-0.5 group-hover:shadow-[0_18px_38px_rgba(30,35,55,.055)]">
              <div className="flex items-start justify-between gap-4"><div className="flex min-w-0 gap-3"><div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[#fdebf5]"><BookOpen className="h-5 w-5 text-[#c73f82]" /></div><div className="min-w-0"><p className="truncate text-sm font-black">{postmortem.incident_title ?? `Incident #${postmortem.incident_id}`}</p><p className="mt-1 text-[10px] font-bold text-[#979aa2]">Incident #{postmortem.incident_id} · {postmortem.incident_service ?? "Unknown service"}</p></div></div><ChevronRight className="h-5 w-5 text-[#b0b1b6] transition group-hover:translate-x-1 group-hover:text-[#c73f82]" /></div>
              <p className="mt-5 line-clamp-3 text-sm leading-6 text-[#5f6470]">{postmortem.summary}</p>
              <div className="mt-5 rounded-[20px] bg-white/58 p-4"><div className="flex items-center gap-2"><FileText className="h-4 w-4 text-[#777b84]" /><p className="text-[9px] font-black uppercase tracking-[.12em] text-[#999ca3]">Probable Root Cause</p></div><p className="mt-2 line-clamp-2 text-xs leading-5 text-[#606571]">{postmortem.root_cause ?? "Not established from available evidence."}</p></div>
              <div className="mt-5 flex items-center justify-between border-t border-black/[.05] pt-4"><div className="flex gap-2">{postmortem.incident_severity && <StatusBadge text={postmortem.incident_severity} tone={postmortem.incident_severity === "HIGH" || postmortem.incident_severity === "CRITICAL" ? "red" : "amber"} />}<span className="flex items-center gap-1 rounded-full bg-[#eaf8f0] px-2.5 py-1 text-[10px] font-black text-[#16875d]"><Lightbulb className="h-3 w-3" />{postmortem.preventive_actions?.length ?? 0} actions</span></div><p className="text-[10px] font-bold text-[#979aa2]">{formatDate(postmortem.created_at)}</p></div>
            </Panel>
          </Link>
        ))}
      </div>
      {!postmortems.length && <Panel className="p-14 text-center"><BookOpen className="mx-auto h-8 w-8 text-[#aaa]" /><p className="mt-3 text-sm font-black">No postmortems stored</p></Panel>}
    </div>
  );
}
