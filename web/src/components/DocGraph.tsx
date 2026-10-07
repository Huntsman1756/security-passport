import type { DocNode } from "../types";

const TYPE_ORDER = ["BASE", "STDA", "FNTE", "SUPP", "SECN", "SUMM"];

export function DocGraph({ docs }: { docs: DocNode[] }) {
  if (!docs.length) return null;
  const sorted = [...docs].sort(
    (a, b) =>
      TYPE_ORDER.indexOf(a.document_type) -
      TYPE_ORDER.indexOf(b.document_type),
  );
  return (
    <div className="px-2 py-1">
      {sorted.map((d) => (
        <div
          key={d.root_id}
          className="relative ml-3 border-l border-[var(--line)] pb-4 pl-4 last:pb-1"
        >
          <span
            className="absolute -left-[5px] top-1.5 h-2.5 w-2.5 rounded-full border border-[var(--accent)] bg-[var(--surface)]"
            aria-hidden
          />
          <div className="flex flex-wrap items-baseline gap-x-3">
            <span className="text-[13px] font-medium">
              {d.document_type_descr || d.document_type}
            </span>
            <span className="mono text-[11px] text-[var(--ink-2)]">
              {d.national_document_id}
            </span>
            {d.is_passported ? (
              <span className="rounded border border-sky-600/40 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-sky-700 dark:text-sky-400">
                passported
              </span>
            ) : null}
          </div>
          <div className="mono mt-1 text-[11.5px] leading-relaxed text-[var(--ink-2)]">
            approved {d.approval_filing_date || "—"}
            {d.first_passporting_date
              ? ` · first passported ${d.first_passporting_date}`
              : ""}
            {d.member_states.length
              ? ` · host: ${d.member_states.join(", ")}`
              : ""}
            {d.home_member_state
              ? ` · home: ${d.home_member_state}`
              : ""}
          </div>
          <div className="mt-0.5 text-[11.5px] text-[var(--ink-2)]">
            {d.party_name}
            {d.languages ? ` · ${d.languages}` : ""}
          </div>
          {d.related_document_ids.length ? (
            <div className="mono mt-0.5 text-[11px] text-[var(--ink-2)]">
              related: {d.related_document_ids.join(" · ")}
            </div>
          ) : null}
          {d.download_url ? (
            <a
              href={d.download_url}
              target="_blank"
              rel="noreferrer"
              className="mt-1 inline-block text-[12px] text-[var(--accent)] underline-offset-2 hover:underline"
            >
              document PDF ↗
            </a>
          ) : null}
        </div>
      ))}
    </div>
  );
}
