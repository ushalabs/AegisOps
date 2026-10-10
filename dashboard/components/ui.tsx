import type { ComponentType, ReactNode } from "react";

export function Panel({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <section className={`aegis-card rounded-[28px] ${className}`}>{children}</section>;
}

export function SoftBox({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`aegis-soft rounded-[20px] ${className}`}>{children}</div>;
}

export function PageTitle({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-7 flex flex-col justify-between gap-4 md:flex-row md:items-end">
      <div>
        {eyebrow && (
          <p className="text-[11px] uppercase tracking-[.18em] text-[#9a9ca3]">{eyebrow}</p>
        )}
        <h2 className="mt-1 text-[40px] leading-none tracking-[-.04em] text-[#111625]">{title}</h2>
        {description && (
          <p className="mt-1 max-w-2xl text-[15px] text-[#737783]">{description}</p>
        )}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-3">{actions}</div>}
    </div>
  );
}

export function MetricPill({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: number | string;
  tone?: "neutral" | "red" | "green" | "amber" | "blue";
}) {
  const tones = {
    neutral: "bg-white text-[#111625]",
    red: "bg-[#fff0ec] text-[#e65245]",
    green: "bg-[#eaf8f0] text-[#16875d]",
    amber: "bg-[#fff6da] text-[#a56a08]",
    blue: "bg-[#eef1ff] text-[#5364db]",
  };

  return (
    <div
      className={`min-w-[88px] rounded-[18px] px-4 py-3 shadow-[0_8px_22px_rgba(28,34,55,.035)] ${tones[tone]}`}
    >
      <p className="text-[11px] uppercase tracking-wide opacity-70">{label}</p>
      <p className="mt-1 text-[22px] tracking-[-.03em]">{value}</p>
    </div>
  );
}

export function StatusBadge({
  text,
  tone = "neutral",
}: {
  text: string;
  tone?: "neutral" | "red" | "green" | "amber" | "blue" | "pink";
}) {
  const styles = {
    neutral: "bg-[#eeece7] text-[#666b75]",
    red: "bg-[#fff0ec] text-[#d94d43]",
    green: "bg-[#e9f8f0] text-[#16875d]",
    amber: "bg-[#fff4d1] text-[#a96c06]",
    blue: "bg-[#edf0ff] text-[#5364db]",
    pink: "bg-[#fdebf5] text-[#c73f82]",
  };

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-[10px] uppercase tracking-[.05em] ${styles[tone]}`}
    >
      {text}
    </span>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  description,
}: {
  icon: ComponentType<{ className?: string }>;
  title: string;
  description?: string;
}) {
  return (
    <div className="flex min-h-[240px] items-center justify-center px-6 text-center">
      <div>
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#eeece7]">
          <Icon className="h-6 w-6 text-[#858993]" />
        </div>
        <p className="mt-4 text-[16px] text-[#242936]">{title}</p>
        <p className="mt-1 text-[13px] text-[#858993]">{description}</p>
      </div>
    </div>
  );
}

export function humanize(value: string) {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function formatDate(value: string | null | undefined) {
  if (!value) return "—";

  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
