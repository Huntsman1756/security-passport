# ADR-006 — Post-trade is evidence-only in v0.1.0

**Status:** accepted (v0.1.0)

## Decision

The POST-TRADE block reports evidence and exactly one conservative
inference class:

- `issuer_sss` — reported when ECB eligible assets publishes
  `ISSUER_CSD` for the ISIN (mapped to CSD name via the eligible
  SSS list); otherwise `not_found`.
- `eligible_sss` / `eligible_links` — the published Eurosystem
  topology, reported verbatim with observation metadata.
- `possible_paths` — **requires** (a) a reported issuer SSS and
  (b) instrument-specific evidence of admission/holding in the
  investor-side SSS. Without (b), no path is asserted.
- `assessment` — a deterministic statement of what the evidence
  does and does not establish (`settlement_path.v1`).

Explicitly NOT built: a settlement router, CSD inference from ISIN
prefix (`DE` ⇒ Clearstream is a discovery hint, never a fact),
link-topology ⇒ instrument-eligibility jumps.

## Rationale

"A link between two SSSs exists" says nothing about whether a
given ISIN can settle across it. Asserting otherwise is the single
most dangerous wrong answer this product could give. `not_found`
with a full explanation of what was checked is a feature.
