"""Fixture provider — replay captured payloads.

``FixtureInstrumentProvider`` answers InstrumentProvider calls from
``tests/fixtures/corpus/openinstrument/*.json`` through the same
mapping code as the live API provider, so fixtures exercise real
contract handling — including the recorded ``/v1/evidence`` 503.

``FixturePassportStore`` serves own-source facts by running the
real adapters over the captured raw payloads (ECB UTF-16 TSV,
PRIII Solr responses, ECB HTML pages, MIC CSV) — the fixture path
exercises the real parsers, not canned outputs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from security_passport.providers import (
    ecb_assets,
    ecb_sss,
    esma_prospectus,
    mic,
)
from security_passport.providers.base import (
    EcbAssetFact,
    MicFact,
    PassportStore,
    PriiiDocument,
    PriiiFacts,
    ProviderError,
    SssFact,
    SssLinkFact,
)
from security_passport.providers.openinstrument.api import (
    OpenInstrumentApiProvider,
)

PROVIDER = "fixtures"


class FixtureInstrumentProvider(OpenInstrumentApiProvider):
    """InstrumentProvider over recorded API payloads."""

    def __init__(self, corpus_dir: Path | str) -> None:
        # no httpx client — _get is overridden
        self._dir = Path(corpus_dir) / "openinstrument"
        self._generation = ""
        self._cache: dict[str, dict[str, Any]] = {}

    def _load(self, isin: str, name: str) -> dict[str, Any]:
        key = f"{isin}.{name}"
        if key not in self._cache:
            p = self._dir / f"{key}.json"
            if not p.exists():
                self._cache[key] = {"found": False}
            else:
                self._cache[key] = json.loads(
                    p.read_text(encoding="utf-8"))
        return self._cache[key]

    def _get(self, path: str, **params: Any) -> dict[str, Any]:
        if path == "/v1/status":
            return json.loads(
                (self._dir / "status.json").read_text(
                    encoding="utf-8"))
        if path == "/v1/search":
            q = (params.get("q") or "").strip().upper()
            results = []
            for p in sorted(self._dir.glob("*.instrument.json")):
                d = json.loads(p.read_text(encoding="utf-8"))
                if d.get("found"):
                    nm = (d.get("full_name") or d.get("fisn") or "")
                    if (p.name.split(".")[0] == q
                            or q in str(nm).upper()):
                        results.append({
                            "isin": d["isin"],
                            "full_name": d.get("full_name"),
                            "cfi": d.get("cfi")})
            kind = ("exact_isin" if len(q) == 12
                    else "text_candidates")
            return {"query": q, "kind": kind, "results": results}
        parts = path.split("/")
        isin = parts[3] if len(parts) > 3 else ""
        if path.startswith("/v2/"):
            name = "v2"
        elif len(parts) > 4:
            name = parts[4]
        else:
            name = "instrument"
        d = self._load(isin, name)
        if "_capture_error" in d:
            raise ProviderError(
                "openinstrument",
                f"recorded contract failure: {d['_capture_error']}")
        return d

    def generation(self) -> str:
        st = self._get("/v1/status")
        return str(st.get("generation") or "fixture-generation")


class FixturePassportStore:
    """PassportStore over the raw fixture corpus — real parsers."""

    def __init__(self, corpus_dir: Path | str) -> None:
        self._dir = Path(corpus_dir)
        ecb_csv = (self._dir / "ecb_assets" / "ea_slice.csv"
                   ).read_bytes()
        self._ecb_rows = {
            r["isin"]: r for r in (
                ecb_assets.normalize(
                    row, snapshot="261006", retrieved_at="")
                for row in ecb_assets.parse(ecb_csv))}
        sss_html = (self._dir / "ecb_sss" / "sss_page.html"
                    ).read_text(encoding="utf-8")
        links_html = (self._dir / "ecb_sss" / "links_page.html"
                      ).read_text(encoding="utf-8")
        self._sss = ecb_sss.parse_pages(sss_html, links_html)
        mic_csv = mic.decode_csv(
            (self._dir / "mic" / "mic_slice.csv").read_bytes())
        self._mic = mic.parse(mic_csv)

    def generation(self) -> str:
        return "fixture-0001"

    # ---- ECB -------------------------------------------------------------

    def ecb_asset(self, isin: str) -> EcbAssetFact | None:
        r = self._ecb_rows.get(isin)
        if r is None:
            return None
        return EcbAssetFact(**r)

    def ecb_snapshot(self) -> str:
        return "261006"

    def ecb_retrieved_at(self) -> str:
        return "2026-10-07"

    # ---- PRIII -------------------------------------------------------------

    def priii(self, isin: str) -> PriiiFacts | None:
        p = self._dir / "priii" / f"{isin}.json"
        if not p.exists():
            return None
        raw = json.loads(p.read_text(encoding="utf-8"))
        d = esma_prospectus.normalize_raw(raw)
        docs: list[PriiiDocument] = []
        for fl in d.get("filings") or []:
            docs.append(PriiiDocument(
                root_id=str(fl.get("root") or ""),
                document_type=str(fl.get("document_type") or ""),
                document_type_descr=str(
                    fl.get("document_type_descr") or ""),
                prospectus_type=str(fl.get("prospectus_type") or ""),
                structure_type=str(fl.get("structure_type") or ""),
                national_document_id=str(
                    fl.get("national_document_id") or ""),
                home_member_state=str(
                    fl.get("home_member_state") or ""),
                home_member_state_code=str(
                    fl.get("home_member_state_code") or ""),
                member_states=tuple(fl.get("member_states") or ()),
                is_passported=bool(fl.get("is_passported")),
                approval_filing_date=str(
                    fl.get("approval_filing_date") or ""),
                first_passporting_date=str(
                    fl.get("first_passporting_date") or ""),
                last_passporting_date=str(
                    fl.get("last_passporting_date") or ""),
                doc_last_update_date=str(
                    fl.get("doc_last_update_date") or ""),
                document_rfss_id=str(
                    fl.get("document_rfss_id") or ""),
                download_url=str(fl.get("download_url") or ""),
                party_name=str(fl.get("party_name") or ""),
                issuer_lei=str(fl.get("issuer_lei") or ""),
                issuer_name=str(fl.get("issuer_name") or ""),
                offeror_lei=str(fl.get("offeror_lei") or ""),
                offeror_name=str(fl.get("offeror_name") or ""),
                related_document_ids=tuple(
                    fl.get("related_document_ids") or ()),
                document_languages=str(
                    fl.get("document_languages") or ""),
                ifii_doc_type=str(fl.get("ifii_doc_type") or ""),
                ifii_mat_exp_date=str(
                    fl.get("ifii_mat_exp_date") or ""),
                ifii_securities_type=str(
                    fl.get("ifii_securities_type") or ""),
                ifii_trading_venue=str(
                    fl.get("ifii_trading_venue") or "")))
        return PriiiFacts(
            isin=isin, searched=True, documents=tuple(docs),
            observed_at="2026-10-07",
            artifact_id=hashlib.sha256(
                p.read_bytes()).hexdigest())

    # ---- SSS / links -------------------------------------------------------

    def eligible_sss(self) -> list[SssFact]:
        return [SssFact(sss_id=s["name"], name=s["name"],
                        country=s["country"],
                        observed_at="2026-10-07",
                        page_stamp=self._sss["sss_page_stamp"])
                for s in self._sss["sss"]]

    def eligible_links(self) -> list[SssLinkFact]:
        return [SssLinkFact(
            investor_sss=l["investor_sss"],
            issuer_sss=l["issuer_sss"],
            intermediaries=tuple(l["intermediaries"]),
            operated_by=l["operated_by"],
            observed_at="2026-10-07",
            page_stamp=self._sss["links_page_stamp"])
            for l in self._sss["links"]]

    # ---- MIC -----------------------------------------------------------------

    def mic(self, code: str) -> MicFact | None:
        r = self._mic.get(code)
        if r is None:
            return None
        return MicFact(mic=r.mic, market_name=r.market_name,
                       operating_mic=r.operating_mic,
                       oprt_sgmt=r.oprt_sgmt, country=r.country,
                       status=r.status)

    def meta(self) -> dict[str, Any]:
        return {"mode": "fixtures"}
