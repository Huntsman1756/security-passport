# Runbooks

## Public demo — passport.h1756.es

The public instance runs in **fixture mode**: the API replays
`tests/fixtures/corpus` (28 instruments) through the production
parsers. It has no upstream dependency, no timer and no writable
state, so it needs no routine maintenance.

Layout on the H1756 VPS (Coolify Traefik routes by label; no host
ports published):

| path | content |
|---|---|
| `/opt/security-passport` | git checkout at the deployed commit |
| `/data/security-passport/corpus` | read-only copy of `tests/fixtures/corpus` |

```bash
# deploy / upgrade (on the VPS)
cd /opt/security-passport && sudo git fetch && sudo git checkout <commit-or-tag>
sudo rsync -a --delete tests/fixtures/corpus/ /data/security-passport/corpus/
sudo SP_VERSION=$(git rev-parse --short HEAD)   docker compose -f infra/h1756/compose.yml up -d --build
curl -fsS https://passport.h1756.es/health/ready
```

Rollback: `git checkout <previous>` and repeat the `up -d --build`.
Compose file: `infra/h1756/compose.yml` (limits: API 512 MB /
0.5 CPU, web 128 MB / 0.25 CPU). The VPS operations log lives in
the private `h1756-vps-ops` repo (`baseline/CAMBIOS.md`).

## Deployment (single VPS, full mode)

```bash
docker compose up -d --build
# env: PUBLIC_BASE_URL=passport.h1756.es
#      OPENINSTRUMENT_URL=http://<oi-service>:8000
#      DATA_ROOT=/srv/security-passport/data
#      OPENVENUE_URL= optional — rulebook context
```

Caddy terminates TLS and proxies `/api/*` + `/health/*` to the
API container; the SPA is served with history-fallback. The API
publishes no port — the web edge is the only public surface.
`security-passport update` runs via
`infra/systemd/security-passport-update.timer`.

## Daily update (production)

```bash
security-passport update
```

Stages into `data/staging/`, writes `data/read/generation-XXXX`,
then swaps `CURRENT`. Non-blocking on upstream: upstream
generation is probed, not required. Failures abort before the
swap — `CURRENT` never points at a partial generation.

Timer: `infra/systemd/security-passport-update.timer` (daily
05:30 UTC ± 15min jitter, `flock` deduped).

**Verify**

```bash
security-passport status        # generation + provider metadata
security-passport doctor        # provider/store reachability
curl -s localhost:8000/health/ready
```

## Rollback

```bash
security-passport status                    # identify generations
ls data/read/                               # available targets
# repoint CURRENT atomically:
python -c "from security_passport.storage.generations import rollback; \
           rollback(__import__('pathlib').Path('data/read'), 'generation-000N')"
systemctl restart security-passport-api     # repin on next request
```

Rollback is pointer-only — no data is rewritten. The staging dir
can be purged afterward.

## Source failure

| Symptom | Check | Action |
|---|---|---|
| `503 SOURCE_UNAVAILABLE` | `GET /api/v1/status` → `provider_error` | provider is a hard dependency for identity — fix upstream reachability; store-backed blocks still degrade per-field, not per-request |
| `503 DATASET_NOT_READY` | `ls data/read` — no generation | run `security-passport update` |
| ECB ingest failed | staging logs | `CURRENT` untouched; fields degrade to `not_found` with `searched_sources`; investigate CSV schema drift (`SchemaError`) |
| PRIII failed for one ISIN | `manifest.providers` | PRIII payload simply absent → primary-market `not_found` |
| Stale generation | `manifest.created_at` age | trigger update; `stale_source` flag marks derived data past source staleness window |

## Schema drift

Any adapter raising `SchemaError` aborts ingest. Do **not** patch
parsers reactively in prod — capture the new artifact into the
fixture corpus, adapt + bump `parser_version`, and add a contract
test. Parser version bumps change the semantic fingerprint and
make the drift auditable.

## Golden corpus drift

`security-passport validate` compares built passports against
`tests/fixtures/goldens.yaml`. A drift in a *correct* direction
(source fixed upstream, better evidence) requires updating the
golden with the change reason in the commit message. A drift
in the wrong direction blocks release — that is the point.
