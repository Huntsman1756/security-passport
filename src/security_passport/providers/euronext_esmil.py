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
    # the workbook's own shorthand for its host CSD
    "Euronext Securities": "CLIT01",
}


def parse_workbook(data: bytes) -> list[dict[str, Any]]:
    """xlsx bytes → per-ISIN rows (all three sheets), full width.

    Columns 9-12 are the settlement semantics:
    ``Current place of settlement``, ``In/out of scope``,
    ``Designated place of settlement as of <date>``,
    ``Alternative Settlement Systems`` (spillover columns 12+)."""
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True,
                               data_only=True)
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
            # designated/alternative headers contain a date —
            # locate them positionally after the first 8 cols
            designated_i = next(
                (i for i, h in enumerate(hdr) if h and
                 h.startswith("Designated")), None)
            alt_i = next(
                (i for i, h in enumerate(hdr) if h and
                 h.startswith("Alternative")), None)
            current_i = next(
                (i for i, h in enumerate(hdr) if h and
                 h.startswith("Current")), None)
            scope_i = next(
                (i for i, h in enumerate(hdr) if h and
                 h.startswith("In/out")), None)
            designated = (cells[designated_i]
                          if designated_i is not None else "")
            alternatives = [c for c in cells[alt_i:]
                            if c and not c.startswith("=")] \
                if alt_i is not None else []
            # effective date embedded in the header text
            eff = ""
            if designated_i is not None:
                m = re.search(r"(\d{1,2} \w+ \d{4})",
                              hdr[designated_i])
                if m:
                    import datetime as _dt
                    eff = _dt.datetime.strptime(
                        m.group(1), "%d %B %Y").date().isoformat()
            des_flag = ""
            if designated.endswith("*"):
                des_flag = "main_depositary_exception"
                designated = designated.rstrip("*")
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
                "current_place": (cells[current_i]
                                  if current_i is not None else ""),
                "scope": (cells[scope_i]
                          if scope_i is not None else ""),
                "designated": designated,
                "designated_flag": des_flag,
                "alternatives": alternatives,
                "effective_from": eff,
            })
    return rows


def normalize(rec: dict[str, Any], observed_at: str,
              artifact_sha: str,
              file_date: str,
              provider: str = PROVIDER) -> list[dict[str, Any]]:
    """Workbook row → one record per *settlement location*.

    A single ISIN can legitimately carry several locations:
    the issuer CSD, the pre-migration place, the designated
    place (post go-live) and any alternatives — each is its
    own reported assertion, never merged."""
    base = {
        "isin": rec["isin"], "provider": provider,
        "market": rec["market"], "mic": rec["mic"],
        "other_mic": rec["other_mic"],
        "settlement_currency": rec["settlement_currency"],
        "sheet": rec["sheet"], "scope": rec.get("scope", ""),
        "state": "reported",
        "observed_at": observed_at,
        "artifact_sha256": artifact_sha,
        "file_date": file_date,
    }

    def loc(csd_name: str, relationship: str,
            effective_from: str, flag: str = "") -> dict[str, Any]:
        return {**base,
                "csd_name": csd_name,
                "csd_code": CSD_NAME_TO_CODE.get(csd_name),
                "relationship": relationship,
                "effective_from": effective_from,
                "source_published_at": file_date,
                "note": flag}

    out: list[dict[str, Any]] = []
    if rec.get("issuer_csd_name"):
        out.append(loc(rec["issuer_csd_name"],
                       "issuer_csd", ""))
    if rec.get("current_place") and \
            rec["current_place"] != rec["issuer_csd_name"]:
        out.append(loc(rec["current_place"],
                       "current_place_of_settlement", ""))
    if rec.get("designated"):
        out.append(loc(rec["designated"],
                       "designated_place_of_settlement",
                       rec["effective_from"],
                       rec.get("designated_flag", "")))
    for alt in rec.get("alternatives") or []:
        if alt != rec.get("designated"):
            out.append(loc(alt,
                           "alternative_settlement_system",
                           rec["effective_from"]))
    return out


FRS_URL_TEMPLATE = (
    "https://www.euronext.com/sites/default/files/{ym}/"
    "euronext_securities_-_isins_for_french_registered_shares_"
    "{ddmmyy}.xlsx")


def parse_fr_registered(data: bytes) -> list[dict[str, Any]]:
    """"ISINs for french registered shares" workbook — the
    European-offering docs page's second instrument-level file.
    Single sheet, ISIN/issuer/country/issuer-CSD columns."""
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True,
                               data_only=True)
    out: list[dict[str, Any]] = []
    for sheet in wb.sheetnames:
        ws = wb[sheet]
        hdr_seen = False
        for row in ws.iter_rows(values_only=True):
            cells = [str(c).strip() if c is not None else ""
                     for c in row]
            if not hdr_seen:
                if cells and cells[0] == "ISIN Code":
                    hdr_seen = True
                continue
            isin = cells[0]
            if not re.match(r"^[A-Z]{2}[A-Z0-9]{10}$", isin):
                continue
            out.append({
                "isin": isin,
                "sheet": sheet,
                "issuer_name": cells[1] if len(cells) > 1 else "",
                "issuer_country": cells[2] if len(cells) > 2 else "",
                "market": "EURONEXT PARIS", "mic": "",
                "other_mic": "",
                "settlement_currency": "EUR",
                "issuer_csd_name": cells[3] if len(cells) > 3
                else "",
                "current_place": "", "scope": "",
                "designated": "", "designated_flag": "",
                "alternatives": [], "effective_from": "",
            })
    return out


def file_date_from_name(name: str) -> str:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", name)
    if m:
        return m.group(1)
    m = re.search(r"(\d{2})(\d{2})(\d{2})", name)
    return f"20{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""
