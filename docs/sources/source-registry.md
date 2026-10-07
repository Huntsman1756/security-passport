# Source registry

Canonical list of providers Security Passport consumes. Every
`EvidenceRef.provider` value must be registered here.

| provider | dataset | access | semantics | history basis | notes |
|---|---|---|---|---|---|
| `openinstrument` | `v1/v2 REST` | `OPENINSTRUMENT_URL` | adjudicated FIRDS/GLEIF/OpenFIGI projection | `reconstructed` (publication-time) | upstream; its own provenance carried through |
| `esma_firds` | `fulins/dltins` | via openinstrument | regulatory reference data; field5 = "issuer or venue operator" | `reconstructed` | evidence refs surface upstream artifact+locator |
| `esma_priii` | `priii_documents` | Solr select (registers.esma.europa.eu) | prospectus filings, parent/child graph | `observed_history` | M2M surface; RFSS doc locators public |
| `ecb_eligible_assets` | `ea_csv` | HTTPS bulk CSV (UTF-16 TSV, daily) | authoritative eligible-asset enumeration | `observed_history` → native when multi-snapshot | includes `ISSUER_CSD`, haircut inputs |
| `ecb_sss_links` | `eligiblesss` + `ssslinks` HTML | HTTPS pages | Eurosystem SSS/link eligibility | `observed_history` ("Last updated" stamp) | topology ≠ instrument eligibility |
| `gleif` | `isin_lei + golden` | via openinstrument | ISIN↔LEI + entity master | `reconstructed` | role semantics matter — see entity roles |
| `iso10383_mic` | `mic.csv` | HTTPS public CSV | market identifier code registry | `observed_history` | venue naming only |
| `iberclear` | curated | none (facts doc) | SSS identity only | `current_only` | no instrument-level claims v0.1 |

## Sentinel / absence semantics

| source | sentinel | meaning |
|---|---|---|
| FIRDS | `9999-12-31...` in date fields | "not provided" — never a real date |
| FIRDS | record absent from FULINS | NOT "doesn't exist" — check DLTINS/history |
| ECB ea_csv | ISIN absent from snapshot | not eligible **as of that snapshot** (authoritative enumeration) |
| PRIII | no filings for ISIN | `not_found` — may be exempt, out of scope, or unregistered; never "no prospectus exists" as a fact |
