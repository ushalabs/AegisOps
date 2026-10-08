import {
  AlertTriangle,
  BookOpen,
  BrainCircuit,
  ChartNoAxesCombined,
  FileSearch,
  FileText,
  Settings,
  ShieldCheck,
  Wrench,
} from "lucide-react";

import {
  notFound,
} from "next/navigation";


const sections = {
  investigations: {
    title:
      "Investigations",

    description:
      "Agent investigations, evidence and analysis.",

    icon:
      FileSearch,
  },

  remediation: {
    title:
      "Remediation",

    description:
      "Remediation proposals, human approvals and execution.",

    icon:
      Wrench,
  },

  postmortems: {
    title:
      "Postmortems",

    description:
      "Generated postmortems and historical incident memory.",

    icon:
      FileText,
  },

  runbooks: {
    title:
      "Runbooks",

    description:
      "Operational runbooks used by AegisOps investigations.",

    icon:
      BookOpen,
  },

  "knowledge-base": {
    title:
      "Knowledge Base",

    description:
      "Runbook knowledge and historical incident context.",

    icon:
      BrainCircuit,
  },

  monitoring: {
    title:
      "Monitoring",

    description:
      "Metrics, telemetry and observability integrations.",

    icon:
      ChartNoAxesCombined,
  },

  "system-health": {
    title:
      "System Health",

    description:
      "Health of AegisOps and monitored infrastructure.",

    icon:
      ShieldCheck,
  },

  settings: {
    title:
      "Settings",

    description:
      "Dashboard and operator configuration.",

    icon:
      Settings,
  },
} as const;


export default async function SectionPage({
  params,
}: {
  params: Promise<{
    section: string;
  }>;
}) {
  const {
    section,
  } = await params;


  const config =
    sections[
      section as keyof typeof sections
    ];


  if (!config) {
    notFound();
  }


  const Icon =
    config.icon;


  return (
    <main
      className="
        min-h-[calc(100vh-70px)]
        p-6 xl:p-8
      "
    >

      <section
        className="
          rounded-2xl
          border
          border-slate-200
          bg-white
          p-8
          shadow-sm
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
              h-12 w-12
              items-center
              justify-center
              rounded-xl
              bg-blue-50
            "
          >

            <Icon
              className="
                h-6 w-6
                text-blue-600
              "
            />

          </div>


          <div>

            <h1
              className="
                text-3xl
                font-bold
                tracking-tight
              "
            >
              {config.title}
            </h1>

            <p
              className="
                mt-1
                text-sm
                text-slate-500
              "
            >
              {config.description}
            </p>

          </div>

        </div>


        <div
          className="
            mt-8
            rounded-xl
            border
            border-dashed
            border-slate-300
            bg-slate-50
            px-6 py-14
            text-center
          "
        >

          <p
            className="
              font-medium
              text-slate-700
            "
          >
            This page is routed and ready.
          </p>

          <p
            className="
              mt-2
              text-sm
              text-slate-500
            "
          >
            We will connect this section to its real AegisOps data during Phase 15.
          </p>

        </div>

      </section>

    </main>
  );
}