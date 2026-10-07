"""VenueContextProvider — the port for OpenVenue context.

OpenVenue (``openbloomb``) owns venue/operator/rulebook semantics:
operating MIC vs segment MIC, venue registry, market-category,
rulebook publications. Security Passport deliberately does NOT
reimplement that layer — this port exists so the builder can
consume it when a live service is configured, and degrade to
``not_found`` when it is not.

Status (v0.1.1): the fixture provider ships; the live provider is
a thin HTTP adapter over ``GET /venues/{mic}`` +
``GET /instruments/{id}/operational-dossier`` — wired once a
pinned OpenVenue data bundle is available to the deployment.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class VenueContext:
    """Venue facts the passport may surface (secondary_market)."""
    mic: str
    operating_mic: str
    segment_mic: str
    market_name: str
    operator: str
    market_category: str
    country: str
    rulebook_ref: str = ""
    rulebook_version: str = ""
    observed_at: str = ""


class VenueContextProvider(Protocol):
    """Read surface; absence of an upstream never fails the
    passport — it degrades the venue-context fields to
    ``not_found`` with the search declared."""

    def venue(self, mic: str) -> VenueContext | None: ...
    def instrument_dossier(self, isin: str) -> dict[str, Any]: ...


class FixtureVenueProvider:
    """Corpus-backed — ``corpus/venues/{MIC}.json`` +
    ``corpus/venues/{ISIN}.dossier.json``."""

    def __init__(self, corpus_dir: str | Path) -> None:
        self._dir = Path(corpus_dir) / "venues"

    def venue(self, mic: str) -> VenueContext | None:
        p = self._dir / f"{mic}.json"
        if not p.exists():
            return None
        d = json.loads(p.read_text(encoding="utf-8"))
        return VenueContext(
            mic=mic,
            operating_mic=d.get("operating_mic", ""),
            segment_mic=d.get("segment_mic", ""),
            market_name=d.get("market_name", ""),
            operator=d.get("operator", ""),
            market_category=d.get("market_category", ""),
            country=d.get("country", ""),
            rulebook_ref=d.get("rulebook_ref", ""),
            rulebook_version=d.get("rulebook_version", ""),
            observed_at=d.get("observed_at", ""))

    def instrument_dossier(self, isin: str) -> dict[str, Any]:
        p = self._dir / f"{isin}.dossier.json"
        if p.exists():
            body: dict[str, Any] = json.loads(
                p.read_text(encoding="utf-8"))
            return body
        return {}


class OpenVenueProvider:
    """Live adapter over a configured OpenVenue service.
    Requires ``openbloomb`` ≥ the operational-dossier endpoint;
    absence of the service degrades to ``None`` — callers treat
    that as ``not_found``, never as an invented venue."""

    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        import httpx
        self._c = httpx.Client(base_url=base_url.rstrip("/"),
                               timeout=timeout)

    def venue(self, mic: str) -> VenueContext | None:
        try:
            r = self._c.get(f"/venues/{mic}")
            if r.status_code != 200:
                return None
            d = r.json()
        except Exception:
            return None
        return VenueContext(
            mic=mic,
            operating_mic=d.get("operating_mic", ""),
            segment_mic=d.get("segment_mic", mic),
            market_name=d.get("name", ""),
            operator=d.get("operator", ""),
            market_category=d.get("market_category", ""),
            country=d.get("country", ""),
            rulebook_ref=d.get("rulebook_ref", ""),
            observed_at=d.get("observed_at", ""))

    def instrument_dossier(self, isin: str) -> dict[str, Any]:
        try:
            r = self._c.get(
                f"/instruments/{isin}/operational-dossier")
            return r.json() if r.status_code == 200 else {}
        except Exception:
            return {}
