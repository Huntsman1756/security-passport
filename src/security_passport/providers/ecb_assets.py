"""ECB eligible marketable assets — bulk daily dataset.

Official download area lists full-database files as
``ea_csv_YYMMDD.csv[.gz]`` (UTF-16, tab-separated, ~31k rows).
The list is the Eurosystem's authoritative enumeration of eligible
marketable assets: presence = eligible as of that snapshot,
absence = not eligible as of that snapshot (not "never").

Fields (schema v260925/261006): ISIN_CODE, OTHER_REG_NUMBER,
HAIRCUT_CATEGORY, TYPE, REFERENCE_MARKET, DENOMINATION,
ISSUANCE_DATE, MATURITY_DATE, ISSUER_CSD, COUPON_RATE (%),
ISSUER_NAME, ISSUER_RESIDENCE, ISSUER_GROUP, GUARANTOR_NAME,
GUARANTOR_RESIDENCE, GUARANTOR_GROUP, COUPON_DEFINITION, HAIRCUT,
HAIRCUT_OWN_USE, POTENTIALLY_OWN_USABLE_COVERED_BOND,
CLIMATE_FACTOR.
"""
from __future__ import annotations

import gzip
import hashlib
import re
import urllib.request
from typing import Any

PARSER = "security_passport.providers.ecb_assets"
PARSER_VERSION = "1"
PROVIDER = "ecb_eligible_assets"
DATASET = "ea_csv"

LIST_PAGE = ("https://www.ecb.europa.eu/mopo/coll/assets/html/"
             "list-MID.en.html")
_UA = {"User-Agent": "security-passport/0.1.0"}

_HREF_RE = re.compile(r'href="([^"]*/ea_csv_\d{6}\.csv\.gz)"')

EXPECTED_COLUMNS = [
    "ISIN_CODE", "OTHER_REG_NUMBER", "HAIRCUT_CATEGORY", "TYPE",
    "REFERENCE_MARKET", "DENOMINATION", "ISSUANCE_DATE",
    "MATURITY_DATE", "ISSUER_CSD", "COUPON_RATE (%)", "ISSUER_NAME",
    "ISSUER_RESIDENCE", "ISSUER_GROUP", "GUARANTOR_NAME",
    "GUARANTOR_RESIDENCE", "GUARANTOR_GROUP", "COUPON_DEFINITION",
    "HAIRCUT", "HAIRCUT_OWN_USE",
    "POTENTIALLY_OWN_USABLE_COVERED_BOND", "CLIMATE_FACTOR",
]


class SchemaError(Exception):
    """Unexpected ECB file shape — fail closed, never guess."""


def latest_url(list_page_html: str | None = None
               ) -> tuple[str, str]:
    """(absolute_url, snapshot_tag like '261006')."""
    html = list_page_html
    if html is None:
        html = urllib.request.urlopen(  # noqa: S310 — allowlisted
            urllib.request.Request(LIST_PAGE, headers=_UA),
            timeout=60).read().decode("utf-8", "replace")
    m = _HREF_RE.search(html)
    if not m:
        return "", ""
    href = m.group(1)
    tag = href.rsplit("_", 1)[-1].split(".")[0]
    return "https://www.ecb.europa.eu" + href, tag


def download(url: str) -> tuple[bytes, str]:
    raw = urllib.request.urlopen(  # noqa: S310 — allowlisted ECB
        urllib.request.Request(url, headers=_UA),
        timeout=300).read()
    return raw, hashlib.sha256(raw).hexdigest()


def _dmy(s: str) -> str:
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def parse(raw: bytes) -> list[dict[str, str]]:
    """Decompress (if gzipped) + parse the UTF-16 TSV.

    Fail closed: an unexpected header shape raises SchemaError —
    a silent column drift would produce wrong passports."""
    data = raw
    if raw[:2] == b"\x1f\x8b":
        data = gzip.decompress(raw)
    txt = data.decode("utf-16")
    lines = [ln for ln in txt.split("\r\n") if ln.strip()]
    if not lines:
        return []
    hdr = lines[0].lstrip("﻿").split("\t")
    missing = [c for c in ("ISIN_CODE", "HAIRCUT_CATEGORY", "TYPE",
                           "ISSUER_CSD", "HAIRCUT")
               if c not in hdr]
    if missing:
        raise SchemaError(
            f"ECB ea_csv missing required columns: {missing}")
    out: list[dict[str, str]] = []
    for ln in lines[1:]:
        cells = ln.split("\t")
        row = dict(zip(hdr, cells, strict=False))
        if not row.get("ISIN_CODE", "").strip():
            continue
        out.append(row)
    return out


def normalize(row: dict[str, str], snapshot: str,
              retrieved_at: str) -> dict[str, Any]:
    """ECB row → normalized fact dict (dates ISO, rest verbatim)."""
    return {
        "isin": row.get("ISIN_CODE", "").strip(),
        "haircut_category": row.get("HAIRCUT_CATEGORY", ""),
        "asset_type": row.get("TYPE", ""),
        "reference_market": row.get("REFERENCE_MARKET", ""),
        "denomination_currency": row.get("DENOMINATION", ""),
        "issuance_date": _dmy(row.get("ISSUANCE_DATE", "")),
        "maturity_date": _dmy(row.get("MATURITY_DATE", "")),
        "issuer_csd": row.get("ISSUER_CSD", ""),
        "coupon_rate": row.get("COUPON_RATE (%)", ""),
        "issuer_name": row.get("ISSUER_NAME", ""),
        "issuer_residence": row.get("ISSUER_RESIDENCE", ""),
        "issuer_group": row.get("ISSUER_GROUP", ""),
        "guarantor_name": row.get("GUARANTOR_NAME", ""),
        "guarantor_residence": row.get("GUARANTOR_RESIDENCE", ""),
        "guarantor_group": row.get("GUARANTOR_GROUP", ""),
        "coupon_definition": row.get("COUPON_DEFINITION", ""),
        "haircut": row.get("HAIRCUT", ""),
        "haircut_own_use": row.get("HAIRCUT_OWN_USE", ""),
        "covered_bond_flag": row.get(
            "POTENTIALLY_OWN_USABLE_COVERED_BOND", ""),
        "climate_factor": row.get("CLIMATE_FACTOR", ""),
        "snapshot": snapshot,
        "retrieved_at": retrieved_at,
    }
