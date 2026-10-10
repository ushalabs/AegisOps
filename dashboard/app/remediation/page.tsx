import Link from "next/link";
import { CheckCircle2, ShieldCheck, Wrench, XCircle } from "lucide-react";
import { getDashboardRemediations } from "@/lib/aegisops";
import { MetricPill, PageTitle, Panel, StatusBadge, formatDate, humanize } from "@/components/ui";
import { approveProposal, rejectProposal } from "./actions";

export const instant = false;

export default async function RemediationPage({ searchParams }: { searchParams: Promise<{ review?: string; error?: string }> }) {
  const params = await searchParams;
  const records = await getDashboardRemediations(100);
  const pending = records.filter((record) => record.status === "PENDING").length;
  const approved = records.filter((record) => record.status === "APPROVED").length;
  const executed = records.filter((record) => record.execution_status === "SUCCEEDED").length;
  const recovered = records.filter((record) => record.recovery_status === "RECOVERED").length;

  return (
    <div className="mx-auto max-w-[1700px]">
      <PageTitle eyebrow="Human-in-the-Loop" title="Remediation" actions={<><MetricPill label="Pending" value={pending} tone="amber" /><MetricPill label="Approved" value={approved} tone="blue" /><MetricPill label="Recovered" value={recovered} tone="green" /></>} />
      {params.review && <Notice tone="green">Proposal review submitted successfully.</Notice>}
      {params.error && <Notice tone="red">{params.error}</Notice>}

      <Panel className="overflow-hidden">
        <div className="flex items-center justify-between px-6 py-5"><div><p className="text-lg font-black">Remediation Queue</p><p className="mt-1 text-xs text-[#8b8e96]">{records.length} proposals · {executed} successful executions</p></div><div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#edf0ff]"><Wrench className="h-4.5 w-4.5 text-[#5364db]" /></div></div>
        <div className="space-y-4 px-4 pb-4">{records.map((record) => (
          <div key={record.id} className="rounded-[24px] bg-white/58 p-5">
            <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start"><div className="flex min-w-0 gap-3"><div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[#fff4d1]"><Wrench className="h-5 w-5 text-[#a56a08]" /></div><div className="min-w-0"><p className="truncate text-sm font-black">{record.incident_title}</p><p className="mt-1 text-[10px] font-bold text-[#979aa2]">Proposal #{record.id} · {humanize(record.action_key)} · {record.target_service}</p></div></div><StatusBadge text={record.status} tone={record.status === "APPROVED" ? "green" : record.status === "REJECTED" ? "red" : record.status === "PENDING" ? "amber" : "neutral"} /></div>
            <div className="mt-5 grid gap-4 lg:grid-cols-2"><TextBlock title="Rationale" text={record.rationale} /><TextBlock title="Expected Outcome" text={record.expected_outcome} /></div>
            <div className="mt-5 flex flex-wrap gap-2"><StatusBadge text={`Risk ${record.risk_level}`} tone="pink" />{record.execution_status && <StatusBadge text={`Execution ${record.execution_status}`} tone={record.execution_status === "SUCCEEDED" ? "green" : "red"} />}{record.recovery_status && <StatusBadge text={`Recovery ${record.recovery_status}`} tone={record.recovery_status === "RECOVERED" ? "green" : "amber"} />}</div>
            {record.status === "PENDING" && (
              <form className="mt-5 rounded-[22px] bg-[#f2efe9] p-4">
                <input type="hidden" name="proposal_id" value={record.id} />
                <label className="text-[10px] font-black uppercase tracking-[.12em] text-[#8d9098]">Operator review note</label>
                <textarea name="note" required minLength={5} placeholder="Explain the approval or rejection decision..." className="mt-2 min-h-[88px] w-full resize-y rounded-2xl border border-black/[.05] bg-white px-4 py-3 text-xs font-semibold text-[#333845] outline-none focus:border-[#6674ef]/40" />
                <div className="mt-3 flex justify-end gap-3"><button formAction={rejectProposal} className="inline-flex items-center gap-2 rounded-full bg-[#fff0ec] px-4 py-2.5 text-xs font-black text-[#d94d43]"><XCircle className="h-4 w-4" />Reject</button><button formAction={approveProposal} className="inline-flex items-center gap-2 rounded-full bg-[#111625] px-4 py-2.5 text-xs font-black text-white"><ShieldCheck className="h-4 w-4" />Approve</button></div>
              </form>
            )}
            <div className="mt-4 flex items-center justify-between gap-3 border-t border-black/[.05] pt-4"><p className="text-[10px] font-bold text-[#979aa2]">Created {formatDate(record.created_at)}</p><Link href={`/incidents/${record.incident_id}`} className="text-[10px] font-black text-[#5364db]">Open incident →</Link></div>
          </div>
        ))}</div>
        {!records.length && <div className="p-14 text-center"><CheckCircle2 className="mx-auto h-8 w-8 text-[#55a87f]" /><p className="mt-3 text-sm font-black">No remediation proposals</p></div>}
      </Panel>
    </div>
  );
}

function TextBlock({ title, text }: { title: string; text: string }) { return <div><p className="text-[9px] font-black uppercase tracking-[.12em] text-[#999ca3]">{title}</p><p className="mt-2 text-xs leading-5 text-[#626771]">{text}</p></div>; }
function Notice({ tone, children }: { tone: "red" | "green"; children: React.ReactNode }) { return <div className={`mb-5 rounded-2xl px-4 py-3 text-xs font-black ${tone === "green" ? "bg-[#eaf8f0] text-[#16875d]" : "bg-[#fff0ec] text-[#d94d43]"}`}>{children}</div>; }
