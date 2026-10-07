# Contributing

Security Passport is maintained primarily as a research-grade
evidence product. Contributions are welcome for correctness,
reproducibility, and new **publicly reproducible** sources —
not for broad data coverage.

## Architecture entry points

- `src/security_passport/services/passport_builder.py` —
  adjudication: the only place `FieldStatus` is assigned
- `src/security_passport/providers/` — source adapters (normalize
  raw evidence, never decide epistemology)
- `src/security_passport/domain/` — the public contract:
  `FieldStatus`, `AssessmentVerdict`, `TemporalAnswerState`,
  `TemporalBasis`, `PassportField`, evidence refs
- `src/security_passport/services/update.py` — acquisition:
  every fetch becomes a captured artifact
- `tests/fixtures/corpus/` + `tests/fixtures/goldens.yaml` —
  offline fixture corpus; every provider must run against it

## Setup

```console
make setup                    # python deps + web deps
security-passport doctor      # verify environment
security-passport DE000A3LJCB4  # fixture mode, fully offline
```

## Checks

`make check` — ruff + mypy strict + pytest + frontend build.
`security-passport validate` — golden corpus + release gates.

## Hard rules

- **No positive assertion without evidence.** `reported`,
  `derived`, `inferred` all require evidence refs; a missing
  value is `not_found` with named searched sources.
- **No new `FieldStatus`.** The taxonomy is closed; a recursive
  test enforces it across every passport field and collection.
- **No silent current-for-historical substitution.** At
  `--as-of=T`, a block whose evidence is unavailable at T reports
  `outside_coverage` — never substitutes current data.
- **Access taxonomy is binding.** `AUTH_REQUIRED`, `PREMIUM`,
  `BLOCKED_POLICY` sources are never silently scraped.
- **No non-public data in fixtures, issues, or PRs** — public or
  synthetic evidence only.

## Adding a provider

1. Implement the port in `providers/base.py` style: normalize to
   facts, carry `observed_at`/`published_at`/`effective_from`,
   never assign a `FieldStatus`.
2. Register the source in `docs/sources/source-registry.md` with
   an honest access classification.
3. Capture fixtures into `tests/fixtures/corpus/<provider>/` —
   no live network in tests.
4. Add a golden or contract test proving the field wiring.
5. The provider's `User-Agent` comes from
   `security_passport.user_agent()` — never a literal.

## Updating an existing parser

Bump `parser_version` in the provider, capture the new artifact
shape into fixtures, and let `validate` show the semantic
fingerprint drift.

## Contract changes

Anything that changes the JSON schema of a passport is a
contract change: it needs a `docs/release/` note and a passing
`oasdiff` run.
