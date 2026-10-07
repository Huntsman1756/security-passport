# CLI

```bash
security-passport DE000A3LJCB4                # human passport
security-passport DE000A3LJCB4 --json         # contract JSON
security-passport DE000A3LJCB4 --sources      # searched sources
security-passport DE000A3LJCB4 --explain issuer_lei
security-passport DE000A3LJCB4 --explain post-trade

security-passport update                      # ingest → publish
security-passport update --priii-isin DE000A3LJCB4
security-passport validate                    # golden release gate
security-passport status                      # generation state
security-passport doctor                      # env check
```

## `--explain`

Deterministic field/block explanation — no LLM:

```
FIELD identity.issuer_lei
  value:   894500SN5GTABFSFWS54
  status:  reported
  rule:    issuer_lei_adjudication.v1
  limits:  FIRDS field 5 is 'issuer or operator of the trading
           venue' — the role qualifier is carried, not relabelled.
  evidence: openinstrument/firds_projection rec=DE000A3LJCB4 …
```

Accepts a field (`identity.issuer_lei`, `eurosystem_collateral.haircut`)
or a block name (`post-trade`, `primary_market`).

## Exit codes

`0` ok · `2` invalid ISIN or bad usage · `3` source unavailable ·
`1` validation/update failure.

## Modes

`SECURITY_PASSPORT_PROVIDER=openinstrument_api` (default for
production) or `fixtures` (replays `tests/fixtures/corpus` —
offline, deterministic).
