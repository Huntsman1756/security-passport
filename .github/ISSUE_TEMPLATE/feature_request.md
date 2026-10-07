---
name: Feature request
about: Propose a capability the passport should add
labels: enhancement
---

## Operational question

What concrete question should the passport answer that it
currently cannot? State it in the form a user would ask, e.g.

> "Given this ISIN, what evidence exists that X?"

## Authoritative public source

Which public source(s) would carry the answer? Confirm the
access classification:

- [ ] publicly machine-readable (bulk or API)
- [ ] public human lookup only
- [ ] requires authentication / premium — **cannot be silently
      scraped; state the access boundary explicitly**

## Why existing blocks cannot answer it

Which of `identity` / `primary_market` / `secondary_market` /
`post_trade` / `eurosystem_collateral` should carry it, and why
can't the current evidence chain produce it?

## Proposed evidence semantics

What would `reported` / `derived` / `inferred` look like here —
and what are the failure / `not_found` / `conflict` states?
