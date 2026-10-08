import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-24 text-center">
      <p className="mono text-[12px] uppercase tracking-[0.2em] text-[var(--ink-3)]">404</p>
      <h1 className="mt-2 text-2xl font-semibold">No such page</h1>
      <p className="mt-3 text-[14px] text-[var(--ink-2)]">
        Passports live at <span className="mono">/isin/&lt;ISIN&gt;</span>.
      </p>
      <Link to="/" className="mt-6 inline-block text-[13px] text-[var(--accent)] hover:underline">
        ← Back to search
      </Link>
    </div>
  );
}
