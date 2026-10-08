import type { FieldStatus } from "../types";

export const STATUS_ORDER: FieldStatus[] = [
  "reported",
  "derived",
  "inferred",
  "conflict",
  "not_found",
  "not_applicable",
];

export const STATUS_META: Record<
  FieldStatus,
  { label: string; glyph: string; cls: string; bar: string; meaning: string }
> = {
  reported: {
    label: "reported",
    glyph: "●",
    cls: "text-emerald-700 dark:text-emerald-400 border-emerald-600/40",
    bar: "bg-emerald-500",
    meaning: "Stated directly by an authoritative source; evidence attached.",
  },
  derived: {
    label: "derived",
    glyph: "◆",
    cls: "text-sky-700 dark:text-sky-400 border-sky-600/40",
    bar: "bg-sky-500",
    meaning: "Computed by a versioned, deterministic rule from reported inputs.",
  },
  inferred: {
    label: "inferred",
    glyph: "◈",
    cls: "text-violet-700 dark:text-violet-400 border-violet-500/40",
    bar: "bg-violet-500",
    meaning: "An evidence-bounded assessment, shipped with its limitations.",
  },
  conflict: {
    label: "conflict",
    glyph: "▲",
    cls: "text-amber-700 dark:text-amber-400 border-amber-500/50",
    bar: "bg-amber-500",
    meaning: "Sources disagree. Every assertion is kept; none is silently chosen.",
  },
  not_found: {
    label: "not found",
    glyph: "○",
    cls: "text-slate-500 dark:text-slate-400 border-slate-400/40",
    bar: "bg-slate-400/70",
    meaning: "Searched and absent. Never rendered as false; the searched sources are listed.",
  },
  not_applicable: {
    label: "n/a",
    glyph: "–",
    cls: "text-slate-400 dark:text-slate-500 border-slate-400/30",
    bar: "bg-slate-300 dark:bg-slate-600",
    meaning: "The question does not apply to this instrument type.",
  },
};
