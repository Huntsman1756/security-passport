# Source registry

Canonical list of providers Security Passport consumes. Every
`EvidenceRef.provider` value must be registered here.

| provider | dataset | access | semantics | history basis | notes |
|---|---|---|---|---|---|
| `openinstrument` | `v1/v2 REST` | `OPENINSTRUMENT_URL` / `PUBLIC_MACHINE_READABLE` | adjudicated FIRDS/GLEIF/OpenFIGI projection | `reconstructed` (publication-time) | upstream; its own provenance carried through |
| `esma_firds` | `fulins/dltins` | via openinstrument | regulatory reference data; field5 = "issuer or venue operator" | `reconstructed` | evidence refs surface upstream artifact+locator |
| `esma_priii` | `priii_documents` | Solr select (registers.esma.europa.eu) / `PUBLIC_MACHINE_READABLE` | prospectus filings, parent/child graph | `observed_history` | M2M surface; RFSS doc locators public |
| `ecb_eligible_assets` | `ea_csv` | HTTPS bulk CSV (UTF-16 TSV, daily) / `PUBLIC_MACHINE_READABLE` | authoritative eligible-asset enumeration | `observed_history` → native when multi-snapshot | includes `ISSUER_CSD`, haircut inputs |
| `ecb_sss_links` | `eligiblesss` + `ssslinks` HTML | HTTPS pages / `PUBLIC_MACHINE_READABLE` | Eurosystem SSS/link eligibility | `observed_history` ("Last updated" stamp) | topology ≠ instrument eligibility |
| `ecb_collateral_dictionary` | `dictionary.en.html` | HTTPS page / `PUBLIC_MACHINE_READABLE` | official codebook for ECB codes | `observed_history` | issuer-CSD/asset-type/issuer-group labels |
| `euronext_esmil` | `isin_eligibility_file` | HTTPS dated XLSX / `PUBLIC_MACHINE_READABLE` | instrument-level CSD admission (ES Milan) | `observed_history` + `effective_from` | publication date ≠ go-live |
| `euronext_frs` | `isins_for_french_registered_shares` | HTTPS dated XLSX / `PUBLIC_MACHINE_READABLE` | FR registered shares + issuer CSD | `observed_history` | same docs page family |
| `euronext_porto_custody` | `securities_under_custody` | HTML table w/ ISIN filter / `PUBLIC_HUMAN_LOOKUP` | instrument-level custody (ES Porto) | `observed_history` | CSV endpoint returns 404; per-ISIN page lookup only, no crawler |
| `gleif` | `isin_lei + golden` | via openinstrument | ISIN↔LEI + entity master | `reconstructed` | role semantics matter — see entity roles |
| `iso10383_mic` | `mic.csv` | HTTPS public CSV / `PUBLIC_MACHINE_READABLE` | market identifier code registry | `observed_history` | venue naming only |
| `iberclear` | curated | none (facts doc) | SSS identity only | `current_only` | no instrument-level claims v0.1 |
| `clearstream_eligible` | securities list | `PREMIUM` — **not ingested** | eligible-securities list exists per Clearstream docs | — | never silently scraped; `PROBED_RESTRICTED` |
| `euroclear_isin_lookup` | isin_codes.html | `AUTH_REQUIRED` — **not ingested** | guest lookup for Euroclear Bank/ESES | — | corroboration only via manual research; no crawler |

## Access classification

| class | rule |
|---|---|
| `PUBLIC_MACHINE_READABLE` | bulk/reproducible artifact — ingest freely with artifact SHA-256 |
| `PUBLIC_HUMAN_LOOKUP` | interactive page — manual corroboration only; no automation |
| `AUTH_REQUIRED` | credentials needed — **never silently scraped** |
| `PREMIUM` | paywalled content — **never silently scraped** |
| `BLOCKED_POLICY` | ToS prohibits machine access — **never ingested** |
| `UNAVAILABLE` | attempted capture failed — attempt recorded as data |

Hard rule: `AUTH_REQUIRED`, `PREMIUM` and `BLOCKED_POLICY` are
classified `PROBED_RESTRICTED` and are never harvested — a failed
probe is recorded in `attempts.jsonl`, nothing else. Coverage is
never traded for reproducibility.

## Sentinel / absence semantics

| source | sentinel | meaning |
|---|---|---|
| FIRDS | `9999-12-31...` in date fields | "not provided" — never a real date |
| FIRDS | record absent from FULINS | NOT "doesn't exist" — check DLTINS/history |
| ECB ea_csv | ISIN absent from snapshot | not eligible **as of that snapshot** (authoritative enumeration) |
| PRIII | no filings for ISIN | `not_found` — may be exempt, out of scope, or unregistered; never "no prospectus exists" as a fact |
