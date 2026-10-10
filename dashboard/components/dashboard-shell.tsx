"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import type { ReactNode } from "react";
import {
  AlertTriangle,
  Bell,
  ChevronDown,
  FileSearch,
  FileText,
  LayoutDashboard,
  Wrench,
} from "lucide-react";
import { BrandOrbit3D, ShieldMark } from "@/components/brand-mark";

const navigation = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Incidents", href: "/incidents", icon: AlertTriangle },
  { label: "Investigations", href: "/investigations", icon: FileSearch },
  { label: "Remediation", href: "/remediation", icon: Wrench },
  { label: "Postmortems", href: "/postmortems", icon: FileText },
];

export default function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname() ?? "/";

  return (
    <div className="aegis-frame">
      <aside className="fixed inset-y-0 left-0 z-50 hidden w-[96px] flex-col items-center bg-[#0f1424] py-6 lg:flex">
        <ShieldMark compact />

        <nav className="mt-12 flex w-full flex-col items-center gap-3 px-3">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                title={item.label}
                className={[
                  "group relative flex h-12 w-12 items-center justify-center rounded-2xl transition-all duration-200",
                  active
                    ? "bg-[#b7b8b4] text-white"
                    : "text-[#e5e6ea] hover:bg-white/10 hover:text-white",
                ].join(" ")}
              >
                <Icon className="h-[20px] w-[20px]" />

                {active && (
                  <span className="absolute -right-[13px] h-2 w-2 rounded-full bg-white" />
                )}

                <span className="pointer-events-none absolute left-[62px] z-50 whitespace-nowrap rounded-lg bg-[#151a2c] px-3 py-2 text-xs text-white opacity-0 shadow-xl transition group-hover:opacity-100">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </nav>

        <div className="pointer-events-none absolute bottom-[126px] left-0 z-20 h-[126px] w-[126px]">
          <BrandOrbit3D />
        </div>
      </aside>

      <div className="min-h-screen min-w-0 bg-[#f3f0eb] lg:pl-[96px]">
        <header className="flex min-h-[96px] items-center justify-between gap-5 px-6 py-5 xl:px-9">
          <div className="flex min-w-0 items-center gap-5">
            <h1 className="text-[38px] leading-none tracking-[-0.045em] text-[#111625] sm:text-[42px]">
              Aegis
              <span className="bg-gradient-to-r from-[#ff765f] via-[#f45c72] to-[#ef4e91] bg-clip-text text-transparent">
                Ops
              </span>
            </h1>

            <div className="hidden items-center gap-2 rounded-full bg-white/80 px-4 py-2.5 text-[13px] text-[#333845] shadow-[0_8px_24px_rgba(28,34,55,.04)] md:flex">
              <span className="h-2 w-2 rounded-full bg-[#55cfa0]" />
              Benchmark Stack
              <ChevronDown className="h-3.5 w-3.5 text-[#9a9ca3]" />
            </div>
          </div>

          <div className="flex items-center gap-4 sm:gap-5">
            <button
              className="relative flex h-10 w-10 items-center justify-center rounded-full bg-[#0f1424] text-white shadow-[0_8px_20px_rgba(15,20,36,.16)] transition hover:bg-black"
              aria-label="Notifications"
            >
              <Bell className="h-5 w-5" />
              <span className="absolute -right-1 -top-1 h-5 min-w-5 rounded-full bg-[#ef4f5a] px-1 text-[9px] leading-5 text-white shadow-sm">
                1
              </span>
            </button>

            <div className="hidden h-8 w-px bg-black/10 sm:block" />

            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#0f1424] text-xs text-white shadow-[0_8px_20px_rgba(15,20,36,.16)]">
                OP
              </div>

              <div className="hidden sm:block">
                <p className="text-sm text-[#111625]">Operator</p>
                <p className="text-[11px] text-[#8b8f98]">Administrator</p>
              </div>
            </div>
          </div>
        </header>

        <div>{children}</div>
      </div>
    </div>
  );
}
