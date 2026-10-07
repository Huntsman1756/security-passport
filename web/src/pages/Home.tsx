import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { status } from "../api";

const EXAMPLES: { isin: string; label: string; asOf?: string }[] = [
  { isin: "IE00B4L5Y983", label: "temporal/post-trade",
    asOf: "2026-09-19" },
  { isin: "DE000A3LJCB4", label: "equity passport" },
  { isin: "IE0007SRI1C7", label: "issuer-LEI conflict" },
  { isin: "ES0105321030", label: "CNMV fund roles" },
  { isin: "FR0129714681", label: "ECB-only unknown" },
];

export function Home() {
  const [q, setQ] = useState("");
  const nav = useNavigate();
  const st = useQuery({ queryKey: ["status"], queryFn: status });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const v = q.trim().toUpperCase();
    if (v.length === 12) nav(`/isin/${v}`);
  };

  return (
    <div className="mx-auto flex min-h-[calc(100vh-10rem)] max-w-2xl flex-col items-center justify-center px-4">
      <h1 className="text-center text-3xl font-semibold tracking-tight">
        Security Passport
      </h1>
      <p className="mt-3 max-w-md text-center text-[15px] leading-relaxed text-[var(--ink-2)]">
        What is this security, where does it trade, what supports it,
        and how can it settle?
      </p>

      <form onSubmit={submit} className="mt-8 flex w-full max-w-lg gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Enter ISIN"
          maxLength={12}
          autoFocus
          spellCheck={false}
          className="mono h-11 flex-1 rounded-md border border-[var(--line)] bg-[var(--surface-2)] px-4 text-[15px] tracking-wider outline-none placeholder:text-[var(--ink-2)] focus:border-[var(--accent)]"
          aria-label="ISIN"
        />
        <button
          type="submit"
          className="h-11 rounded-md bg-[var(--accent)] px-5 text-[14px] font-medium text-white hover:opacity-90"
        >
          Search
        </button>
      </form>

      <div className="mt-4 flex flex-wrap justify-center gap-2">
        {EXAMPLES.map((e) => (
          <button
            key={e.isin}
            onClick={() =>
              nav(`/isin/${e.isin}` +
                  (e.asOf ? `?as_of=${e.asOf}` : ""))}
            title={e.label}
            className="mono rounded border border-[var(--line)] px-2.5 py-1 text-[11.5px] text-[var(--ink-2)] hover:border-[var(--accent)] hover:text-[var(--ink)]"
          >
            {e.isin}
            {e.asOf ? `·${e.asOf.slice(5)}` : ""}
          </button>
        ))}
      </div>

      <div className="mt-10 flex gap-6 text-[12px] text-[var(--ink-2)]">
        <span>Evidence-backed</span>
        <span>·</span>
        <span>European public data</span>
        <span>·</span>
        <span>Field-level provenance</span>
      </div>

      {st.data ? (
        <div className="mono mt-6 text-[11px] text-[var(--ink-2)]">
          generation {String(st.data.generation ?? "—")} · upstream{" "}
          {String(st.data.openinstrument_generation ?? "—")}
        </div>
      ) : null}
    </div>
  );
}
