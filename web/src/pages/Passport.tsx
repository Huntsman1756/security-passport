import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchPassport, ApiRequestError } from "../api";
import type { PassportField, PassportBlock } from "../types";
import { Field } from "../components/Field";
import { Block } from "../components/Block";
import { ListingsTable } from "../components/ListingsTable";
import { DocGraph } from "../components/DocGraph";
import { ProvenanceDrawer } from "../components/ProvenanceDrawer";

function F(
  blk: PassportBlock,
  key: string,
): PassportField | undefined {
  const v = blk[key];
  return v && typeof v === "object" && "status" in (v as object)
    ? (v as PassportField)
    : undefined;
}

export function PassportPage() {
  const { isin = "" } = useParams();
  const q = useQuery({
    queryKey: ["passport", isin],
    queryFn: () => fetchPassport(isin),
    retry: (n, e) =>
      !(e instanceof ApiRequestError && e.code === "INVALID_ISIN") &&
      n < 2,
  });
  const [drawer, setDrawer] = useState<{
    name: string;
    field: PassportField;
  } | null>(null);
  const open = (name: string, field: PassportField) =>
    setDrawer({ name, field });

  const p = q.data;

  const roles = useMemo(
    () => (p?.identity.entity_roles ?? []),
    [p],
  );

  if (q.isLoading)
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 text-center text-[var(--ink-2)]">
        Loading passport…
      </div>
    );

  if (q.isError || !p) {
    const err = q.error;
    const code = err instanceof ApiRequestError ? err.code : "";
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 text-center">
        <h1 className="mono text-2xl font-semibold">{isin}</h1>
        <p className="mt-4 text-[var(--ink-2)]">
          {code === "INVALID_ISIN"
            ? "This is not a valid ISIN — structure or check digit failed."
            : code === "SOURCE_UNAVAILABLE"
              ? "A required data source is unavailable. The passport cannot be assembled right now."
              : "The passport could not be loaded."}
        </p>
        <p className="mono mt-2 text-[12px] text-[var(--ink-2)]">
          {err instanceof Error ? err.message : ""}
        </p>
      </div>
    );
  }

  const id = p.identity;
  const pm = p.primary_market;
  const sm = p.secondary_market;
  const pt = p.post_trade;
  const ec = p.eurosystem_collateral;

  const name = (id.instrument_name as PassportField | undefined)
    ?.value;
  const lei = (id.issuer_lei as PassportField | undefined)?.value;
  const issuerName = (id.issuer_name as PassportField | undefined)
    ?.value;

  return (
    <div className="mx-auto max-w-5xl px-4 pb-16">
      {/* header */}
      <header className="border-b border-[var(--line)] py-5">
        <div className="flex flex-wrap items-baseline gap-x-4">
          <h1 className="mono text-2xl font-semibold tracking-wide">
            {p.isin}
          </h1>
          <span
            className={`rounded border px-2 py-0.5 text-[11px] uppercase tracking-wide ${
              p.overall_state === "found"
                ? "border-emerald-600/40 text-emerald-700 dark:text-emerald-400"
                : p.overall_state === "partial"
                  ? "border-amber-500/40 text-amber-700 dark:text-amber-400"
                  : "border-slate-400/40 text-slate-500"
            }`}
          >
            {p.overall_state}
          </span>
        </div>
        <div className="mt-1.5 flex flex-wrap gap-x-5 text-[13px] text-[var(--ink-2)]">
          <span>{typeof name === "string" ? name : "—"}</span>
          <span className="mono">
            {typeof issuerName === "string"
              ? issuerName
              : typeof lei === "string"
                ? lei
                : ""}
          </span>
          <span className="mono">
            {(id.notional_currency as PassportField | undefined)
              ?.value as string ?? ""}
            {" · "}
            {(id.instrument_type as PassportField | undefined)
              ?.value as string ?? ""}
          </span>
        </div>
        <div className="mono mt-1 text-[11px] text-[var(--ink-2)]">
          generated {p.generated_at} · generation {p.generation} ·
          upstream {p.openinstrument_generation || "—"}
        </div>
        {p.warnings.map((w, i) => (
          <div
            key={i}
            className="mt-2 rounded border border-amber-500/40 bg-amber-500/5 px-3 py-1.5 text-[12px] text-amber-700 dark:text-amber-400"
          >
            {w}
          </div>
        ))}
      </header>

      <div className="mt-5 space-y-5">
        {/* IDENTITY */}
        <Block title="Identity" temporal={id.temporal}>
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
            <div className="px-2 py-1.5">
              <div className="text-[11px] uppercase tracking-wider text-[var(--ink-2)]">
                Entity roles
              </div>
              <div className="mt-1 flex flex-wrap gap-1.5">
                {(roles ?? []).slice(0, 12).map((r, i) => (
                  <span
                    key={i}
                    className="mono rounded border border-[var(--line)] px-1.5 py-0.5 text-[11px] text-[var(--ink-2)]"
                    title={`${r.role} · ${r.source}`}
                  >
                    {r.role}: {r.lei.slice(0, 10)}…
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </Block>

        {/* PRIMARY MARKET */}
        <Block title="Primary market" temporal={pm.temporal}
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
          <DocGraph docs={pm.document_graph ?? []} />
        </Block>

        {/* SECONDARY MARKET */}
        <Block title="Secondary market" temporal={sm.temporal}>
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

        {/* POST-TRADE */}
        <Block title="Post-trade" temporal={pt.temporal}>
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
            <div className="mt-2 px-2">
              <div className="text-[11px] uppercase tracking-wider text-[var(--ink-2)]">
                Settlement locations (instrument-level)
              </div>
              <ul className="mono mt-1 space-y-0.5 text-[12px] text-[var(--ink-2)]">
                {(pt.settlement_locations ?? []).map((l, i) => (
                  <li key={i}>
                    {l.csd} — {l.relationship}
                    {l.mic ? ` via ${l.mic}` : ""}
                    {l.effective_from
                      ? ` (from ${l.effective_from})`
                      : ""}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {(pt.link_topology ?? []).length ? (
            <div className="mt-2 px-2">
              <div className="text-[11px] uppercase tracking-wider text-[var(--ink-2)]">
                Link topology (infrastructure, not routes)
              </div>
              <ul className="mono mt-1 space-y-0.5 text-[12px] text-[var(--ink-2)]">
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
              </ul>
            </div>
          ) : null}
          {(pt.route_assessments ?? []).length ? (
            <div className="mt-2 px-2">
              <div className="text-[11px] uppercase tracking-wider text-[var(--ink-2)]">
                Route assessments (inferred)
              </div>
              <ul className="mono mt-1 space-y-0.5 text-[12px] text-[var(--ink-2)]">
                {(pt.route_assessments ?? []).map((a, i) => (
                  <li key={i}>
                    {a.from_sss && a.to_sss
                      ? `${a.from_sss} → ${a.to_sss}: `
                      : ""}
                    [{a.state}] {a.assessment}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </Block>

        {/* EUROSYSTEM COLLATERAL */}
        <Block title="Eurosystem collateral" temporal={ec.temporal}>
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

        <p className="px-1 text-[11.5px] leading-relaxed text-[var(--ink-2)]">
          Every field carries provenance — click any row for source,
          rule, raw values and conflicting assertions. Unknown is a
          valid result; absence is never rendered as false.
        </p>
      </div>

      {drawer ? (
        <ProvenanceDrawer
          name={drawer.name}
          field={drawer.field}
          onClose={() => setDrawer(null)}
        />
      ) : null}
    </div>
  );
}
