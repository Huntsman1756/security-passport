import { useCallback, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchPassport, ApiRequestError } from "../api";
import type { PassportField, PassportBlock } from "../types";
import { Field } from "../components/Field";
import { Block, SubList } from "../components/Block";
import { ListingsTable } from "../components/ListingsTable";
import { DocGraph } from "../components/DocGraph";
import { ProvenanceDrawer } from "../components/ProvenanceDrawer";
import { CoverageBar } from "../components/CoverageBar";
import { useServiceStatus } from "../lib/status";

function F(
  blk: PassportBlock,
  key: string,
): PassportField | undefined {
  const v = blk[key];
  return v && typeof v === "object" && "status" in (v as object)
    ? (v as PassportField)
    : undefined;
}

function str(f: unknown): string | undefined {
  const v = (f as PassportField | undefined)?.value;
  return typeof v === "string" && v ? v : undefined;
}

const SECTIONS = [
  ["identity", "Identity"],
  ["primary-market", "Primary market"],
  ["secondary-market", "Secondary market"],
  ["post-trade", "Post-trade"],
  ["collateral", "Eurosystem collateral"],
] as const;

const STATE_CLS: Record<string, string> = {
  found: "border-emerald-600/40 text-emerald-700 dark:text-emerald-400",
  partial: "border-amber-500/40 text-amber-700 dark:text-amber-400",
};

function AsOfControl({ asOf }: { asOf?: string }) {
  const [, setParams] = useSearchParams();
  return (
    <label className="flex items-center gap-2 text-[12px] text-[var(--ink-2)]">
      <span title="Ask what was knowable and effective on a past date">As of</span>
      <input
        type="date"
        value={asOf ?? ""}
        max={new Date().toISOString().slice(0, 10)}
        onChange={(e) =>
          setParams(e.target.value ? { as_of: e.target.value } : {})}
        className="mono h-8 rounded-md border border-[var(--line)] bg-[var(--surface-2)] px-2 text-[12px] outline-none focus:border-[var(--accent)]"
      />
      {asOf ? (
        <button
          onClick={() => setParams({})}
          className="text-[12px] underline underline-offset-2 hover:text-[var(--ink)]"
        >
          today
        </button>
      ) : null}
    </label>
  );
}

function CopyLink() {
  const [done, setDone] = useState(false);
  return (
    <button
      onClick={() => {
        void navigator.clipboard?.writeText(window.location.href).then(() => {
          setDone(true);
          setTimeout(() => setDone(false), 1500);
        });
      }}
      className="h-8 rounded-md border border-[var(--line)] px-3 text-[12px] text-[var(--ink-2)] hover:bg-[var(--surface-2)] hover:text-[var(--ink)]"
    >
      {done ? "Copied" : "Copy link"}
    </button>
  );
}

function Skeleton() {
  return (
    <div className="mx-auto max-w-6xl animate-pulse px-4 py-8" aria-busy="true" aria-label="Loading passport">
      <div className="h-8 w-64 rounded bg-[var(--surface-2)]" />
      <div className="mt-3 h-4 w-96 max-w-full rounded bg-[var(--surface-2)]" />
      <div className="mt-6 h-2 w-full rounded bg-[var(--surface-2)]" />
      {[0, 1, 2].map((i) => (
        <div key={i} className="mt-6 h-40 rounded-lg border border-[var(--line)] bg-[var(--surface-2)]/50" />
      ))}
    </div>
  );
}

