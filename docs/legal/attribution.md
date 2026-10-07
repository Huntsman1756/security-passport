# Required attribution strings

These strings must appear in the UI (`/sources`), README, and the
API `/api/v1/status` response.

## ESMA registers (FIRDS + PRIII)

> Source: European Securities and Markets Authority (ESMA),
> ESMA Registers — FIRDS reference data and Prospectus register.
> Security Passport transforms and combines the original REGISTERS
> information. ESMA has not reviewed or endorsed this product.

## ECB

> Source: European Central Bank — list of eligible marketable
> assets, list of eligible securities settlement systems, and list
> of eligible links. Data shown is a transformed projection of the
> published information; retrieval dates are shown per field.

## GLEIF

> Source: Global Legal Entity Identifier Foundation (GLEIF) —
> ISIN-to-LEI relationship data (CC0).

## ISO 10383

> Market Identifier Codes per ISO 10383; registration authority
> SWIFT. Codes and market names shown for identification only.

## Iberclear

> Iberclear (BME) is named as a securities settlement system in
> Eurosystem publications. No instrument-level data is sourced
> from Iberclear.

## OpenInstrument

> Instrument reference data via OpenInstrument
> (Huntsman1756/openinstrument, MIT) — itself a transformed
> projection of the sources above.

## Generic disclaimer

> Security Passport is an independent evidence-backed projection
> of public European regulatory data. It is not endorsed by ESMA,
> the ECB, GLEIF, ISO/SWIFT, or BME/Iberclear.

## v0.1.1 additions

- `python-stdnum` 2.2+ — LGPL-2.1+. Used as a library for
  ISO 6166/17442 validation; no code copied; dynamic linking
  satisfies the licence.
- `schemathesis` 4.x — MIT. Test-only dependency.
- `oasdiff` — Apache-2.0. CI tool, not distributed.
- ECB Eligible Assets Dictionary — public data, verbatim labels
  preserved as codebook evidence.
- Euronext Securities Milan ISIN-eligibility workbook — public
  operational file; rows carry artifact SHA-256 + file date.
- `openinstrument/artifacts/store.py` (MIT, same-owner) —
  pattern ported to `evidence/store.py`.
- `posttrade-europe/capture` (Apache-2.0, same-owner) —
  retrieval-attempt semantics ported.
