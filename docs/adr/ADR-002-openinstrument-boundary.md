# ADR-002 — OpenInstrument integration boundary

**Status:** accepted (v0.1.0)

## Decision

One port: `InstrumentProvider` (Protocol). Implementations:

- `OpenInstrumentApiProvider` — httpx against `OPENINSTRUMENT_URL`.
  Pins the upstream generation once per passport build
  (`/v1/status` → `generation`); a mid-build CURRENT flip cannot
  mix snapshots inside one passport.
- `FixtureInstrumentProvider` — captured API payloads +
  own-source fixture stores; the whole pipeline runs offline.

No `OpenInstrumentDataRootProvider` (direct parquet) in v0.1.0:
no measured performance need, and it would couple us to upstream
storage layout.

## Rationale

- The upstream contract is frozen (G6) and additive-versioned;
  depending on internals would silently re-implement its
  adjudication and conflict preservation.
- Evidence stays verifiable: upstream `artifact_sha256` + `locator`
  values are carried verbatim into our `EvidenceRef` objects as
  `upstream_locator`, so a passport claim can be traced back to the
  exact upstream artifact.

## Consequences

- If OpenInstrument is down, the API degrades per-block
  (`SOURCE_UNAVAILABLE` on affected fields) — a fallen upstream
  never produces invented data.
- Our generation manifest records the pinned
  `openinstrument_generation` for reproducibility.
