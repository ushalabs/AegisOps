"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { reviewRemediationProposal } from "@/lib/aegisops";

async function submitReview(decision: "APPROVED" | "REJECTED", formData: FormData) {
  const proposalId = Number(formData.get("proposal_id"));
  const note = String(formData.get("note") ?? "").trim();
  if (!Number.isInteger(proposalId) || proposalId < 1) redirect("/remediation?error=Invalid%20proposal");
  if (note.length < 5) redirect("/remediation?error=Review%20note%20must%20be%20at%20least%205%20characters");

  try {
    await reviewRemediationProposal(proposalId, decision, note);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Review failed.";
    redirect(`/remediation?error=${encodeURIComponent(message)}`);
  }

  revalidatePath("/remediation");
  redirect(`/remediation?review=${decision.toLowerCase()}`);
}

export async function approveProposal(formData: FormData) { await submitReview("APPROVED", formData); }
export async function rejectProposal(formData: FormData) { await submitReview("REJECTED", formData); }
