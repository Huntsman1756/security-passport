import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useServiceStatus } from "../lib/status";

const CFI_CATEGORY: Record<string, string> = {
  E: "Equity",
  C: "Collective investment",
  D: "Debt",
  R: "Entitlement",
  O: "Listed option",
  F: "Future",
  S: "Swap",
  H: "Non-listed option",
  I: "Spot",
  J: "Forward",
  K: "Strategy",
  L: "Financing",
  T: "Referential",
  M: "Other",
};

export function Corpus() {
  const st = useServiceStatus();
  const [filter, setFilter] = useState("");
  const corpus = useMemo(() => st.data?.demo?.corpus ?? [], [st.data]);
  const rows = useMemo(() => {
    const f = filter.trim().toUpperCase();
    return corpus.filter(
      (c) => !f || c.isin.includes(f) || (c.name ?? "").toUpperCase().includes(f),
    );
  }, [corpus, filter]);

  if (st.isLoading)
    return <div className="mx-auto max-w-5xl px-4 py-16 text-[var(--ink-2)]">Loading…</div>;

  if (!st.data?.demo)
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="text-2xl font-semibold">Coverage</h1>
        <p className="mt-3 text-[14px] text-[var(--ink-2)]">
          This instance runs against the live OpenInstrument security master
          (generation {st.data?.openinstrument_generation ?? "unknown"}), so any
          EU-reported ISIN can be queried.
        </p>
      </div>
    );

  return (
    <div className="mx-auto max-w-5xl px-4 py-12">
      <h1 className="text-2xl font-semibold tracking-tight">Demo corpus</h1>
      <p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-[var(--ink-2)]">
        This instance replays {corpus.length} instruments captured
        {st.data.demo.captured_at ? ` on ${st.data.demo.captured_at}` : ""} from
        the live sources. The raw payloads go through the same parsers and rules
        as production, so these passports are what the full system produces. An
        ISIN outside this list returns an honest <em>unknown</em>.
      </p>
      <input
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter by ISIN or name"
        aria-label="Filter corpus"
        className="mt-6 h-9 w-full max-w-sm rounded-md border border-[var(--line)] bg-[var(--surface-2)] px-3 text-[13px] outline-none focus:border-[var(--accent)]"
      />
      <div className="mt-4 overflow-x-auto rounded-lg border border-[var(--line)]">
        <table className="w-full text-left text-[13px]">
          <thead className="bg-[var(--surface-2)] text-[10.5px] uppercase tracking-wider text-[var(--ink-2)]">
            <tr>
              <th className="px-3 py-2 font-medium">ISIN</th>
              <th className="px-3 py-2 font-medium">Name (FISN)</th>
              <th className="px-3 py-2 font-medium">Category</th>
              <th className="px-3 py-2 font-medium">CFI</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.isin} className="border-t border-[var(--line)] hover:bg-[var(--surface-2)]">
                <td className="mono px-3 py-2">
                  <Link to={`/isin/${c.isin}`} className="font-medium text-[var(--accent)] hover:underline">
                    {c.isin}
                  </Link>
                </td>
                <td className="px-3 py-2">{c.name ?? "—"}</td>
                <td className="px-3 py-2 text-[var(--ink-2)]">{CFI_CATEGORY[c.cfi?.[0] ?? ""] ?? "—"}</td>
                <td className="mono px-3 py-2 text-[var(--ink-2)]">{c.cfi ?? "—"}</td>
              </tr>
            ))}
            {rows.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-3 py-6 text-center text-[var(--ink-2)]">No match.</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
