## What this changes

## Contract surface

- [ ] This does **not** change the passport JSON schema, status
  taxonomies, or public CLI/API surface — OR a release note
  under `docs/release/` documents the change.

## Gates

- [ ] `pytest tests/` passes (offline)
- [ ] `ruff check src tests` clean
- [ ] `mypy src` strict clean
- [ ] `security-passport validate` → `unsupported_assertions = 0`
- [ ] No current value substituted into an `outside_coverage`
      block under `--as-of`
- [ ] No new `FieldStatus` value introduced
- [ ] Every positive (`reported`/`derived`/`inferred`) field has
      evidence

## Data / licensing

- [ ] No proprietary, confidential, or non-public data in code,
      fixtures, docs, or tests
- [ ] New sources are in `docs/sources/source-registry.md` with
      an honest access classification; restricted sources are
      never silently scraped
