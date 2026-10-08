# Roadmap

Guiding constraint: the project should stay cheap to run and to
maintain. Each item lists the value it adds and its rough cost.

## Landscape (October 2026)

No open-source tool combines FIRDS, the prospectus register,
venue admissions, settlement evidence and ECB collateral data
per ISIN with field-level provenance. The closest references:

- **eFIRDS** (Nordic Trustee / Stamdata): commercial FIRDS +
  FCA FIRDS + GLEIF lookup and API. Covers identity and venues,
  but has no provenance model and no post-trade or collateral
  data.
- **OpenSanctions securities**: open data built from FIRDS and
  GLEIF, with statement-level provenance (every value traces to a
  source dataset). This is the closest analogue to this project's
  evidence model, but its focus is sanctions.
- Small single-market ISIN lookups on GitHub (Canada, Turkey…):
  name ↔ ISIN only.

Security Passport is differentiated by its evidence semantics
(not_found ≠ false, preserved conflicts, temporal `as_of`). Keep
investing there, not in breadth of data.

## Next (small, high value)

| item | why | cost |
|---|---|---|
| Tag `v0.3.0` (UI redesign + demo deployment) | releases page and GHCR images match what is live | S |
| CSV/JSON "evidence ledger" download on the passport page | the OpenSanctions-style statement export; `/evidence` already exists | S |
| `as_of` diff view (today vs date T) | makes the temporal model visible in one screen | M |
| Mark `tests/integration/test_update.py` as `slow` and run it only in CI | local suite drops from ~2.5 min to well under a minute | S |
| Uptime check on `passport.h1756.es/health/ready` (existing Telegram alerts) | proves the demo stays up without manual checks | S |

## Later

- OG image per passport (static render of the header + coverage
  bar) for sharing on LinkedIn.
- Full mode on the VPS once OpenInstrument is deployed (see
  `h1756.es/baseline/PROYECTOS-PREVISTOS.md`). Requires RAM and disk
  budgeting; the demo stays as a fallback.
- Bulk lookup (paste up to N ISINs → coverage table), only if
  real users ask for it.

## Not planned

Prices, portfolios, alerts, accounts, LLM chat. See README.
