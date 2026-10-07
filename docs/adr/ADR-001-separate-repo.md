# ADR-001 — Security Passport is a separate repo

**Status:** accepted (v0.1.0)

## Decision

Security Passport is its own repository, package, API, and frontend.
It consumes OpenInstrument strictly through the versioned REST
contract (`/v1/*`, `/v2/*`), never through imports or file paths.

## Rationale

- Different product question: OpenInstrument answers *"what is this
  instrument and how do we know"*; Security Passport answers
  *"what is this ISIN's operational dossier — issuance docs, venues,
  settlement evidence, collateral treatment"*.
- Different source coverage: PRIII document graphs, ECB eligible
  assets, ECB SSS/links, and Iberclear evidence live here because
  they are primary sources for this product, not upstream gaps.
- Independent release cadence, schema version, and release gate
  (`unsupported_assertions = 0`).

## Consequences

- Fixture mode lets the repo build/demo without OpenInstrument.
- Upstream API drift is contained behind one provider class
  (`OpenInstrumentApiProvider`).
