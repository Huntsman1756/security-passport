import type { FieldStatus } from "../types";

const META: Record<
  FieldStatus,
  { label: string; glyph: string; cls: string }
> = {
  reported: {
    label: "reported",
    glyph: "●",
    cls: "text-emerald-700 dark:text-emerald-400 border-emerald-600/40",
  },
  derived: {
    label: "derived",
    glyph: "◆",
    cls: "text-sky-700 dark:text-sky-400 border-sky-600/40",
  },
  inferred: {
    label: "inferred",
    glyph: "◈",
    cls: "text-violet-700 dark:text-violet-400 border-violet-500/40",
  },
  conflict: {
    label: "conflict",
    glyph: "▲",
    cls: "text-amber-700 dark:text-amber-400 border-amber-500/50",
  },
  not_found: {
    label: "not found",
    glyph: "○",
    cls: "text-slate-500 dark:text-slate-400 border-slate-400/40",
  },
  not_applicable: {
    label: "n/a",
    glyph: "–",
    cls: "text-slate-400 dark:text-slate-500 border-slate-400/30",
  },
};

export function StatusBadge({ status }: { status: FieldStatus }) {
  const m = META[status];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide ${m.cls}`}
    >
      <span aria-hidden>{m.glyph}</span>
      {m.label}
    </span>
  );
}

export function statusGlyph(status: FieldStatus): string {
  return META[status].glyph;
}
