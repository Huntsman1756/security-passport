# Security Policy

## Supported versions

| version | supported |
|---|---|
| `v0.2.x` (latest release) | yes — security fixes land on `main` |
| earlier `0.x` | no — upgrade to the latest tag |

## Reporting a vulnerability

Report privately via **GitHub Private Vulnerability Reporting**
(security advisories on this repository) or via the repository
owner's profile contact. Do **not** open a public issue.

Include:

- affected component (API, web, CLI, Docker/deployment, a parser)
- version / tag / commit
- reproduction or a concrete description of the impact
- whether the issue involves data handling, network access, or
  the container boundary

## Scope

**In scope:** the FastAPI surface, the SPA, the Docker/compose
deployment, parsers and providers that fetch remote content, the
artifact store, secrets handling, and any code path that could
expose non-public data or allow injection through crafted source
content.

**Out of scope:** correctness of upstream public datasets
themselves (ESMA, ECB, ISO, Euronext, CNMV). However, a bug where
Security Passport *mishandles* upstream content — e.g. silently
turning malformed input into a confident assertion — **is** in
scope: that is a data-integrity defect, not an upstream problem.

## Response policy

Acknowledgement is best-effort within a reasonable window; there
is no commercial SLA. Verified fixes are released with a note in
the GitHub Release.
