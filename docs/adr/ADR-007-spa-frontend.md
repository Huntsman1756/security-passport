# ADR-007 — SPA frontend behind Caddy, no SSR

**Status:** accepted (v0.1.0)

## Decision

React + TypeScript + Vite + Tailwind + TanStack Query SPA, served
as static assets. Caddy terminates TLS, proxies `/api/*` to
FastAPI, and falls back to `index.html` for client routes.

## Rationale

- The product is read-only lookup; there is no server-rendered
  state worth paying an SSR stack for.
- One small VPS (4 vCPU / 8 GB) runs: Caddy, FastAPI, static
  files, mounted read-only generation. No Node runtime in prod.
- Dark mode, density, and provenance UX are CSS/component work,
  not framework work.

## Consequences

- Public surface is `/` (home), `/isin/{ISIN}` (passport),
  `/sources`. SEO is a non-goal for v0.1.0.
