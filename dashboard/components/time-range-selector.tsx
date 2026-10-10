"use client";

import { Check, ChevronDown, Clock3 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

export type TimeRange = "1h" | "6h" | "24h" | "7d";
const options: Array<{ value: TimeRange; label: string }> = [
  { value: "1h", label: "Last hour" },
  { value: "6h", label: "Last 6 hours" },
  { value: "24h", label: "Last 24 hours" },
  { value: "7d", label: "Last 7 days" },
];

export default function TimeRangeSelector({ value }: { value: TimeRange }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const selected = options.find((option) => option.value === value) ?? options[2];

  function selectRange(range: TimeRange) {
    setOpen(false);
    router.push(range === "24h" ? "/" : `/?range=${range}`);
  }

  return (
    <div className="relative">
      <button type="button" onClick={() => setOpen((current) => !current)} className="flex items-center gap-2 rounded-full bg-white/80 px-4 py-2.5 text-xs font-bold text-[#242936] shadow-[0_8px_22px_rgba(28,34,55,.04)] transition hover:bg-white">
        <Clock3 className="h-3.5 w-3.5" /> {selected.label} <ChevronDown className={["h-3.5 w-3.5 transition", open ? "rotate-180" : ""].join(" ")} />
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-44 overflow-hidden rounded-2xl bg-white p-1.5 shadow-[0_18px_45px_rgba(20,25,45,.16)]">
          {options.map((option) => (
            <button key={option.value} type="button" onClick={() => selectRange(option.value)} className="flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-xs font-semibold text-[#3e4350] hover:bg-[#f3f0eb]">
              {option.label}{option.value === value && <Check className="h-3.5 w-3.5 text-[#6674ef]" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
