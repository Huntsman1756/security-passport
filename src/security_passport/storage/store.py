"""Generation read store — the PassportStore implementation over
a published generation directory.

Layout::

    generation-NNNN/
      manifest.json
      stores/
        meta.json              per-source retrieval metadata
        ecb_assets.parquet     normalized ECB rows (all ISINs)
        mic.parquet            MIC registry slice
        sss.json               eligible SSSs + links + stamps
        priii/<ISIN>.json      observed document-family graphs
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb

from security_passport.providers.base import (
    EcbAssetFact,
    MicFact,
    PriiiDocument,
    PriiiFacts,
    SssFact,
    SssLinkFact,
)


class GenerationStore:
    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._stores = self._root / "stores"
        self._meta: dict[str, Any] = {}
        mp = self._stores / "meta.json"
        if mp.exists():
            self._meta = json.loads(mp.read_text(encoding="utf-8"))
        self._sss: dict[str, Any] = {}
        sp = self._stores / "sss.json"
        if sp.exists():
            self._sss = json.loads(sp.read_text(encoding="utf-8"))

    def generation(self) -> str:
        return self._root.name

    # ---- ECB eligible assets -------------------------------------------

    def _ecb_path(self) -> Path:
        return self._stores / "ecb_assets.parquet"

    def ecb_asset(self, isin: str) -> EcbAssetFact | None:
        p = self._ecb_path()
        if not p.exists():
            return None
        con = duckdb.connect()
        try:
            rows = con.execute(
                f"SELECT * FROM '{p.as_posix()}' WHERE isin = $1",
                [isin]).fetchall()
            cols = [d[0] for d in con.description]
        finally:
            con.close()
        if not rows:
            return None
        r = dict(zip(cols, rows[0], strict=True))
        return EcbAssetFact(
            isin=r["isin"],
            haircut_category=r.get("haircut_category") or "",
            asset_type=r.get("asset_type") or "",
            reference_market=r.get("reference_market") or "",
            denomination_currency=(
                r.get("denomination_currency") or ""),
            issuance_date=r.get("issuance_date") or "",
            maturity_date=r.get("maturity_date") or "",
            issuer_csd=r.get("issuer_csd") or "",
            coupon_rate=r.get("coupon_rate") or "",
            issuer_name=r.get("issuer_name") or "",
            issuer_residence=r.get("issuer_residence") or "",
            issuer_group=r.get("issuer_group") or "",
            guarantor_name=r.get("guarantor_name") or "",
            guarantor_residence=(r.get("guarantor_residence") or ""),
            guarantor_group=r.get("guarantor_group") or "",
            coupon_definition=r.get("coupon_definition") or "",
            haircut=r.get("haircut") or "",
            haircut_own_use=r.get("haircut_own_use") or "",
            covered_bond_flag=r.get("covered_bond_flag") or "",
            climate_factor=r.get("climate_factor") or "",
            snapshot=r.get("snapshot") or "",
            retrieved_at=r.get("retrieved_at") or "")

    def ecb_snapshot(self) -> str:
        return str((self._meta.get("ecb_eligible_assets") or {})
                   .get("snapshot") or "")

    def ecb_retrieved_at(self) -> str:
        return str((self._meta.get("ecb_eligible_assets") or {})
                   .get("retrieved_at") or "")

    # ---- PRIII -----------------------------------------------------------

    def priii(self, isin: str) -> PriiiFacts | None:
        p = self._stores / "priii" / f"{isin}.json"
        if not p.exists():
            return None
        d = json.loads(p.read_text(encoding="utf-8"))
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
            isin=isin, searched=True,
            documents=tuple(docs),
            observed_at=str(d.get("observed_at") or ""),
            artifact_id=str(d.get("sha256") or ""))

    # ---- ECB SSS / links ------------------------------------------------

    def eligible_sss(self) -> list[SssFact]:
        stamp = str(self._sss.get("sss_page_stamp") or "")
        obs = str(self._sss.get("observed_at") or "")
        return [SssFact(sss_id=str(s.get("name") or ""),
                        name=str(s.get("name") or ""),
                        country=str(s.get("country") or ""),
                        observed_at=obs, page_stamp=stamp)
                for s in self._sss.get("sss") or []]

    def eligible_links(self) -> list[SssLinkFact]:
        stamp = str(self._sss.get("links_page_stamp") or "")
        obs = str(self._sss.get("observed_at") or "")
        return [SssLinkFact(
            investor_sss=str(l.get("investor_sss") or ""),
            issuer_sss=str(l.get("issuer_sss") or ""),
            intermediaries=tuple(l.get("intermediaries") or ()),
            operated_by=str(l.get("operated_by") or ""),
            observed_at=obs, page_stamp=stamp)
            for l in self._sss.get("links") or []]

    # ---- MIC ---------------------------------------------------------------

    def mic(self, mic: str) -> MicFact | None:
        p = self._stores / "mic.parquet"
        if not p.exists():
            return None
        con = duckdb.connect()
        try:
            rows = con.execute(
                f"SELECT * FROM '{p.as_posix()}' WHERE mic = $1",
                [mic]).fetchall()
            cols = [d[0] for d in con.description]
        finally:
            con.close()
        if not rows:
            return None
        r = dict(zip(cols, rows[0], strict=True))
        return MicFact(
            mic=r["mic"], market_name=r.get("market_name") or "",
            operating_mic=r.get("operating_mic") or "",
            oprt_sgmt=r.get("oprt_sgmt") or "",
            country=r.get("country") or "",
            status=r.get("status") or "")

    def meta(self) -> dict[str, Any]:
        return self._meta
