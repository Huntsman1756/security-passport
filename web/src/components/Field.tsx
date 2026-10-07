import type { PassportField } from "../types";
import { StatusBadge } from "./StatusBadge";

function fmtValue(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  if (Array.isArray(v)) return v.join(", ");
  if (typeof v === "object") {
    const o = v as Record<string, unknown>;
    if (typeof o.name === "string" && o.name) return o.name;
    if (typeof o.code === "string" && o.code) return o.code;
    return JSON.stringify(v);
  }
  return String(v);
}

export function Field({
  label,
  name,
  field,
  onOpen,
}: {
  label: string;
  name: string;
  field: PassportField | undefined;
  onOpen: (name: string, field: PassportField) => void;
}) {
  if (!field) return null;
  const value = fmtValue(field.value);
  const muted =
    field.status === "not_found" || field.status === "not_applicable";
  return (
    <button
      type="button"
      onClick={() => onOpen(name, field)}
      className="group grid w-full grid-cols-[11rem_1fr_auto] items-baseline gap-3 rounded px-2 py-1.5 text-left hover:bg-[var(--surface-2)] focus-visible:bg-[var(--surface-2)] sm:grid-cols-[13rem_1fr_auto]"
      aria-label={`${label}: ${value} — ${field.status}. Open provenance.`}
    >
      <span className="text-[13px] text-[var(--ink-2)]">{label}</span>
      <span
        className={`mono truncate text-[13px] ${
          muted ? "text-[var(--ink-2)]" : ""
        }`}
      >
        {value}
      </span>
      <span className="flex items-center gap-1.5">
        {field.quality_flags.slice(0, 1).map((f) => (
          <span
            key={f}
            className="hidden rounded border border-amber-500/40 px-1 py-0.5 text-[9px] uppercase text-amber-600 dark:text-amber-400 sm:inline"
            title={f}
          >
            flag
          </span>
        ))}
        <StatusBadge status={field.status} />
      </span>
    </button>
  );
}
