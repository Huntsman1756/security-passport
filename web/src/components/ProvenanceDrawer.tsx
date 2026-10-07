import type { PassportField } from "../types";
import { StatusBadge } from "./StatusBadge";

function Row({
  label, children, mono,
}: {
  label: string; children: React.ReactNode; mono?: boolean;
}) {
  return (
    <div className="grid grid-cols-[7.5rem_1fr] gap-3 py-1.5">
      <div className="text-[11px] uppercase tracking-wide text-[var(--ink-2)]">
        {label}
      </div>
      <div className={mono ? "mono text-[12px] break-all" : "text-[13px]"}>
        {children}
      </div>
    </div>
  );
}

export function ProvenanceDrawer({
  name,
  field,
  onClose,
}: {
  name: string;
  field: PassportField;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-black/40"
      role="dialog"
      aria-modal="true"
      aria-label={`Provenance for ${name}`}
      onClick={onClose}
    >
      <div
        className="h-full w-full max-w-xl overflow-y-auto border-l border-[var(--line)] bg-[var(--surface)] p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div>
            <div className="text-[11px] uppercase tracking-widest text-[var(--ink-2)]">
              field provenance
            </div>
            <h2 className="mono mt-1 text-lg font-semibold">{name}</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded border border-[var(--line)] px-2 py-1 text-sm text-[var(--ink-2)] hover:bg-[var(--surface-2)]"
            aria-label="Close provenance"
          >
            ✕
          </button>
        </div>

        <div className="mt-4 flex items-center gap-3">
          <StatusBadge status={field.status} />
          {(field.quality_flags ?? []).map((f) => (
            <span
              key={f}
              className="rounded border border-amber-500/40 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-amber-700 dark:text-amber-400"
            >
              {f}
            </span>
          ))}
        </div>

        <div className="mono mt-4 rounded border border-[var(--line)] bg-[var(--surface-2)] px-3 py-2 text-sm break-all">
          {field.value === null || field.value === undefined
            ? "—"
            : typeof field.value === "object"
              ? JSON.stringify(field.value)
              : String(field.value)}
        </div>

        {field.explanation ? (
          <p className="mt-3 text-[13px] leading-relaxed text-[var(--ink-2)]">
            {field.explanation}
          </p>
        ) : null}

        {field.rule ? (
          <section className="mt-5">
            <h3 className="text-[11px] font-semibold uppercase tracking-widest text-[var(--ink-2)]">
              Rule
            </h3>
            <Row label="Rule" mono>
              {field.rule.rule_id}.v{field.rule.rule_version}
            </Row>
            {field.rule.basis ? (
              <Row label="Basis">{field.rule.basis}</Row>
            ) : null}
            {field.rule.limitations ? (
              <Row label="Limitations">{field.rule.limitations}</Row>
            ) : null}
            {(field.rule.inputs ?? []).length ? (
              <Row label="Inputs" mono>
                {JSON.stringify(field.rule.inputs)}
              </Row>
            ) : null}
          </section>
        ) : null}

        <section className="mt-5">
          <h3 className="text-[11px] font-semibold uppercase tracking-widest text-[var(--ink-2)]">
            Evidence ({(field.evidence ?? []).length})
          </h3>
          {(field.evidence ?? []).length === 0 && (
            <p className="mt-1 text-[13px] text-[var(--ink-2)]">
              No evidence attached.
            </p>
          )}
          {(field.evidence ?? []).map((e, i) => (
            <div
              key={i}
              className="mt-3 rounded border border-[var(--line)] p-3"
            >
              <Row label="Source" mono>
                {e.provider} / {e.dataset}
              </Row>
              <Row label="Record" mono>{e.record_id}</Row>
              {e.artifact_id ? (
                <Row label="Artifact" mono>{e.artifact_id}</Row>
              ) : null}
              {e.source_locator ? (
                <Row label="Locator" mono>{e.source_locator}</Row>
              ) : null}
              {e.retrieved_at ? (
                <Row label="Retrieved" mono>{e.retrieved_at}</Row>
              ) : null}
              {e.published_at ? (
                <Row label="Published" mono>{e.published_at}</Row>
              ) : null}
              {e.effective_at ? (
                <Row label="Effective" mono>{e.effective_at}</Row>
              ) : null}
              {e.raw_value !== undefined && e.raw_value !== null ? (
                <Row label="Raw value" mono>
                  {JSON.stringify(e.raw_value)}
                </Row>
              ) : null}
              {(e.transformations ?? []).length ? (
                <Row label="Transforms">
                  {(e.transformations ?? []).join(" → ")}
                </Row>
              ) : (
                <Row label="Transforms">None</Row>
              )}
              {e.upstream ? (
                <Row label="Upstream" mono>
                  {e.upstream.provider} · {e.upstream.artifact} ·{" "}
                  {e.upstream.locator}
                </Row>
              ) : null}
            </div>
          ))}
        </section>

        {(field.alternatives ?? []).length ? (
          <section className="mt-5">
            <h3 className="text-[11px] font-semibold uppercase tracking-widest text-amber-700 dark:text-amber-400">
              Conflicting assertions ({(field.alternatives ?? []).length})
            </h3>
            {(field.alternatives ?? []).map((a, i) => (
              <div
                key={i}
                className="mt-2 rounded border border-amber-500/40 p-3"
              >
                <Row label="Value" mono>
                  {JSON.stringify(a.value)}
                </Row>
                {a.role ? <Row label="Role">{a.role}</Row> : null}
                <Row label="Source" mono>
                  {a.evidence.provider}/{a.evidence.dataset}
                </Row>
              </div>
            ))}
          </section>
        ) : null}

        {(field.searched_sources ?? []).length ? (
          <section className="mt-5">
            <h3 className="text-[11px] font-semibold uppercase tracking-widest text-[var(--ink-2)]">
              Checked sources
            </h3>
            <ul className="mono mt-2 list-inside list-disc text-[12px] text-[var(--ink-2)]">
              {(field.searched_sources ?? []).map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {field.temporal ? (
          <section className="mt-5">
            <h3 className="text-[11px] font-semibold uppercase tracking-widest text-[var(--ink-2)]">
              Temporal basis
            </h3>
            <Row label="Basis" mono>{field.temporal.basis}</Row>
            <Row label="Semantics" mono>
              {field.temporal.source_time_semantics}
            </Row>
            {field.temporal.left_censored ? (
              <Row label="Censoring">left-censored</Row>
            ) : null}
          </section>
        ) : null}
      </div>
    </div>
  );
}