export function PassportPage() {
  const { isin = "" } = useParams();
  const [params] = useSearchParams();
  const asOf = params.get("as_of") ?? undefined;
  const st = useServiceStatus();
  const q = useQuery({
    queryKey: ["passport", isin, asOf],
    queryFn: () => fetchPassport(isin, asOf),
    retry: (n, e) =>
      !(e instanceof ApiRequestError &&
        (e.code === "INVALID_ISIN" || e.code === "INVALID_AS_OF")) &&
      n < 2,
  });
  const [drawer, setDrawer] = useState<{
    name: string;
    field: PassportField;
  } | null>(null);
  const open = (name: string, field: PassportField) =>
    setDrawer({ name, field });
  const closeDrawer = useCallback(() => setDrawer(null), []);

  const p = q.data;

  const roles = useMemo(
    () => (p?.identity.entity_roles ?? []),
    [p],
  );

  if (q.isLoading) return <Skeleton />;

  if (q.isError || !p) {
    const err = q.error;
    const code = err instanceof ApiRequestError ? err.code : "";
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center">
        <h1 className="mono text-2xl font-semibold">{isin}</h1>
        <p className="mt-4 text-[var(--ink-2)]">
          {code === "INVALID_ISIN"
            ? "This is not a valid ISIN — structure or check digit failed."
            : code === "INVALID_AS_OF"
              ? "The as-of date is not a valid ISO date."
              : code === "SOURCE_UNAVAILABLE"
                ? "A required data source is unavailable. The passport cannot be assembled right now."
                : "The passport could not be loaded."}
        </p>
        <p className="mono mt-2 text-[12px] text-[var(--ink-2)]">
          {err instanceof Error ? err.message : ""}
        </p>
        <Link to="/" className="mt-6 inline-block text-[13px] text-[var(--accent)] hover:underline">
          ← Back to search
        </Link>
      </div>
    );
  }

  const id = p.identity;
  const pm = p.primary_market;
  const sm = p.secondary_market;
  const pt = p.post_trade;
  const ec = p.eurosystem_collateral;

  const name = str(id.instrument_name) ?? str(id.fisn);
  const issuer = str(id.issuer_name) ?? str(id.issuer_lei);
  const maturity = str(id.maturity_date);
  const chips = [
    str(id.cfi),
    str(id.notional_currency),
    str(id.instrument_type),
    maturity ? `matures ${maturity}` : undefined,
  ].filter((c): c is string => !!c);
  const demo = st.data?.demo;
  const outsideCorpus = !!demo && !demo.corpus.some((c) => c.isin === p.isin);

  return (
    <div className="mx-auto max-w-6xl px-4 pb-16">
      {/* header */}
      <header className="border-b border-[var(--line)] py-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="mono text-2xl font-semibold tracking-wide sm:text-3xl">
                {p.isin}
              </h1>
              <span
                className={`rounded border px-2 py-0.5 text-[11px] uppercase tracking-wide ${
                  STATE_CLS[p.overall_state] ?? "border-slate-400/40 text-slate-500"
                }`}
                title="found: every block answered · partial: some blocks not found · unknown: no source knows this ISIN"
              >
                {p.overall_state}
              </span>
            </div>
            <div className="mt-1.5 text-[15px] font-medium">{name ?? "Unnamed instrument"}</div>
            {issuer ? <div className="mono mt-0.5 text-[12.5px] text-[var(--ink-2)]">{issuer}</div> : null}
            {chips.length ? (
              <div className="mt-2.5 flex flex-wrap gap-1.5">
                {chips.map((c) => (
                  <span key={c} className="mono rounded border border-[var(--line)] bg-[var(--surface-2)] px-1.5 py-0.5 text-[11px] text-[var(--ink-2)]">
                    {c}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <AsOfControl asOf={asOf} />
            <CopyLink />
            <a
              href={`/api/v1/passports/${p.isin}${asOf ? `?as_of=${asOf}` : ""}`}
              className="grid h-8 place-items-center rounded-md border border-[var(--line)] px-3 text-[12px] text-[var(--ink-2)] hover:bg-[var(--surface-2)] hover:text-[var(--ink)]"
            >
              JSON
            </a>
          </div>
        </div>
        <div className="mt-5 max-w-xl">
          <CoverageBar passport={p} />
        </div>
        <div className="mono mt-3 text-[11px] text-[var(--ink-2)]">
          generated {p.generated_at} · generation {p.generation} ·
          upstream {p.openinstrument_generation || "—"}
          {asOf ? ` · as of ${asOf}` : ""}
        </div>
        {outsideCorpus ? (
          <div className="mt-3 rounded border border-sky-500/40 bg-sky-500/5 px-3 py-2 text-[12.5px] text-sky-800 dark:text-sky-300">
            This ISIN is outside the demo corpus, so no source here knows it.
            That is reported as <strong>unknown</strong>, never as “does not exist”.{" "}
            <Link to="/corpus" className="underline underline-offset-2">See which instruments are covered</Link>.
          </div>
        ) : null}
        {p.warnings.map((w, i) => (
          <div
            key={i}
            className="mt-2 rounded border border-amber-500/40 bg-amber-500/5 px-3 py-1.5 text-[12px] text-amber-700 dark:text-amber-400"
          >
            {w}
          </div>
        ))}
      </header>

      <div className="mt-6 lg:grid lg:grid-cols-[11rem_1fr] lg:gap-8">
        <nav aria-label="Passport sections" className="hidden lg:block">
          <ul className="sticky top-20 space-y-1 text-[12.5px]">
            {SECTIONS.map(([sid, label]) => (
              <li key={sid}>
                <a href={`#${sid}`} className="block rounded px-2 py-1 text-[var(--ink-2)] hover:bg-[var(--surface-2)] hover:text-[var(--ink)]">
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="min-w-0 space-y-5">
          <Block id="identity" title="Identity" question="What is it?" temporal={id.temporal}>
            <Field label="ISIN" name="identity.isin"
              field={F(id, "isin")} onOpen={open} />
            <Field label="CFI" name="identity.cfi"
              field={F(id, "cfi")} onOpen={open} />
            <Field label="FISN" name="identity.fisn"
              field={F(id, "fisn")} onOpen={open} />
            <Field label="Instrument name" name="identity.instrument_name"
              field={F(id, "instrument_name")} onOpen={open} />
            <Field label="Instrument type" name="identity.instrument_type"
              field={F(id, "instrument_type")} onOpen={open} />
            <Field label="Issuer LEI" name="identity.issuer_lei"
              field={F(id, "issuer_lei")} onOpen={open} />
            <Field label="Issuer name" name="identity.issuer_name"
              field={F(id, "issuer_name")} onOpen={open} />
            <Field label="Currency" name="identity.notional_currency"
              field={F(id, "notional_currency")} onOpen={open} />
            <Field label="Maturity" name="identity.maturity_date"
              field={F(id, "maturity_date")} onOpen={open} />
            <Field label="Competent authority"
              name="identity.competent_authority"
              field={F(id, "competent_authority")} onOpen={open} />
            {roles.length ? (
              <SubList title="Entity roles">
                <div className="flex flex-wrap gap-1.5">
                  {roles.slice(0, 12).map((r, i) => {
                    const cls = "mono rounded border border-[var(--line)] px-1.5 py-0.5 text-[11px] text-[var(--ink-2)]";
                    const label = `${r.role}: ${r.lei}`;
                    return /^[A-Z0-9]{18}[0-9]{2}$/.test(r.lei) ? (
                      <a
                        key={i}
                        href={`https://search.gleif.org/#/record/${r.lei}`}
                        target="_blank"
                        rel="noreferrer"
                        className={`${cls} hover:border-[var(--accent)] hover:text-[var(--ink)]`}
                        title={`${r.source} · open in GLEIF`}
                      >
                        {label}
                      </a>
                    ) : (
                      <span key={i} className={cls} title={r.source}>{label}</span>
                    );
                  })}
                </div>
              </SubList>
            ) : null}
          </Block>

          <Block id="primary-market" title="Primary market" question="Which documents support it?" temporal={pm.temporal}
            warnings={pm.warnings}>
            <Field label="Prospectus found" name="primary_market.prospectus_found"
              field={F(pm, "prospectus_found")} onOpen={open} />
            <Field label="Home member state" name="primary_market.home_member_state"
              field={F(pm, "home_member_state")} onOpen={open} />
            <Field label="Host states" name="primary_market.host_member_states"
              field={F(pm, "host_member_states")} onOpen={open} />
            <Field label="Approval date" name="primary_market.approval_filing_date"
              field={F(pm, "approval_filing_date")} onOpen={open} />
            <Field label="Passported" name="primary_market.is_passported"
              field={F(pm, "is_passported")} onOpen={open} />
            {(pm.document_graph ?? []).length ? (
              <SubList title="Document graph">
                <DocGraph docs={pm.document_graph ?? []} />
              </SubList>
            ) : null}
          </Block>

          <Block id="secondary-market" title="Secondary market" question="Where is it admitted to trading?" temporal={sm.temporal}>
            <div className="grid gap-x-6 sm:grid-cols-2">
              <Field label="Venue records" name="secondary_market.listing_count"
                field={F(sm, "listing_count")} onOpen={open} />
              <Field label="Active venues" name="secondary_market.active_venue_count"
                field={F(sm, "active_venue_count")} onOpen={open} />
            </div>
            <Field label="First admission" name="secondary_market.first_admission_date"
              field={F(sm, "first_admission_date")} onOpen={open} />
            <ListingsTable listings={sm.listings ?? []} />
          </Block>

          <Block id="post-trade" title="Post-trade" question="How could it settle?" temporal={pt.temporal}>
            <Field label="Issuer CSD" name="post_trade.issuer_csd"
              field={F(pt, "issuer_csd")} onOpen={open} />
            <Field label="Settlement locations"
              name="post_trade.settlement_location_count"
              field={F(pt, "settlement_location_count")} onOpen={open} />
            <Field label="Iberclear admitted" name="post_trade.iberclear_admitted"
              field={F(pt, "iberclear_admitted")} onOpen={open} />
            <Field label="Eligible SSSs" name="post_trade.eligible_sss_count"
              field={F(pt, "eligible_sss_count")} onOpen={open} />
            <Field label="Assessment" name="post_trade.assessment"
              field={F(pt, "assessment")} onOpen={open} />
            {(pt.settlement_locations ?? []).length ? (
              <SubList title="Settlement locations · instrument-level evidence">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-[12.5px]">
                    <thead className="text-[10.5px] uppercase tracking-wider text-[var(--ink-2)]">
                      <tr>
                        <th className="py-1 pr-3 font-medium">CSD</th>
                        <th className="py-1 pr-3 font-medium">Relationship</th>
                        <th className="py-1 pr-3 font-medium">Market</th>
                        <th className="py-1 pr-3 font-medium">Published</th>
                        <th className="py-1 pr-3 font-medium">Effective</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(pt.settlement_locations ?? []).map((l, i) => (
                        <tr key={i} className="border-t border-[var(--line)]">
                          <td className="py-1.5 pr-3">{l.csd}</td>
                          <td className="mono py-1.5 pr-3 text-[var(--ink-2)]">{l.relationship.replaceAll("_", " ")}</td>
                          <td className="mono py-1.5 pr-3 text-[var(--ink-2)]">{l.mic || "—"}</td>
                          <td className="mono py-1.5 pr-3 text-[var(--ink-2)]">{l.source_published_at || "—"}</td>
                          <td className="mono py-1.5 pr-3">
                            {l.effective_from ?? "—"}
                            {l.effective === true ? (
                              <span className="ml-1.5 rounded border border-emerald-600/40 px-1 text-[9.5px] uppercase text-emerald-700 dark:text-emerald-400">effective</span>
                            ) : l.effective === false ? (
                              <span className="ml-1.5 rounded border border-amber-500/50 px-1 text-[9.5px] uppercase text-amber-700 dark:text-amber-400">not yet</span>
                            ) : null}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </SubList>
            ) : null}
            {(pt.link_topology ?? []).length ? (
              <SubList title="Link topology · infrastructure, not instrument routes">
                <ul className="mono space-y-0.5 text-[12px] text-[var(--ink-2)]">
                  {(pt.link_topology ?? []).slice(0, 12).map((l, i) => (
                    <li key={i}>
                      {l.investor_csd}
                      {(l.intermediaries ?? []).length
                        ? ` via ${l.intermediaries.join(" → ")}`
                        : ""}{" "}
                      → {l.issuer_csd}
                      {l.link_type ? ` [${l.link_type}]` : ""}
                      {l.operated_by ? ` (${l.operated_by})` : ""}
                    </li>
                  ))}
                  {(pt.link_topology ?? []).length > 12 ? (
                    <li>… {(pt.link_topology ?? []).length - 12} more in the JSON</li>
                  ) : null}
                </ul>
              </SubList>
            ) : null}
            {(pt.route_assessments ?? []).length ? (
              <SubList title="Route assessments · inferred, with limitations">
                <ul className="space-y-1.5 text-[12.5px]">
                  {(pt.route_assessments ?? []).map((a, i) => (
                    <li key={i} className="rounded border border-violet-500/30 px-2.5 py-1.5">
                      <span className="mono text-[11px] uppercase text-violet-700 dark:text-violet-400">{a.assessment.replaceAll("_", " ")}</span>
                      {a.from_sss && a.to_sss ? (
                        <span className="mono ml-2 text-[11.5px] text-[var(--ink-2)]">{a.from_sss} → {a.to_sss}</span>
                      ) : null}
                      <p className="mt-0.5 text-[var(--ink-2)]">{a.explanation}</p>
                      {a.limitations ? (
                        <p className="mt-0.5 text-[11.5px] italic text-[var(--ink-3)]">Limitation: {a.limitations}</p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </SubList>
            ) : null}
          </Block>

          <Block id="collateral" title="Eurosystem collateral" question="Is it eligible collateral?" temporal={ec.temporal}>
            <Field label="Eligible" name="eurosystem_collateral.eligible"
              field={F(ec, "eligible")} onOpen={open} />
            <Field label="Snapshot" name="eurosystem_collateral.ecb_snapshot"
              field={F(ec, "ecb_snapshot")} onOpen={open} />
            <Field label="Haircut category" name="eurosystem_collateral.haircut_category"
              field={F(ec, "haircut_category")} onOpen={open} />
            <Field label="Haircut" name="eurosystem_collateral.haircut"
              field={F(ec, "haircut")} onOpen={open} />
            <Field label="Asset type" name="eurosystem_collateral.asset_type"
              field={F(ec, "asset_type")} onOpen={open} />
            <Field label="Issuer CSD" name="eurosystem_collateral.issuer_csd"
              field={F(ec, "issuer_csd")} onOpen={open} />
            <Field label="Coupon" name="eurosystem_collateral.coupon_rate"
              field={F(ec, "coupon_rate")} onOpen={open} />
            <Field label="Covered bond" name="eurosystem_collateral.covered_bond_flag"
              field={F(ec, "covered_bond_flag")} onOpen={open} />
          </Block>

          <p className="px-1 text-[12px] leading-relaxed text-[var(--ink-2)]">
            Every field carries provenance. Click any row for its source
            record, rule, raw value and any conflicting assertions. Unknown
            is a valid result; absence is never rendered as false.
          </p>
        </div>
      </div>

      {drawer ? (
        <ProvenanceDrawer
          name={drawer.name}
          field={drawer.field}
          onClose={closeDrawer}
        />
      ) : null}
    </div>
  );
}
