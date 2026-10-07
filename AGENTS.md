# AGENTS.md — Security Passport

## What this is

Evidence-backed operational passport for European financial
instruments. Thin, read-only product over the OpenInstrument
security master (`openinstrument` (sibling project, pinned) — upstream, do not
modify) plus own-source stores. Start at `README.md`, then
`docs/architecture.md`, `docs/domain.md`.

## Operating principles

- `reported` / `derived` / `inferred` / `conflict` / `not_found` /
  `not_applicable` are enforced per field, validated in
  `services/validate.py`. Release gate:
  **unsupported_assertions = 0**.
- `Unknown` is a valid result. Absence is `not_found`, never
  `false` — unless an authoritative enumeration + rule justify a
  derivation (see `eurosystem_eligibility`).
- Conflicts are preserved, not silently adjudicated.
- No settlement-path inference from generic SSS/link topology.
- One normalization per concept — live fetch, update pipeline,
  and fixture replay share the exact same code.
- Generations publish via staging → manifest → atomic `CURRENT`
  swap; readers pin `CURRENT` once.
- Source licensing/attribution is part of the model
  (`docs/legal/`).

## Environment (Windows host)

- `python -m pip install -e ".[dev]"` — console script:
  `security-passport`.
- Fixture mode runs fully offline:
  `SECURITY_PASSPORT_PROVIDER=fixtures`,
  `SECURITY_PASSPORT_FIXTURES=tests/fixtures/corpus`.
- Production: `SECURITY_PASSPORT_PROVIDER=openinstrument_api`,
  `OPENINSTRUMENT_URL=…`, `SECURITY_PASSPORT_DATA=data`.
- Web: `cd web && pnpm install && pnpm dev` (proxies `/api` →
  :8000).

## Verification

```bash
pytest tests/ -q && ruff check src tests && mypy src
security-passport validate    # golden corpus release gate
cd web && pnpm lint && pnpm typecheck && pnpm test && pnpm build
```

Fixture corpus refresh: `python scripts/capture_fixtures.py`
(requires OpenInstrument API running + network).

## Layout

- `src/security_passport/domain/` — isin, status, evidence,
  fields, rules, passport
- `src/security_passport/providers/` — `base` (ports/facts),
  `openinstrument/api`, `fixtures`, own-source adapters
- `src/security_passport/storage/` — `generations` (publish/
  fingerprint/rollback), `store` (GenerationStore reader)
- `src/security_passport/services/` — `passport_builder`,
  `update`, `validate`
- `src/security_passport/api/app.py`, `cli/main.py`
- `web/` — Vite + React 19 + Tailwind 4 SPA
- `infra/` — Dockerfiles, Caddy, systemd units
- `docs/` — ADRs (`adr/`), `reuse/`, `legal/`, `sources/`,
  `architecture.md`, `domain.md`, `api.md`, `cli.md`,
  `runbook.md`, `release/`
