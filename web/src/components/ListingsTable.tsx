import { useState } from "react";
import type { Listing } from "../types";

const PREVIEW = 8;

const STATE_CLS: Record<string, string> = {
  active:
    "text-emerald-700 dark:text-emerald-400 border-emerald-600/40",
  terminated:
    "text-rose-700 dark:text-rose-400 border-rose-500/40",
  pending: "text-sky-700 dark:text-sky-400 border-sky-500/40",
  unknown_dates:
    "text-slate-500 dark:text-slate-400 border-slate-400/40",
};

export function ListingsTable({ listings }: { listings: Listing[] }) {
  const [all, setAll] = useState(false);
  if (!listings.length)
    return (
      <p className="px-2 py-2 text-[13px] text-[var(--ink-2)]">
        No venue records found.
      </p>
    );
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-[12.5px] [&_td]:whitespace-nowrap">
        <thead>
          <tr className="text-[10.5px] uppercase tracking-wider text-[var(--ink-2)]">
            <th className="px-2 py-1.5 font-medium">MIC</th>
            <th className="px-2 py-1.5 font-medium">Venue</th>
            <th className="px-2 py-1.5 font-medium">Relevant</th>
            <th className="px-2 py-1.5 font-medium">Admission</th>
            <th className="px-2 py-1.5 font-medium">First trade</th>
            <th className="px-2 py-1.5 font-medium">Termination</th>
            <th className="px-2 py-1.5 font-medium">State</th>
          </tr>
        </thead>
        <tbody>
          {(all ? listings : listings.slice(0, PREVIEW)).map((l) => (
            <tr
              key={l.venue_mic}
              className="border-t border-[var(--line)] hover:bg-[var(--surface-2)]"
            >
              <td className="mono px-2 py-1.5 font-medium">
                {l.venue_mic}
                {l.oprt_sgmt === "SGMT" ? (
                  <span
                    className="ml-1 text-[9px] text-[var(--ink-2)]"
                    title="segment MIC"
                  >
                    seg
                  </span>
                ) : null}
              </td>
              <td className="px-2 py-1.5 text-[var(--ink-2)]">
                {l.venue_name || "—"}
              </td>
              <td className="mono px-2 py-1.5 text-[var(--ink-2)]">
                {l.relevant_venue || "—"}
              </td>
              <td className="mono px-2 py-1.5">
                {l.admission_approval_date ?? "—"}
                {typeof l.admission_approval_date_raw === "string" &&
                String(l.admission_approval_date_raw).startsWith("9999") ? (
                  <span
                    className="ml-1 text-[9px] uppercase text-amber-600 dark:text-amber-400"
                    title={`source default: ${l.admission_approval_date_raw}`}
                  >
                    default
                  </span>
                ) : null}
              </td>
              <td className="mono px-2 py-1.5">
                {l.first_trade_date ?? "—"}
              </td>
              <td className="mono px-2 py-1.5 text-[var(--ink-2)]">
                {l.termination_date ?? "—"}
              </td>
              <td className="px-2 py-1.5">
                <span
                  className={`inline-block rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide ${
                    STATE_CLS[l.state] ?? STATE_CLS.unknown_dates
                  }`}
                >
                  {l.state.replace("_", " ")}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {listings.length > PREVIEW ? (
        <button
          onClick={() => setAll(!all)}
          className="mt-1 px-2 py-1.5 text-[12px] text-[var(--accent)] hover:underline"
        >
          {all ? "Show fewer venues" : `Show all ${listings.length} venues`}
        </button>
      ) : null}
    </div>
  );
}
