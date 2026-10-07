# Golden corpus coverage — v0.1.1

Cases: 31 | generated from `tests/fixtures/goldens.yaml`

| ISIN | case | overall | reported | derived | conflict | not_found | n/a |
|---|---|---|---|---|---|---|---|
| DE000A3LJCB4 | debt_priii_full | found | 18 | 5 | 0 | 8 | 0 |
| XS2081615473 | ecb_eligible_emtn | found | 26 | 5 | 0 | 6 | 0 |
| ES0000101966 | iberlear_evidence | found | 27 | 5 | 0 | 5 | 0 |
| ES0113900J37 | spanish_equity_no_inference | found | 13 | 5 | 0 | 11 | 1 |
| DE0007164600 | equity_no_maturity | found | 17 | 5 | 0 | 8 | 1 |
| IE0007SRI1C7 | issuer_lei_conflict | found | 12 | 5 | 1 | 11 | 1 |
| LU0003549028 | lu_fund | found | 12 | 5 | 0 | 12 | 1 |
| XSSE2WKP7HV5 | unknown_valid_isin | unknown | 3 | 2 | 0 | 24 | 0 |
| DE000A3LJCB0 | invalid_checksum | api_error | 0 | 0 | 0 | 0 | 0 |
| FR0013154002 | fr_equity | found | 13 | 5 | 0 | 11 | 1 |
| FR0000120271 | fr_large_equity_multivenue | found | 13 | 5 | 0 | 11 | 1 |
| IT0004729759 | it_equity | found | 12 | 5 | 0 | 12 | 1 |
| NL0000235190 | nl_equity_with_priii | found | 18 | 5 | 0 | 7 | 1 |
| ES0113211835 | es_equity_large | found | 13 | 5 | 0 | 11 | 1 |
| IE00B4L5Y983 | etf_share_class | found | 14 | 5 | 0 | 10 | 1 |
| IE00BYYJHC15 | ucits_share_class | found | 12 | 5 | 0 | 12 | 1 |
| ES0155092036 | es_sicav | found | 12 | 5 | 0 | 12 | 1 |
| IT0005282527 | it_sovereign_btp | found | 13 | 5 | 0 | 12 | 0 |
| ES0000012E44 | es_sovereign_iberclear | found | 26 | 5 | 0 | 5 | 0 |
| IT0005678443 | it_bank_bond_clit01 | found | 30 | 5 | 0 | 3 | 0 |
| FR0129714681 | ecb_only_no_canonical | unknown | 16 | 2 | 0 | 18 | 0 |
| DE000A2GSP56 | covered_bond_de | found | 26 | 5 | 0 | 6 | 0 |
| XS2525255647 | covered_bond_xs_priii | found | 30 | 5 | 0 | 3 | 0 |
| IT0024182286 | option_lei_conflict | found | 11 | 5 | 1 | 13 | 0 |
| AT0000A1NZ16 | fully_delisted | found | 17 | 5 | 0 | 9 | 0 |
| DE0005874846 | firds_sentinel_9999 | found | 12 | 5 | 0 | 12 | 1 |
| DE0001150548 | de_rights_instrument | found | 13 | 5 | 0 | 11 | 1 |
| FR001400YGG3 | fr_debt_convertible | found | 12 | 5 | 0 | 13 | 0 |
| DE000DN48XD7 | priii_only_no_canonical | unknown | 8 | 2 | 0 | 20 | 0 |
| XS0971721963 | ru_sovereign_absent | found | 12 | 5 | 0 | 13 | 0 |
| ES0105015012 | es_equity_small | found | 12 | 5 | 0 | 12 | 1 |

**Totals**: {'reported': 473, 'derived': 141, 'conflict': 2, 'not_found': 321, 'not_applicable': 15}

## Scenario coverage map

See the header comment in `goldens.yaml` for scenario → ISIN mapping.

## Deliberate gaps (not yet covered)

- supplement-chain PRIII families (all corpus filings are single-doc)

- LEI role non-conflict (manager≠issuer) — lands with the OpenFunds provider (v0.2)

- source-outage scenario — covered by ProviderError tests, not a golden

- historical corrected record — needs an as-of implementation (deferred)