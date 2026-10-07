# Data authority matrix — field granularity

No silent dual authority. For every passport fact: one
authoritative provider, optionally corroborating + fallback.

## IDENTITY

| field | authoritative | corroborating | fallback |
|---|---|---|---|
| isin structure/checksum | `python-stdnum` (ISO 6166) | — | — |
| cfi / fisn / name | OpenInstrument canonical | — | FISN for display name |
| issuer_lei | OpenInstrument (conflict state preserved) | GLEIF via upstream | — |
| issuer_name | GLEIF via OpenInstrument | PRIII issuer_name, ECB issuer_name | PRIII/ECB |
| instrument_type | derived rule `instrument_type` on CFI | — | — |
| maturity_date | ECB row | PRIII `ifii_matExpDate` | `not_applicable` via `dated_instrument_scope` |
| entity roles | OpenInstrument v2 (authoritative role semantics) | OpenFunds for ES IIC | — |

## PRIMARY MARKET

| field | authoritative | corroborating | fallback |
|---|---|---|---|
| prospectus_found | PRIII document graph (ESMA) | — | — |
| document family/graph | PRIII | emisiones-es CNMV docs (ES only, corroborate — never overwrite) | — |
| home/host member states | PRIII | — | — |
| approval date | PRIII | emisiones-es | — |
| passported | PRIII `is_passported` | — | — |

## SECONDARY MARKET

| field | authoritative | corroborating | fallback |
|---|---|---|---|
| listings (ISIN×MIC) | OpenInstrument FIRDS | — | — |
| venue state (active/term.) | rule `venue_state` on FIRDS dates | — | — |
| venue name | ISO 10383 via **OpenVenue** | own MIC store (transition only) | raw MIC |
| operating_mic / segment_mic | OpenVenue (registry reconciled) | ISO 10383 direct | — |
| venue operator | OpenVenue | — | — |
| rulebook ref/version | OpenVenue + venue-rule-diff (precomputed) | — | — |
| first_admission_date | rule `first_admission` (min real date) | — | — |

## POST-TRADE

| field | authoritative | corroborating | fallback |
|---|---|---|---|
| issuer SSS identity | ECB eligible-assets `ISSUER_CSD` (instrument-level) | Iberclear public docs (name mapping only) | — |
| instrument-level CSD admission | posttrade-europe instrument-level lists where they exist (e.g. ES Milan eligible ISINs) | — | `not_found` |
| eligible SSS topology | ECB eligible-SSS page | — | — |
| SSS↔SSS links | ECB eligible-links page | — | — |
| settlement path | **never asserted** without instrument-level evidence | — | — |

## EUROSYSTEM COLLATERAL

| field | authoritative | corroborating | fallback |
|---|---|---|---|
| eligible (current snapshot) | ECB eligible-assets enumeration | OpenInstrument `collateral_eligible` (differential-gated) | — |
| haircut category / haircut | ECB row | OpenInstrument assertion | — |
| issuer CSD | ECB row | posttrade CSD identity | — |
| historical eligibility | **security-passport** (own product logic) | — | — |
| haircut regime eval | **security-passport** | — | — |

## Ordering rule

When two sources carry the same fact: display the authoritative
one; attach the corroborating as additional evidence on the same
field; if they disagree, the field becomes `conflict` with both
alternatives — never silently pick one.
