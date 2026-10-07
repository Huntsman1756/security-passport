"""Euronext Securities Milan — "ISINs eligible for settlement"
workbook.

Instrument-level CSD admission evidence: the Euronext-operated
file lists, per ISIN, the designated place of settlement, the
alternative settlement systems and the issuer CSD. This is
*instrument-specific* evidence — categorically different from
SSS-link topology. Identified via the posttrade-europe source
catalog; SP parses the official artifact directly (PARSER-owned
normalization, no runtime dep on posttrade-europe).

The workbook has three sheets — Equities, ETPs, International
ETPs — each keyed on ``ISIN Code``.
"""
from __future__ import annotations

import io
import re
from typing import Any

PROVIDER = "euronext_esmil"
PARSER = "security_passport.providers.euronext_esmil"
PARSER_VERSION = "1"

# dated workbook; the file is republished periodically under the
# same naming convention
URL_TEMPLATE = (
    "https://www.euronext.com/sites/default/files/{ym}/"
    "ISINs%20eligible%20for%20settlement%20in%20Euronext%20"
    "Securities%20Milan%20{date}.xlsx")

# "Issuer CSD" names → the ECB dictionary code where the same CSD
# is corroborated; left None when only a verbatim name is known
CSD_NAME_TO_CODE = {
    "Euroclear Bank": "CLBE02",
    "Euroclear France": "CLFR01",
    "Euroclear Belgium": "CLBE01",
    "Euroclear Nederland": "CLNL01",
    "Iberclear": "CLES01",
    "Iberclear-ARCO": "CLES01",
    "Clearstream Banking Frankfurt": "CLDE01",
    "Clearstream Europe AG - CASCADE": "CLDE01",
    "Euronext Securities Milan": "CLIT01",
    "LuxCSD": "CLLU03",
    "Clearstream Banking S.A.": "CLLU01",
}


def parse_workbook(data: bytes) -> list[dict[str, Any]]:
    """xlsx bytes → per-ISIN rows (all three sheets)."""
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True)
    rows: list[dict[str, Any]] = []
    for sheet in wb.sheetnames[1:]:       # sheet 0 is the preface
        ws = wb[sheet]
        hdr: list[str] | None = None
        for row in ws.iter_rows(values_only=True):
            cells = [str(c).strip() if c is not None else ""
                     for c in row]
            if hdr is None:
                if cells and cells[0] == "ISIN Code":
                    hdr = cells
                continue
            isin = cells[0]
            if not re.match(r"^[A-Z]{2}[A-Z0-9]{10}$", isin):
                continue
            rec = dict(zip(hdr, cells, strict=False))
            rows.append({
                "isin": isin,
                "sheet": sheet,
                "issuer_name": rec.get("Issuer name")
                or rec.get("Issuer Name") or "",
                "issuer_country": rec.get("Issuer country")
                or rec.get("Issuer\ncountry")
                or rec.get("Issuer Country") or "",
                "market": rec.get("Market") or "",
                "mic": rec.get("MIC Code") or "",
                "other_mic": rec.get(
                    "Other MIC Code \n(for ISINs settling in ESM)")
                or rec.get("Other MIC Code (for ISINs settling "
                           "in ESM)") or "",
                "settlement_currency": rec.get(
                    "Settlement currency") or "",
                "issuer_csd_name": rec.get("Issuer CSD") or "",
            })
    return rows


def normalize(rec: dict[str, Any], observed_at: str,
              artifact_sha: str,
              file_date: str) -> dict[str, Any]:
    """Workbook row → normalized instrument-CSD evidence."""
    return {
        "isin": rec["isin"],
        "provider": PROVIDER,
        "instrument_csd_evidence": True,
        "issuer_csd_name": rec["issuer_csd_name"],
        "issuer_csd_code": CSD_NAME_TO_CODE.get(
            rec["issuer_csd_name"]),
        "market": rec["market"], "mic": rec["mic"],
        "other_mic": rec["other_mic"],
        "settlement_currency": rec["settlement_currency"],
        "sheet": rec["sheet"],
        "state": "reported",
        "observed_at": observed_at,
        "artifact_sha256": artifact_sha,
        "file_date": file_date,
    }


def file_date_from_name(name: str) -> str:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", name)
    return m.group(1) if m else ""
