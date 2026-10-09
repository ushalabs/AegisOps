import Link from "next/link";

import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  ShieldCheck,
  Wrench,
  XCircle,
} from "lucide-react";

import {
  getDashboardRemediations,
} from "@/lib/aegisops";

import {
  approveProposal,
  rejectProposal,
} from "./actions";


export const instant = false;


export default async function RemediationPage({
  searchParams,
}: {
  searchParams: Promise<{
    review?: string;
    error?: string;
  }>;
}) {
  const params =
    await searchParams;


  const records =
    await getDashboardRemediations(
      100
    );


  const pending =
    records.filter(
      (record) =>
        record.status ===
        "PENDING"
    );


  return (
    <main className="p-6 xl:p-8">

      <div className="mx-auto max-w-[1700px]">

        <div className="mb-6">

          <h1
            className="
              text-3xl
              font-bold
              tracking-tight
            "
          >
            Remediation
          </h1>

          <p
            className="
              mt-1
              text-sm
              text-slate-600
            "
          >
            Human approval, execution and recovery state.
          </p>

        </div>


        {params.review && (
          <Message
            tone="green"
            text="Proposal review submitted successfully."
          />
        )}


        {params.error && (
          <Message
            tone="red"
            text={params.error}
          />
        )}


        <section
          className="
            mb-5
            grid
            gap-3
            md:grid-cols-4
          "
        >

          <Stat
            label="Pending"
            value={
              pending.length
            }
          />

          <Stat
            label="Approved"
            value={
              records.filter(
                (r) =>
                  r.status ===
                  "APPROVED"
              ).length
            }
          />

          <Stat
            label="Executed"
            value={
              records.filter(
                (r) =>
                  r.execution_status ===
                  "SUCCEEDED"
              ).length
            }
          />

          <Stat
            label="Recovered"
            value={
              records.filter(
                (r) =>
                  r.recovery_status ===
                  "RECOVERED"
              ).length
            }
          />

        </section>


        <GlassPanel>

          <div
            className="
              border-b
              border-white/30
              px-6
              py-5
            "
          >
            <h2 className="font-semibold">
              Remediation Queue
            </h2>

            <p
              className="
                mt-1
                text-xs
                text-slate-500
              "
            >
              {records.length} proposals
            </p>
          </div>


          <div className="space-y-4 p-4">

            {records.map(
              (record) => (

                <div
                  key={record.id}
                  className="
                    rounded-[24px]
                    border
                    border-white/30
                    bg-white/14
                    p-5
                  "
                >

                  <div
                    className="
                      flex
                      flex-col
                      justify-between
                      gap-4
                      lg:flex-row
                      lg:items-start
                    "
                  >

                    <div>

                      <div
                        className="
                          flex
                          items-center
                          gap-3
                        "
                      >

                        <div
                          className="
                            flex
                            h-11
                            w-11
                            items-center
                            justify-center
                            rounded-2xl
                            bg-indigo-100/60
                          "
                        >
                          <Wrench
                            className="
                              h-5
                              w-5
                              text-indigo-600
                            "
                          />
                        </div>


                        <div>
                          <p className="font-semibold">
                            {
                              record.incident_title
                            }
                          </p>

                          <p
                            className="
                              mt-1
                              text-xs
                              text-slate-500
                            "
                          >
                            Proposal #{record.id}
                            {" · "}
                            {
                              humanize(
                                record.action_key
                              )
                            }
                          </p>
                        </div>

                      </div>

                    </div>


                    <StatusBadge
                      status={
                        record.status
                      }
                    />

                  </div>


                  <div
                    className="
                      mt-5
                      grid
                      gap-4
                      lg:grid-cols-2
                    "
                  >

                    <TextBlock
                      title="Rationale"
                      text={
                        record.rationale
                      }
                    />

                    <TextBlock
                      title="Expected Outcome"
                      text={
                        record.expected_outcome
                      }
                    />

                  </div>


                  <div
                    className="
                      mt-5
                      flex
                      flex-wrap
                      gap-2
                    "
                  >

                    <SmallBadge
                      text={
                        `Risk: ${record.risk_level}`
                      }
                    />

                    {record.execution_status && (
                      <SmallBadge
                        text={
                          `Execution: ${record.execution_status}`
                        }
                      />
                    )}

                    {record.recovery_status && (
                      <SmallBadge
                        text={
                          `Recovery: ${record.recovery_status}`
                        }
                      />
                    )}

                  </div>


                  {record.status ===
                    "PENDING" && (

                    <form
                      className="
                        mt-5
                        rounded-2xl
                        border
                        border-white/30
                        bg-white/12
                        p-4
                      "
                    >

                      <input
                        type="hidden"
                        name="proposal_id"
                        value={
                          record.id
                        }
                      />


                      <label
                        className="
                          text-xs
                          font-semibold
                          text-slate-600
                        "
                      >
                        Operator review note
                      </label>


                      <textarea
                        name="note"
                        required
                        minLength={5}
                        placeholder="Explain why this remediation is approved or rejected..."
                        className="
                          mt-2
                          min-h-[90px]
                          w-full
                          resize-y
                          rounded-2xl
                          border
                          border-white/35
                          bg-white/25
                          px-4
                          py-3
                          text-sm
                          outline-none
                          backdrop-blur-xl
                          focus:border-indigo-300
                        "
                      />


                      <div
                        className="
                          mt-3
                          flex
                          justify-end
                          gap-3
                        "
                      >

                        <button
                          formAction={
                            rejectProposal
                          }
                          className="
                            inline-flex
                            items-center
                            gap-2
                            rounded-xl
                            bg-red-100/70
                            px-4
                            py-2.5
                            text-sm
                            font-semibold
                            text-red-700
                          "
                        >
                          <XCircle className="h-4 w-4" />
                          Reject
                        </button>


                        <button
                          formAction={
                            approveProposal
                          }
                          className="
                            inline-flex
                            items-center
                            gap-2
                            rounded-xl
                            bg-emerald-100/75
                            px-4
                            py-2.5
                            text-sm
                            font-semibold
                            text-emerald-700
                          "
                        >
                          <ShieldCheck className="h-4 w-4" />
                          Approve
                        </button>

                      </div>

                    </form>

                  )}


                  <div className="mt-4">

                    <Link
                      href={
                        `/incidents/${record.incident_id}`
                      }
                      className="
                        text-xs
                        font-semibold
                        text-indigo-700
                      "
                    >
                      Open incident →
                    </Link>

                  </div>

                </div>

              )
            )}

          </div>

        </GlassPanel>

      </div>

    </main>
  );
}


