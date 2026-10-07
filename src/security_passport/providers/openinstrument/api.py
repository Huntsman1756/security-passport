"""OpenInstrument REST provider — the only upstream dependency.

Consumes the frozen ``/v1`` and additive ``/v2`` contracts over
httpx. The upstream generation is resolved once per provider
instance so one passport build can never mix two upstream
snapshots (a mid-build CURRENT flip would only affect the NEXT
build).
"""
from __future__ import annotations

from typing import Any

import httpx

from security_passport.providers.base import (
    IdentifierFact,
    InstrumentFacts,
    IssuerAssertionFact,
    IssuerFacts,
    ListingFact,
    ProviderError,
    SearchCandidate,
    UpstreamEvidence,
)

PROVIDER = "openinstrument"


class OpenInstrumentApiProvider:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self._base = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base, timeout=timeout,
            headers={"User-Agent":
                     "security-passport/0.1.0"})
        self._generation = ""

    def name(self) -> str:
        return PROVIDER

    def _get(self, path: str, **params: Any) -> dict[str, Any]:
        try:
            r = self._client.get(path, params=params or None)
        except httpx.HTTPError as e:
            raise ProviderError(
                PROVIDER, f"{path}: {type(e).__name__} {e}",
                cause=e) from e
        if r.status_code == 404:
            return {"found": False}
        if r.status_code >= 400:
            raise ProviderError(
                PROVIDER,
                f"{path}: HTTP {r.status_code}")
        try:
            out = r.json()
        except ValueError as e:
            raise ProviderError(
                PROVIDER, f"{path}: invalid JSON",
                code="INTERNAL_DATA_INTEGRITY_ERROR",
                cause=e) from e
        if not isinstance(out, dict):
            raise ProviderError(
                PROVIDER, f"{path}: non-object JSON",
                code="INTERNAL_DATA_INTEGRITY_ERROR")
        return out

    def generation(self) -> str:
        if not self._generation:
            try:
                ready = self._get("/health/ready")
                if ready.get("generation"):
                    self._generation = str(ready["generation"])
                    return self._generation
            except ProviderError:
                pass
            st = self._get("/v1/status")
            self._generation = str(st.get("generation") or "unknown")
        return self._generation

    # ---- frozen v1 contract -------------------------------------------

    def instrument(self, isin: str) -> InstrumentFacts:
        d = self._get(f"/v1/instruments/{isin}")
        if not d.get("found"):
            return InstrumentFacts(isin=isin, found=False)
        return InstrumentFacts(
            isin=isin, found=True,
            cfi=d.get("cfi"), cfi_state=d.get("cfi_state") or "",
            fisn=d.get("fisn"), fisn_state=d.get("fisn_state") or "",
            full_name=d.get("full_name"),
            full_name_state=d.get("full_name_state") or "",
            notional_currency=d.get("notional_currency"),
            notional_currency_state=(
                d.get("notional_currency_state") or ""),
            issuer_lei=d.get("issuer_lei"),
            issuer_lei_state=d.get("issuer_lei_state") or "",
            issuer_lei_assertions=int(
                d.get("issuer_lei_assertions") or 0),
            competent_authority=d.get("competent_authority"),
            competent_authority_state=(
                d.get("competent_authority_state") or ""),
            cfi_letter=d.get("cfi_letter") or "",
            firds_snapshot=d.get("firds_snapshot") or "",
            n_firds_records=int(d.get("n_firds_records") or 0))

    def listings(self, isin: str) -> list[ListingFact]:
        d = self._get(f"/v1/instruments/{isin}/listings")
        out: list[ListingFact] = []
        for r in d.get("listings") or []:
            if not isinstance(r, dict) or not r.get("venue_mic"):
                continue
            out.append(ListingFact(
                venue_mic=str(r["venue_mic"]),
                relevant_venue=str(r.get("relevant_venue") or ""),
                issuer_requested_admission=str(
                    r.get("issuer_requested_admission") or ""),
                admission_approval_date=r.get(
                    "admission_approval_date"),
                admission_request_date=r.get(
                    "admission_request_date"),
                first_trade_date=r.get("first_trade_date"),
                termination_date=r.get("termination_date"),
                locator=str(r.get("locator") or "")))
        return out

    def issuer(self, isin: str) -> IssuerFacts:
        d = self._get(f"/v1/instruments/{isin}/issuer")
        if not d.get("found"):
            return IssuerFacts(isin=isin, found=False)
        a = d.get("assertions") or {}

        def pack(rows: Any) -> tuple[IssuerAssertionFact, ...]:
            out = []
            for r in rows or []:
                if isinstance(r, dict) and r.get("lei"):
                    out.append(IssuerAssertionFact(
                        lei=str(r["lei"]),
                        locator=str(r.get("locator") or ""),
                        venue=str(r.get("venue") or "")))
                elif isinstance(r, dict) and r.get("issr"):
                    out.append(IssuerAssertionFact(
                        lei=str(r["issr"]),
                        locator=str(r.get("locator") or ""),
                        venue=str(r.get("venue") or "")))
            return tuple(out)

        return IssuerFacts(
            isin=isin, found=True,
            canonical_lei=d.get("canonical_lei"),
            state=d.get("state") or "",
            assertion_count=int(d.get("assertion_count") or 0),
            gleif_assertions=pack(a.get("gleif_isin_lei")),
            firds_assertions=pack(a.get("firds_field5")),
            entity=d.get("entity"))

    def identifiers(self, isin: str) -> list[IdentifierFact]:
        d = self._get(f"/v1/instruments/{isin}/identifiers")
        return [IdentifierFact(
            level=str(r.get("level") or ""),
            scheme=str(r.get("scheme") or ""),
            value=str(r.get("value") or ""),
            provider=str(r.get("provider") or ""))
            for r in d.get("identifiers") or []
            if isinstance(r, dict) and r.get("value")]

    def upstream_evidence(self, isin: str) -> UpstreamEvidence:
        d = self._get(f"/v1/instruments/{isin}/evidence")
        def rows(key: str) -> tuple[dict[str, str], ...]:
            return tuple(
                {k: str(v) for k, v in r.items()}
                for r in d.get(key) or [] if isinstance(r, dict))
        return UpstreamEvidence(
            firds=rows("firds_evidence"),
            gleif=rows("gleif_evidence"),
            other=rows("openfigi_evidence"))

    def fund_roles(self, isin: str) -> list[dict[str, str]]:
        """v2 fund roles — optional surface; absence is not an
        error (non-fund ISINs legitimately have none)."""
        try:
            d = self._get(f"/v2/instruments/{isin}")
        except ProviderError:
            return []
        out: list[dict[str, str]] = []
        for r in d.get("roles") or []:
            if isinstance(r, dict) and r.get("value"):
                out.append({"role": str(r.get("role") or ""),
                            "value": str(r["value"]),
                            "artifact":
                                str(r.get("source_artifact") or "")})
        return out

    def search(self, q: str) -> list[SearchCandidate]:
        d = self._get("/v1/search", q=q)
        kind = str(d.get("kind") or "")
        return [SearchCandidate(
            isin=str(r.get("isin") or ""),
            full_name=r.get("full_name"),
            cfi=r.get("cfi"), kind=kind)
            for r in d.get("results") or []
            if isinstance(r, dict) and r.get("isin")]

    def close(self) -> None:
        self._client.close()
