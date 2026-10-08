import type { ReactNode } from "react";

const BASIS_LABEL: Record<string, string> = {
  reconstructed: "reconstructed history",
  observed_history: "observed history",
  native_history: "native history",
  current_only: "current snapshot only",
};

export function Block({
  id,
  title,
  question,
  temporal,
  warnings,
  children,
}: {
  id: string;
  title: string;
  question?: string;
  temporal?: { basis?: string; left_censored?: boolean;
               answer_state?: string | null;
               answer_note?: string };
  warnings?: string[];
  children: ReactNode;
}) {
  const available = temporal?.answer_state === "available";
  return (
    <section id={id} className="scroll-mt-20 rounded-lg border border-[var(--line)] bg-[var(--surface)]">
      <header className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[var(--line)] px-4 py-3">
        <div className="flex items-baseline gap-3">
          <h2 className="text-[12px] font-semibold uppercase tracking-[0.18em]">{title}</h2>
          {question ? <span className="hidden text-[12.5px] text-[var(--ink-2)] sm:inline">{question}</span> : null}
        </div>
        {temporal?.basis ? (
          <span className="flex items-center gap-2 text-[11px] text-[var(--ink-2)]">
            <span title="How this block's history is known">
              {BASIS_LABEL[temporal.basis] ?? temporal.basis}
              {temporal.left_censored ? " · left-censored" : ""}
            </span>
            {temporal.answer_state ? (
              <span
                title={temporal.answer_note}
                className={`rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide ${
                  available
                    ? "border-emerald-600/40 text-emerald-700 dark:text-emerald-400"
                    : "border-amber-500/50 text-amber-700 dark:text-amber-400"
                }`}
              >
                at T: {temporal.answer_state.replaceAll("_", " ")}
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

export function SubList({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mt-3 px-2">
      <div className="text-[10.5px] font-medium uppercase tracking-wider text-[var(--ink-2)]">{title}</div>
      <div className="mt-1.5">{children}</div>
    </div>
  );
}
