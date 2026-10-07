# Repository hardening — v0.2.x (post-release pass)

Pure repository engineering; no passport semantics changed.

## Issues found → fixed

| issue | fix |
|---|---|
| Three version sources (`pyproject` 0.2.0, `__init__` 0.1.2, web 0.1.0, UAs 0.1.0) | `__version__` now resolves via `importlib.metadata`; all provider UAs use `security_passport.user_agent()`; web `version` removed, `packageManager: pnpm@12.9.1` pinned |
| Local drive paths on `AGENTS.md`, `REUSE_AUDIT_V2.md` | Replaced by sibling-project + pinned-tag references; commit pins preserved |
| `pnpm install --frozen-lockfile \|\| pnpm install` — fallback silently re-resolved | Fallback removed; a bad lockfile now fails the build |
| CI: `oasdiff@latest`, unpinned actions, no permissions block, no timeouts | All actions pinned by commit SHA w/ human version comments; `permissions: contents: read`; `concurrency` + `timeout-minutes` per job; oasdiff pinned to `v1.15.1` |
| Python 3.11/3.13 declared, only 3.12 tested | `python-matrix` job runs unit+contract tests on 3.11/3.12/3.13; heavy jobs stay on 3.12 |
| `str, Enum` deprecated pattern (UP042 under locked ruff) | Migrated to `StrEnum` (all serialization already used `.value`) |
| `.hypothesis/` + `.ruff_cache/` tracked caches | Ignored |
| vitest critical + medium Dependabot alerts | Upgraded vitest 5.0.3 + jsdom 30.1.2 + @vitejs/plugin-react 5.2.0 + jest-dom 7.0.1 — all tests/build green; alerts now 0 |

## Reproducibility

- `uv.lock` committed; `uv sync --frozen --extra dev` in CI.
- Dockerfile.api installs from `uv export --frozen --no-emit-project` — no resolution at image build.
- Dockerfile.web: strict `--frozen-lockfile`; pnpm version via `packageManager` (Corepack).
- Dependabot config: pip + npm + github-actions + docker, weekly, grouped minor/patch.

## Security

- `SECURITY.md` (private vuln reporting path, scope, no public issues).
- CodeQL (python + javascript-typescript, security-and-quality).
- `scripts/check_public_hygiene.py` in CI: personal paths, tracked secrets, key patterns, oversized blobs, hardcoded version UAs.
- Ruleset on `main`: no force-push, no deletion, linear history. No reviewer requirement (solo maintainer).
- Wiki/projects disabled; delete-head-branches on; private vuln reporting enabled.

## Community / presentation

- `CONTRIBUTING.md` (hard rules: no evidence-free assertion, closed taxonomies, no historical substitution, access-policy binding).
- Issue templates (bug: version/ISIN/as_of/provider-mode + no-confidential-data warning; feature: operational question + public-source requirement).
- PR template checklist mirrors the release gates.
- `CITATION.cff` (v0.2.0, MIT, no invented DOI).
- README: 4 badges, live-demo line, real Playwright screenshot of `IE00B4L5Y983?as_of=2026-09-19` showing `[not yet effective]` settlement locations vs `outside_coverage` collateral.
- `pyproject.toml`: author + `[project.urls]` (Homepage/Repository/Issues/Documentation/Changelog).

## Release engineering

- `.github/workflows/release.yml` on `v*` tags: tag==package-version gate → full check suite → `uv build` + `twine check` → SHA256SUMS + SPDX SBOM (anchore/sbom-action) + `attest-build-provenance` → GHCR images `api`/`web` tagged `vX.Y.Z` + `vX.Y` with OCI labels.
- `test_version.py` invariants: `__version__` == installed metadata == FastAPI version; UA carries version; no literal UA in `src/`; web package.json carries no version.

## Remaining intentional limitations

- Release workflow not yet exercised end-to-end (fires on next tag).
- PR #2 (node 26-alpine build image) left to its own CI run — a build-stage-only change.
- No PyPI publish, no CODE_OF_CONDUCT, no CHANGELOG.md — Releases + `docs/release/` are the single history.
- Deploy to `passport.h1756.es` still pending — compose verified locally, homepage metadata already set.
