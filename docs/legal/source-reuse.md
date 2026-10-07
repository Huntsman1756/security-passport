# Source reuse review

Per-provider legal assessment. `retrieved_at` refers to the
v0.1.0 review; recheck on each major source-contract change.

## esma_firds (via OpenInstrument)

```yaml
provider: esma_firds
source: ESMA FIRDS (Financial Instruments Reference Data System)
owner: European Securities and Markets Authority (ESMA)
reuse_basis: ESMA Registers Legal Notice — reproduction authorised
  provided the source is acknowledged and a transformation notice
  is displayed
attribution_required: true
transformation_notice_required: true
redistribution_constraints: derived/transformed projection only;
  we do not redistribute raw FULINS/DLTINS files
raw_redistribution_allowed: false
retrieved_at: 2026-10-07
notes: |
  Security Passport transforms and combines REGISTERS information.
  ESMA has not endorsed this product. Same posture as upstream
  (docs/licensing/firds-legal-review.md in openinstrument).
```

## esma_priii

```yaml
provider: esma_priii
source: ESMA Registers — Prospectus III (documents + securities Solr)
owner: ESMA
reuse_basis: ESMA Registers Legal Notice (same as FIRDS)
attribution_required: true
transformation_notice_required: true
redistribution_constraints: we store document metadata + public
  RFSS download locators; PDFs are linked, not mirrored
raw_redistribution_allowed: false
retrieved_at: 2026-10-07
notes: RFSS file ids are public locators on registers.esma.europa.eu.
```

## ecb_eligible_assets

```yaml
provider: ecb_eligible_assets
source: ECB — List of eligible marketable assets (ea_csv)
owner: European Central Bank
reuse_basis: ECB publishes the daily list for public consultation;
  upstream licensing review classifies it PUBLIC_WITH_ATTRIBUTION
attribution_required: true
transformation_notice_required: true
redistribution_constraints: derived facts projected; raw CSV kept
  as local evidence
raw_redistribution_allowed: false
retrieved_at: 2026-10-07
notes: snapshot-per-day; we keep observed history.
```

## ecb_sss_links

```yaml
provider: ecb_sss_links
source: ECB — List of eligible SSSs / List of eligible links
owner: European Central Bank
reuse_basis: public operational documentation
attribution_required: true
transformation_notice_required: true
redistribution_constraints: topology + "Last updated" stamp quoted
  with provenance
raw_redistribution_allowed: false
retrieved_at: 2026-10-07
notes: HTML pages, no machine contract — parsed as observed evidence.
```

## gleif (via OpenInstrument)

```yaml
provider: gleif
source: GLEIF ISIN-to-LEI relationship files + golden copy
owner: Global Legal Entity Identifier Foundation
reuse_basis: CC0
attribution_required: false
transformation_notice_required: false
redistribution_constraints: none material
raw_redistribution_allowed: true
retrieved_at: 2026-10-07
notes: still attributed for provenance clarity.
```

## openinstrument

```yaml
provider: openinstrument
source: OpenInstrument API (v1/v2)
owner: Huntsman1756/openinstrument (MIT)
reuse_basis: MIT code; consumed as a service, not vendored
attribution_required: true (attribution shown in /sources)
transformation_notice_required: n/a
redistribution_constraints: n/a
raw_redistribution_allowed: n/a
retrieved_at: 2026-10-07
notes: carries upstream per-source licensing (FIRDS notice applies
  transitively to FIRDS-derived fields it serves).
```

## iso10383_mic

```yaml
provider: iso10383_mic
source: ISO 10383 MIC list (registration authority: SWIFT/ISO)
owner: ISO / SWIFT SCRL
reuse_basis: publicly downloadable reference list; used to label
  venue MICs, not to redistribute the registry
attribution_required: true
transformation_notice_required: false
redistribution_constraints: MIC code + market name only
raw_redistribution_allowed: false
retrieved_at: 2026-10-07
```

## iberclear

```yaml
provider: iberclear
source: BME / Iberclear public documentation
owner: Bolsas y Mercados Españoles (Iberclear)
reuse_basis: public documentation; no machine-readable instrument
  registry is publicly offered
attribution_required: true
transformation_notice_required: false
redistribution_constraints: curated facts only; instrument-level
  assertions come only from ECB/FIRDS evidence
raw_redistribution_allowed: false
retrieved_at: 2026-10-07
notes: v0.1.0 uses Iberclear only as a named SSS in ECB topology —
  never as a source of instrument-level claims.
```

## Not used

- Bloomberg / any commercial vendor: never a datasource.
- esma_data_py: EUPL-1.2 prior art — no code copied.
