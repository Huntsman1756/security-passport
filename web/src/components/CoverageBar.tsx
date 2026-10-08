import type { Passport } from "../types";
import { STATUS_ORDER, STATUS_META } from "../lib/statusMeta";
import { countStatuses } from "../lib/coverage";

/** Status distribution across every field — the passport's evidence
 * profile at a glance. Segments carry text labels, not color only. */
export function CoverageBar({ passport }: { passport: Passport }) {
  const counts = countStatuses(passport);
  const total = STATUS_ORDER.reduce((n, s) => n + counts[s], 0) || 1;
  return (
    <div>
      <div
        className="flex h-2 overflow-hidden rounded-full bg-[var(--surface-2)]"
        role="img"
        aria-label={STATUS_ORDER.map((s) => `${counts[s]} ${STATUS_META[s].label}`).join(", ")}
      >
        {STATUS_ORDER.filter((s) => counts[s]).map((s) => (
          <div
            key={s}
            className={STATUS_META[s].bar}
            style={{ width: `${(counts[s] / total) * 100}%` }}
          />
        ))}
      </div>
      <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11.5px] text-[var(--ink-2)]">
        {STATUS_ORDER.filter((s) => counts[s]).map((s) => (
          <li key={s} className="flex items-center gap-1.5">
            <span className={`inline-block h-2 w-2 rounded-full ${STATUS_META[s].bar}`} aria-hidden />
            <span className="mono text-[var(--ink)]">{counts[s]}</span> {STATUS_META[s].label}
          </li>
        ))}
      </ul>
    </div>
  );
}
