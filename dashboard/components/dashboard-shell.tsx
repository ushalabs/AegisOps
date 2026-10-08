"use client";

import { useMemo, useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  AlertTriangle,
  Bell,
  BookOpen,
  BrainCircuit,
  ChartNoAxesCombined,
  ChevronDown,
  FileSearch,
  FileText,
  LayoutDashboard,
  Search,
  Settings,
  ShieldCheck,
  Wrench,
} from "lucide-react";

type NavItem = {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
};

const navigation: NavItem[] = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Incidents", href: "/incidents", icon: AlertTriangle },
  { label: "Investigations", href: "/investigations", icon: FileSearch },
  { label: "Remediation", href: "/remediation", icon: Wrench },
  { label: "Postmortems", href: "/postmortems", icon: FileText },
  { label: "Runbooks", href: "/runbooks", icon: BookOpen },
  { label: "Knowledge Base", href: "/knowledge-base", icon: BrainCircuit },
  { label: "Monitoring", href: "/monitoring", icon: ChartNoAxesCombined },
  { label: "System Health", href: "/system-health", icon: ShieldCheck },
  { label: "Settings", href: "/settings", icon: Settings },
];

export default function DashboardShell({
  children,
}: {
  children: ReactNode;
}) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const activePath = useMemo(() => pathname ?? "/", [pathname]);

  return (
    <div
      className="relative min-h-screen overflow-hidden"
      style={{
                background: `
                radial-gradient(
                    circle at 10% 88%,
                    rgba(238, 132, 115, 0.34),
                    transparent 24%
                ),
                radial-gradient(
                    circle at 89% 82%,
                    rgba(91, 163, 218, 0.34),
                    transparent 28%
                ),
                radial-gradient(
                    circle at 52% 3%,
                    rgba(139, 111, 216, 0.26),
                    transparent 30%
                ),
                radial-gradient(
                    circle at 35% 55%,
                    rgba(202, 163, 211, 0.16),
                    transparent 32%
                ),
                linear-gradient(
                    145deg,
                    #d8d0d0 0%,
                    #ded9df 31%,
                    #d4d3df 62%,
                    #ced9e2 100%
                )
                `,
      }}
    >
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -bottom-24 -left-12 h-[360px] w-[520px] rounded-full bg-[#ffb39b]/25 blur-[90px]" />
        <div className="absolute bottom-[-80px] right-[-60px] h-[360px] w-[460px] rounded-full bg-[#a4d1f0]/25 blur-[100px]" />
        <div className="absolute left-[35%] top-[-120px] h-[300px] w-[420px] rounded-full bg-[#bcaeff]/18 blur-[95px]" />
      </div>

      {!sidebarOpen && (
        <div
          className="fixed inset-y-0 left-0 z-40 hidden w-5 lg:block"
          onMouseEnter={() => setSidebarOpen(true)}
        />
      )}

      <div className="relative z-10 flex min-h-screen">
        <aside
          onMouseEnter={() => setSidebarOpen(true)}
          onMouseLeave={() => setSidebarOpen(false)}
          className={[
            "hidden shrink-0 border-r border-white/35 transition-all duration-300 lg:flex lg:flex-col",
            sidebarOpen ? "w-[250px]" : "w-[88px]",
          ].join(" ")}
          style={{
            background: "rgba(255,255,255,0.22)",
            backdropFilter: "blur(26px)",
            WebkitBackdropFilter: "blur(26px)",
            boxShadow: "inset -1px 0 0 rgba(255,255,255,.22)",
          }}
        >
          <div className="flex h-[82px] items-center border-b border-white/30 px-5">
            <AegisLogoMark />

            <div
              className={[
                "ml-3 overflow-hidden transition-all duration-300",
                sidebarOpen
                  ? "max-w-[180px] opacity-100"
                  : "max-w-0 opacity-0",
              ].join(" ")}
            >
              <div className="text-[19px] font-bold tracking-tight">
                Aegis<span className="text-blue-600">Ops</span>
              </div>

              <div className="text-[11px] text-slate-500">
                Incident Operations Platform
              </div>
            </div>
          </div>

          <nav className="flex-1 space-y-1 px-3 py-5">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/"
                  ? activePath === "/"
                  : activePath.startsWith(item.href);

              return (
                <Link
                  key={item.label}
                  href={item.href}
                  className={[
                    "flex items-center rounded-2xl px-4 py-3 transition-all duration-200",
                    sidebarOpen ? "justify-start gap-3" : "justify-center",
                    isActive
                      ? "border border-slate-900/10 bg-white/45 text-blue-700 shadow-[0_10px_24px_rgba(15,23,42,0.05)]"
                      : "text-slate-700 hover:bg-white/28 hover:text-slate-950",
                  ].join(" ")}
                >
                  <Icon className="h-[18px] w-[18px] shrink-0" />

                  <span
                    className={[
                      "overflow-hidden whitespace-nowrap text-sm font-medium transition-all duration-200",
                      sidebarOpen
                        ? "max-w-[160px] opacity-100"
                        : "max-w-0 opacity-0",
                    ].join(" ")}
                  >
                    {item.label}
                  </span>
                </Link>
              );
            })}
          </nav>

          <div className="px-3 pb-4">
            <div
              className={[
                "rounded-2xl border border-white/35 bg-white/22 transition-all duration-300",
                sidebarOpen ? "px-4 py-4" : "px-3 py-4",
              ].join(" ")}
            >
              <div
                className={[
                  "flex items-center",
                  sidebarOpen ? "gap-2" : "justify-center",
                ].join(" ")}
              >
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                <span
                  className={[
                    "overflow-hidden whitespace-nowrap text-sm font-medium text-slate-700 transition-all duration-200",
                    sidebarOpen
                      ? "max-w-[120px] opacity-100"
                      : "max-w-0 opacity-0",
                  ].join(" ")}
                >
                  Online
                </span>
              </div>
            </div>
          </div>
        </aside>

        <div className="min-w-0 flex-1">
          <header
            className="flex h-[82px] items-center justify-between border-b border-white/30 px-6 xl:px-8"
            style={{
              background: "rgba(255,255,255,0.18)",
              backdropFilter: "blur(24px)",
              WebkitBackdropFilter: "blur(24px)",
            }}
          >
            <div className="flex w-full max-w-xl items-center gap-3 rounded-[20px] border border-white/50 bg-white/22 px-4 py-3 shadow-[0_8px_30px_rgba(15,23,42,0.04)]">
              <Search className="h-4 w-4 text-slate-400" />
              <input
                className="w-full bg-transparent text-sm outline-none placeholder:text-slate-400"
                placeholder="Search incidents, postmortems and runbooks..."
              />
            </div>

            <div className="ml-6 flex items-center gap-5">
              <button
                type="button"
                className="text-slate-500 transition hover:text-slate-900"
              >
                <Bell className="h-5 w-5" />
              </button>

              <div className="h-8 w-px bg-slate-300/50" />

              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/55 text-sm font-semibold text-blue-700 shadow-sm">
                  OP
                </div>

                <div className="hidden sm:block">
                  <p className="text-sm font-semibold">Operator</p>
                  <p className="text-xs text-slate-500">Administrator</p>
                </div>

                <ChevronDown className="h-4 w-4 text-slate-400" />
              </div>
            </div>
          </header>

          <main className="p-6 xl:p-8">{children}</main>
        </div>
      </div>
    </div>
  );
}

function AegisLogoMark() {
  return (
    <div
      className="flex h-11 w-11 shrink-0 items-center justify-center rounded-[14px] bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-700 shadow-[0_8px_22px_rgba(37,99,235,0.24)] ring-1 ring-blue-400/30"
      aria-label="AegisOps"
    >
      <svg
        viewBox="0 0 40 40"
        className="h-8 w-8"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M20 4.5 31 8.6v8.8c0 7.9-4.6 14.2-11 17.1-6.4-2.9-11-9.2-11-17.1V8.6L20 4.5Z"
          fill="rgba(255,255,255,0.14)"
          stroke="white"
          strokeWidth="2.2"
          strokeLinejoin="round"
        />
        <path
          d="M12.8 20h4.1l2.1-5.2 3.2 10.1 2.1-4.9h3"
          stroke="white"
          strokeWidth="2.25"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}