function GlassPanel({
  children,
}: {
  children:
    React.ReactNode;
}) {
  return (
    <section
      className="
        overflow-hidden
        rounded-[28px]
        border
        border-white/35
      "
      style={{
        background:
          "rgba(255,255,255,.28)",

        backdropFilter:
          "blur(22px)",
      }}
    >
      {children}
    </section>
  );
}


function Stat({
  label,
  value,
}: {
  label:
    string;

  value:
    number;
}) {
  return (
    <div
      className="
        rounded-2xl
        border
        border-white/35
        bg-white/20
        p-4
        backdrop-blur-xl
      "
    >
      <p className="text-xs text-slate-500">
        {label}
      </p>

      <p
        className="
          mt-1
          text-2xl
          font-bold
        "
      >
        {value}
      </p>
    </div>
  );
}


function StatusBadge({
  status,
}: {
  status:
    string;
}) {
  const style =
    status === "APPROVED"
      ? "bg-emerald-100/65 text-emerald-700"

      : status === "REJECTED"
        ? "bg-red-100/65 text-red-700"

        : status === "PENDING"
          ? "bg-amber-100/65 text-amber-700"

          : "bg-slate-100/60 text-slate-700";


  return (
    <span
      className={`
        rounded-full
        px-3
        py-1
        text-xs
        font-semibold
        ${style}
      `}
    >
      {status}
    </span>
  );
}


function SmallBadge({
  text,
}: {
  text:
    string;
}) {
  return (
    <span
      className="
        rounded-full
        border
        border-white/30
        bg-white/20
        px-3
        py-1
        text-[10px]
        font-semibold
        text-slate-600
      "
    >
      {text}
    </span>
  );
}


function TextBlock({
  title,
  text,
}: {
  title:
    string;

  text:
    string;
}) {
  return (
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
        {title}
      </p>

      <p
        className="
          mt-2
          text-sm
          leading-6
          text-slate-700
        "
      >
        {text}
      </p>
    </div>
  );
}


function Message({
  tone,
  text,
}: {
  tone:
    "red"
    | "green";

  text:
    string;
}) {
  return (
    <div
      className={`
        mb-5
        rounded-2xl
        border
        px-4
        py-3
        text-sm
        font-medium
        ${
          tone === "green"
            ? "border-emerald-200/50 bg-emerald-100/45 text-emerald-700"
            : "border-red-200/50 bg-red-100/45 text-red-700"
        }
      `}
    >
      {text}
    </div>
  );
}


function humanize(
  value:
    string
) {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(
      /\b\w/g,
      (c) =>
        c.toUpperCase()
    );
}