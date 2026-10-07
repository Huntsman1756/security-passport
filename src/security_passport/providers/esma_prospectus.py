"""ESMA PRIII prospectus register — document family graph.

Public Solr core ``esma_registers_priii_documents`` (documented
M2M surface). Parent docs carry filing metadata; children carry
instruments (``ifii_*``), issuers/offerors (``issuer_*`` /
``offeror_*``), related-document identifiers, passporting
countries, languages, disclosure regimes.

Query pattern: ``ifii_isin:"<ISIN>"`` → filing roots →
``_root_:"<id>" AND type_s:parent|child`` per filing. An ISIN can
appear under several filings (base prospectus + final terms +
supplements form one family via related-document identifiers).

This adapter never assumes an ISIN match alone makes a document
legally relevant: relations are preserved as a graph, not
flattened into "the prospectus".
"""
from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from typing import Any

PARSER = "security_passport.providers.esma_prospectus"
PARSER_VERSION = "1"
PROVIDER = "esma_priii"
DATASET = "priii_documents"

SOLR = ("https://registers.esma.europa.eu/solr/"
        "esma_registers_priii_documents/select")
_UA = {"User-Agent": "security-passport/0.1.0"}

RFSS_DOWNLOAD = ("https://registers.esma.europa.eu/publication/"
                 "downloadFile?fileId={fid}&checksum={cks}")


class SchemaError(Exception):
    """Unexpected Solr payload shape — fail closed."""


def _canon(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True
                      ).encode()


def select(q: str, rows: int = 200,
           solr_url: str = SOLR) -> dict[str, Any]:
    """One Solr select — returns the response object."""
    p = urllib.parse.urlencode({"q": q, "wt": "json",
                                "rows": str(rows)})
    req = urllib.request.Request(
        solr_url + "?" + p, headers=_UA)
    raw = urllib.request.urlopen(req, timeout=90).read()
    resp: dict[str, Any] = json.loads(raw)
    if "response" not in resp:
        raise SchemaError("PRIII Solr payload missing 'response'")
    out: dict[str, Any] = resp["response"]
    return out


def download_url(rfss_id: str) -> str:
    fid, _, cks = (rfss_id or "").partition(",")
    if not fid or not cks:
        return ""
    return RFSS_DOWNLOAD.format(fid=fid, cks=cks)


def _first(docs: list[dict[str, Any]]) -> dict[str, Any]:
    return docs[0] if docs else {}


def _children_by_type(children: list[dict[str, Any]]
                      ) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for c in children:
        out.setdefault(str(c.get("entity_type") or ""), []).append(c)
    return out


def fetch_raw(isin: str,
              select_fn: Any = select) -> dict[str, Any]:
    """Raw Solr responses for one ISIN — the archivable form.

    ``{ifii: <response>, filings: [{root, parent: <response>,
    children: <response>}]}`` — bytes that hash, store, and
    replay identically."""
    ifii_resp = select_fn(f'ifii_isin:"{isin}"')
    ifii_docs = ifii_resp.get("docs") or []
    roots = sorted({str(d.get("_root_") or
                            d.get("ifii_docVersionDbId"))
                    for d in ifii_docs
                    if d.get("_root_") or
                    d.get("ifii_docVersionDbId")})
    return {"isin": isin, "ifii": ifii_resp,
            "filings": [
                {"root": root,
                 "parent": select_fn(
                     f'_root_:"{root}" AND type_s:parent'),
                 "children": select_fn(
                     f'_root_:"{root}" AND type_s:child')}
                for root in roots]}


def normalize_raw(raw: dict[str, Any]) -> dict[str, Any]:
    """Captured raw payload → normalized filing graph.

    Used identically by the live path, the update pipeline, and
    the fixture store — one normalization, no drift."""
    filings: list[dict[str, Any]] = []
    for entry in raw.get("filings") or []:
        root = str(entry.get("root") or "")
        parent_resp = entry.get("parent") or {}
        children_resp = entry.get("children") or {}
        parent = _first(parent_resp.get("docs") or [])
        children = children_resp.get("docs") or []
        by = _children_by_type(children)
        issuers = by.get("issuers", [])
        offerors = by.get("offerors", [])
        rels = [c.get("related_document_identifier_search")
                for c in children
                if c.get("related_document_identifier_search")]
        pscn = sorted(c.get("pscn_country_code") or ""
                      for c in by.get("passportCountry", [])
                      if c.get("pscn_country_code"))
        isin_doc = _first(by.get("isinFinInstrInfo", []))
        filings.append({
            "root": root,
            "parent": parent,
            "children": children,
            "document_type": str(parent.get("document_type") or ""),
            "document_type_descr": str(
                parent.get("document_type_descr") or ""),
            "prospectus_type": str(
                parent.get("prospectus_type_code") or ""),
            "structure_type": str(
                parent.get("structure_type_code") or ""),
            "national_document_id": str(
                parent.get("national_document_id") or ""),
            "home_member_state": str(
                parent.get("home_member_state_descr") or ""),
            "home_member_state_code": str(
                parent.get("home_member_state_code") or ""),
            "member_states": tuple(sorted(
                str(parent.get("member_states") or "").replace(
                    " ", "").split(","))
                ) if parent.get("member_states") else (),
            "passport_countries": tuple(pscn),
            "is_passported": bool(int(
                parent.get("is_passported") or 0)),
            "approval_filing_date": str(
                parent.get("approval_filing_date") or ""),
            "first_passporting_date": str(
                parent.get("first_passporting_date") or ""),
            "last_passporting_date": str(
                parent.get("last_passporting_date") or ""),
            "doc_last_update_date": str(
                parent.get("doc_last_update_date") or ""),
            "document_rfss_id": str(
                parent.get("document_rfss_id") or ""),
            "download_url": download_url(
                str(parent.get("document_rfss_id") or "")),
            "party_name": str(parent.get("party_name") or ""),
            "issuer_lei": str(
                issuers[0].get("issuer_lei") or ""
            ) if issuers else "",
            "issuer_name": str(
                issuers[0].get("issuer_name") or ""
            ) if issuers else "",
            "offeror_lei": str(
                offerors[0].get("offeror_lei") or ""
            ) if offerors else "",
            "offeror_name": str(
                offerors[0].get("offeror_name") or ""
            ) if offerors else "",
            "related_document_ids": tuple(str(r) for r in rels),
            "document_languages": str(
                parent.get("document_languages") or ""),
            "ifii_doc_type": str(isin_doc.get("ifii_docType") or ""),
            "ifii_mat_exp_date": str(
                isin_doc.get("ifii_matExpDate") or ""),
            "ifii_securities_type": str(
                isin_doc.get("ifii_securitiesType") or ""),
            "ifii_trading_venue": str(
                isin_doc.get("ifii_tradingVenue") or ""),
            "parent_sha": hashlib.sha256(
                _canon(parent)).hexdigest(),
            "children_sha": hashlib.sha256(
                _canon(children)).hexdigest(),
        })
    payload = {"isin": str(raw.get("isin") or ""),
               "ifii": raw.get("ifii") or {},
               "filings": filings}
    payload["sha256"] = hashlib.sha256(_canon(payload)).hexdigest()
    return payload


def family_for_isin(
        isin: str,
        select_fn: Any = select) -> dict[str, Any]:
    """Live path: fetch raw responses, normalize, return the
    family graph (with a sha of the normalized payload)."""
    return normalize_raw(fetch_raw(isin, select_fn))
