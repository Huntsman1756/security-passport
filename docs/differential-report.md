# Differential test report — v0.1.1

Cross-pipeline comparisons between Security Passport output and
upstream assertions. UNEXPLAINED diffs block release.

## ECB eligible assets — SP ingestion vs OpenInstrument adapter

Both pipelines ingest the same ECB file; different snapshots.
Comparison via `services/differential.compare_ecb_asset` +
`tests/contract/test_differential.py`.

| ISIN | SP snapshot | OI version | Result |
|---|---|---|---|
| XS2081615473 | ea_csv_261006 | 260925 | all fields SAME/SKEW |
| ES0000101966 | ea_csv_261006 | 260925 | same |
| DE000A3LJCB4 | absent | absent | same absence |
| FR0129714681 | absent | absent* | same absence |
| XSSE2WKP7HV5 | absent | absent | same absence |

*fixture-captured OI row set is limited to corpus ISINs.

Verdicts observed in tests: `SAME`, `SOURCE_VERSION_SKEW`
(snapshots differ), `EXPECTED_TRANSFORMATION` (case-normalized
issuer names). No `UNEXPLAINED`, no `BUG`.

## Taxonomy enforcement

`test_taxonomy_blocks_unexplained` proves a field mismatch under
identical snapshots classifies `UNEXPLAINED` and blocks; version
skew never blocks.

## OpenInstrument `/v1/evidence`

Upstream bug reproduced, fixed and pinned (openinstrument
commit `50e9677` — dynamic partition resolution). Regression test
`test_evidence_uses_instrument_snapshot_not_hardcoded` added
upstream; SP pins `MIN_OPENINSTRUMENT_COMMIT` in
`providers/openinstrument/api.py`.

## ISIN validation — custom vs python-stdnum

`tests/unit/test_isin_stdnum.py`: agreement asserted on the whole
golden corpus; a property test asserts `stdnum ⇒ legacy` on every
generated 12-char input. The single deliberate divergence is
`XX`-prefixed ISINs: the retired Luhn accepted `XX0000000002` on
check digit alone; `stdnum.isin` additionally enforces a real
ISO 3166 issuance prefix — the stricter semantic is correct and
the corpus now uses `XSSE2WKP7HV5` (real prefix, zero evidence).
