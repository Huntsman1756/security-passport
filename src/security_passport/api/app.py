"""Security Passport REST API — read-only, schema_version 1.

Endpoints:
    GET /api/v1/passports/{isin}
    GET /api/v1/passports/{isin}/evidence
    GET /api/v1/passports/{isin}/sources
    GET /api/v1/search?q=
    GET /api/v1/status
    GET /health/live   /health/ready

One request = one pinned (passport generation, upstream
generation) pair. Partial passports are 200s with per-block
not_found — a fallen source never fabricates.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from security_passport import __version__
from security_passport.config import Settings, load
from security_passport.domain.isin import checksum_ok, normalize
from security_passport.providers.base import (
    InstrumentProvider,
    PassportStore,
    ProviderError,
)
from security_passport.providers.fixtures import (
    FixtureInstrumentProvider,
    FixturePassportStore,
)
from security_passport.services.passport_builder import PassportBuilder
from security_passport.storage import generations
from security_passport.storage.store import GenerationStore

ERROR = "error"


def _err(code: str, message: str, status: int,
         details: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={ERROR: {"code": code, "message": message,
                         "details": details,
                         "request_id": uuid.uuid4().hex[:12]}})


class _State:
    """Process state — provider + pinned generation store."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider: InstrumentProvider | None = None
        self.store: PassportStore | None = None
        self.provider_error: str = ""
        self.store_error: str = ""
        self.started = time.time()

    def reload(self) -> None:
        s = self.settings
        self.provider_error = self.store_error = ""
        try:
            if s.provider == "openinstrument_api":
                from security_passport.providers.openinstrument.api import (
                    OpenInstrumentApiProvider,
                )
                self.provider = OpenInstrumentApiProvider(
                    s.openinstrument_url)
                self.provider.generation()  # probe now
            else:
                self.provider = FixtureInstrumentProvider(
                    s.fixtures_dir)
        except Exception as e:
            self.provider_error = f"{type(e).__name__}: {e}"
            self.provider = None
        try:
            if s.provider == "openinstrument_api":
                gen = generations.current(s.data_root / "read")
                if gen is None:
                    raise FileNotFoundError(
                        "no published generation — run "
                        "`security-passport update`")
                self.store = GenerationStore(gen)
            else:
                self.store = FixturePassportStore(s.fixtures_dir)
        except Exception as e:
            self.store_error = f"{type(e).__name__}: {e}"
            self.store = None


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load()
    state = _State(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
        state.reload()
        yield

    app = FastAPI(
        title="Security Passport",
        version=__version__,
        description="Evidence-backed operational passport for "
                    "European financial instruments.",
        lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET"],
        allow_headers=["*"])

    def _deps() -> _State:
        return state

    @app.middleware("http")
    async def security_headers(request: Request,
                               call_next: Any) -> Any:
        resp = await call_next(request)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = \
            "strict-origin-when-cross-origin"
        return resp

    # ------------------------------------------------------------------

    @app.get("/api/v1/status")
    def status(st: _State = Depends(_deps)) -> dict[str, Any]:
        return {
            "service": "security-passport",
            "version": __version__,
            "schema_version": "1",
            "provider_mode": settings.provider,
            "openinstrument_generation": (
                st.provider.generation()
                if st.provider else None),
            "generation": (
                st.store.generation() if st.store else None),
            "provider_error": st.provider_error or None,
            "store_error": st.store_error or None,
            "attribution": (
                "Security Passport transforms and combines public "
                "source information; not endorsed by ESMA, ECB, "
                "GLEIF, ISO/SWIFT, or BME/Iberclear."),
            "sources": "/api/v1/status#sources or /sources",
        }

    @app.get("/api/v1/passports/{isin}")
    def passport(isin: str,
                 st: _State = Depends(_deps)) -> JSONResponse:
        isin_n = normalize(isin)
        if not checksum_ok(isin_n):
            return _err("INVALID_ISIN",
                        f"'{isin}' is not a valid ISIN "
                        "(structure or check digit failed).", 422)
        if st.provider is None:
            return _err("SOURCE_UNAVAILABLE",
                        st.provider_error or "provider not ready",
                        503)
        if st.store is None:
            return _err("DATASET_NOT_READY",
                        st.store_error or "no generation", 503)
        builder = PassportBuilder(st.provider, st.store)
        try:
            p = builder.build(isin_n, checksum_ok=True)
        except ProviderError as e:
            return _err("SOURCE_UNAVAILABLE", str(e), 503)
        body = json.dumps(p.to_dict(), ensure_ascii=False)
        etag = hashlib.sha256(
            f"{p.generation}:{p.openinstrument_generation}:"
            f"{isin_n}:1".encode()).hexdigest()[:16]
        resp = JSONResponse(content=json.loads(body))
        resp.headers["ETag"] = f'"{etag}"'
        resp.headers["Cache-Control"] = "public, max-age=60"
        return resp

    @app.get("/api/v1/passports/{isin}/evidence")
    def passport_evidence(isin: str,
                          st: _State = Depends(
                              _deps)) -> JSONResponse:
        isin_n = normalize(isin)
        if not checksum_ok(isin_n):
            return _err("INVALID_ISIN",
                        f"'{isin}' is not a valid ISIN.", 422)
        if st.provider is None or st.store is None:
            return _err("SOURCE_UNAVAILABLE",
                        st.provider_error or st.store_error, 503)
        p = PassportBuilder(st.provider, st.store).build(
            isin_n, checksum_ok=True)
        evs = []
        for block in p.blocks():
            for f in block.all_fields():
                for e in f.evidence:
                    evs.append({"block": block.name,
                                "field": f.name,
                                **e.to_dict()})
        return JSONResponse(content={
            "isin": isin_n, "generation": p.generation,
            "evidence": evs})

    @app.get("/api/v1/passports/{isin}/sources")
    def passport_sources(isin: str,
                         st: _State = Depends(
                             _deps)) -> JSONResponse:
        isin_n = normalize(isin)
        if not checksum_ok(isin_n):
            return _err("INVALID_ISIN",
                        f"'{isin}' is not a valid ISIN.", 422)
        if st.provider is None or st.store is None:
            return _err("SOURCE_UNAVAILABLE",
                        st.provider_error or st.store_error, 503)
        p = PassportBuilder(st.provider, st.store).build(
            isin_n, checksum_ok=True)
        return JSONResponse(content={
            "isin": isin_n,
            "source_summary": p.source_summary,
            "searched_sources": sorted(
                {s for b in p.blocks()
                 for f in b.all_fields()
                 for s in f.searched_sources})})

    @app.get("/api/v1/search")
    def search(q: str = Query(...),
               st: _State = Depends(_deps)) -> JSONResponse:
        if st.provider is None:
            return _err("SOURCE_UNAVAILABLE",
                        st.provider_error or "provider not ready",
                        503)
        try:
            cands = st.provider.search(q)
        except ProviderError as e:
            return _err("SOURCE_UNAVAILABLE", str(e), 503)
        return JSONResponse(content={
            "query": q, "results": [c.__dict__ for c in cands],
            "note": "exact-identifier first; text returns "
                    "candidates only"})

    # ---- health ---------------------------------------------------------

    @app.get("/health/live", include_in_schema=False)
    def live() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/health/ready", include_in_schema=False)
    def ready(st: _State = Depends(_deps)) -> JSONResponse:
        checks = {
            "provider": st.provider is not None,
            "store": st.store is not None,
        }
        # real readiness: the store actually answers a lookup
        if st.store is not None:
            try:
                st.store.ecb_snapshot()
            except Exception:
                checks["store"] = False
        ok = all(checks.values())
        return JSONResponse(
            {"status": "ready" if ok else "degraded",
             "checks": checks},
            status_code=200 if ok else 503)

    return app


app = create_app()
