# AGENTS.md — Security Passport

## What this is

Evidence-backed operational passport for European financial
instruments. Thin, read-only product over the OpenInstrument
security master (`openinstrument` (sibling project, pinned) — upstream, do not
modify) plus own-source stores. Start at `README.md`, then
`docs/architecture.md`, `docs/domain.md`.

**Purpose and scope.** A public, professional portfolio piece
for the owner (live at <https://passport.h1756.es>). Priorities, in
order: correct → trustworthy to a domain expert → low maintenance
→ polished. Prefer small, verifiable improvements over new
surface area. Out of scope: prices, portfolios, watchlists,
alerts, auth, LLM chat (see README "What it does not do").

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
- **Copy is a claim too.** Any UI/README text that describes an
  instrument or a capability (e.g. the showcase cards in
  `web/src/pages/Home.tsx`) must be checked against the built
  passport before shipping. Never describe the demo as live data.

## Environment (Windows host)

- Python venv: `.venv` (use `.venv/Scripts/python -m …` from Git
  Bash). `python -m pip install -e ".[dev]"` — console script:
  `security-passport`. CI uses `uv sync --frozen --extra dev`.
- Fixture mode runs fully offline:
  `SECURITY_PASSPORT_PROVIDER=fixtures`,
  `SECURITY_PASSPORT_FIXTURES=tests/fixtures/corpus`.
- Production (full) mode: `SECURITY_PASSPORT_PROVIDER=openinstrument_api`,
  `OPENINSTRUMENT_URL=…`, `SECURITY_PASSPORT_DATA=data`.
- Web: `cd web && pnpm install && pnpm dev` (proxies `/api` and
  `/health` → :8000). Run the API on :8000 in fixture mode first.
- Pi stack (Pi + Gentle Shell + Ponytail, NaN provider) is
  installed project-locally in `.pi/`. Activate with
  `. .\.pi\bin\activate.ps1` (PowerShell) or
  `source .pi/bin/activate.sh`, then `pi --stack-check` / `pi`.
  Runtime dirs under `.pi/` are git-ignored; only
  `.pi/settings.json`, `.pi/extensions/` and `.pi/npm/.gitignore`
  are tracked. Never commit credentials (`NAN_API_KEY`).

### Host pitfalls

- The workstation often runs many other projects' test suites in
  parallel. A suite that normally takes ~2 min can take >10 min:
  run long commands in the background instead of assuming a hang.
  If vitest reports "Failed to start forks worker … Timeout",
  rerun with `pnpm exec vitest run --maxWorkers=1` — it is load,
  not a test failure.
- Python one-liners that read repo files must pass
  `encoding="utf-8"` (default codepage is cp1252).
- Git Bash paths (`/f/...`) are not understood by Windows Python;
  use `F:/...` or repo-relative paths.

## Verification (definition of done)

```bash
pytest tests/ -q && ruff check src tests && mypy src
security-passport validate    # golden corpus release gate
cd web && pnpm lint && pnpm typecheck && pnpm test && pnpm build
# e2e: API on :8000 (fixtures) + `pnpm dev`, then
PW_BASE_URL=http://localhost:5173 pnpm exec playwright test
python scripts/check_public_hygiene.py
```

UI changes: also look at the result (light + dark, 390 px mobile,
no horizontal overflow, no console errors). API changes: keep
`tests/fixtures/openapi-baseline.json` non-breaking
(`make openapi-check`); additive fields are fine, new request
constraints are not — validate in the handler instead.

Fixture corpus refresh: `python scripts/capture_fixtures.py`
(requires OpenInstrument API running + network). The corpus is
also the public demo's data; refreshing it changes the demo.

## Deployment (public demo)

`passport.h1756.es` runs `infra/h1756/compose.yml` on the H1756
VPS: fixture mode, corpus mounted read-only from
`/data/security-passport/corpus`, Coolify Traefik routing by
label, no published ports. Procedure and rollback:
`docs/runbook.md` → "Public demo". Deploying is an outward action:
only with the owner's go-ahead, and record each change in the
private ops repo `h1756-vps-ops` (`baseline/CAMBIOS.md`).

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
- `web/` — Vite + React 19 + Tailwind 4 SPA. `src/pages/`
  (Home, Passport, Corpus, Sources, NotFound), `src/components/`,
  `src/lib/` (ISIN check, status hook, status metadata, coverage
  — non-component exports live here for fast-refresh), `e2e/`
  (Playwright, desktop + mobile)
- `infra/` — Dockerfiles, Caddy, systemd units, `h1756/` (demo
  compose)
- `docs/` — ADRs (`adr/`), `reuse/`, `legal/`, `sources/`,
  `architecture.md`, `domain.md`, `api.md`, `cli.md`,
  `runbook.md`, `roadmap.md`, `release/`
