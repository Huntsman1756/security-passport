import type { FieldStatus } from "../types";
import { STATUS_META } from "../lib/statusMeta";

export function StatusBadge({ status }: { status: FieldStatus }) {
  const m = STATUS_META[status];
  return (
    <span
      title={m.meaning}
      className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide ${m.cls}`}
    >
      <span aria-hidden>{m.glyph}</span>
      {m.label}
    </span>
  );
}

