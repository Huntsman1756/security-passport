import type { ReactNode } from "react";

const BASIS_LABEL: Record<string, string> = {
  reconstructed: "reconstructed history",
  observed_history: "observed history",
  native_history: "native history",
  current_only: "current only",
};

export function Block({
  title,
  temporal,
  warnings,
  children,
}: {
  title: string;
  temporal?: { basis?: string; left_censored?: boolean;
               answer_state?: string | null;
               answer_note?: string };
  warnings?: string[];
  children: ReactNode;
}) {
  return (
    <section className="rounded-lg border border-[var(--line)] bg-[var(--surface)]">
      <header className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[var(--line)] px-4 py-2.5">
        <h2 className="text-[12px] font-semibold uppercase tracking-[0.18em] text-[var(--ink-2)]">
          {title}
        </h2>
        {temporal?.basis ? (
          <span className="text-[11px] text-[var(--ink-2)]">
            temporal: {BASIS_LABEL[temporal.basis] ?? temporal.basis}
            {temporal.left_censored ? " · left-censored" : ""}
            {temporal.answer_state ? (
              <span style={{
                marginLeft: 8, padding: "1px 6px",
                border: "1px solid currentColor",
                borderRadius: 3, fontSize: 10,
                color: temporal.answer_state === "available"
                  ? "#4a7" : "#c73",
              }}>
                at T: {temporal.answer_state}
              </span>
            ) : null}
          </span>
        ) : null}
      </header>
      {warnings?.map((w, i) => (
        <div
          key={i}
          className="border-b border-amber-500/30 bg-amber-500/5 px-4 py-1.5 text-[12px] text-amber-700 dark:text-amber-400"
        >
          {w}
        </div>
      ))}
      <div className="px-2 py-2">{children}</div>
    </section>
  );
}
