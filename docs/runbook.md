# Runbooks

## Deployment (single VPS)

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
