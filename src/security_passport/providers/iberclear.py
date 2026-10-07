"""Iberclear — curated registry facts only (ADR-006).

Iberclear (BME) publishes no public machine-readable registry of
admitted ISINs. In v0.1.0 this module provides exactly two things:

1. The ECB CSD code → SSS name mapping context so an ECB
   ``ISSUER_CSD=CLES01`` row can be labelled correctly.
2. The explicit limitation text the passport carries when no
   instrument-specific Iberclear evidence exists.

Nothing here asserts that a given ISIN is registered with or
settles through Iberclear.
"""
from __future__ import annotations

PROVIDER = "iberclear"

# ECB eligible-assets ISSUER_CSD codes — verbatim labels from the
# ECB "Eligible Assets Dictionary" (providers/ecb_dictionary.py
# parses the live page; this table is the offline fallback for it,
# not a hand-rolled guess — v0.1 had CLBL01 mislabelled as
# Clearstream Banking Luxembourg alone).
# CLBL01 is a JOINT ICSD code — XS securities dual-issued through
# Euroclear Bank / Clearstream Banking S.A. collapse to it.
SSS_BY_CSD_CODE: dict[str, dict[str, str]] = {
    "CLAT01": {"name": "OeKB", "country": "Austria"},
    "CLBE01": {"name": "NBB SSS", "country": "Belgium"},
    "CLBE02": {"name": "Euroclear Bank", "country": "Belgium"},
    "CLBG01": {"name": "BNBGSSS", "country": "Bulgaria"},
    "CLBL01": {"name": "Euroclear Bank / Clearstream Banking S.A.",
               "country": "Belgium / Luxembourg"},
    "CLCY01": {"name": "CDCR", "country": "Cyprus"},
    "CLCZ01": {"name": "CDCP", "country": "Czech Republic"},
    "CLDE01": {"name": "Clearstream Europe AG - CASCADE",
               "country": "Germany"},
    "CLDK01": {"name": "Euronext Securities Copenhagen",
               "country": "Denmark"},
    "CLEE01": {"name": "Nasdaq CSD SE", "country": "Estonia"},
    "CLES01": {"name": "Iberclear-ARCO", "country": "Spain"},
    "CLEU01": {"name": "ECB debt certificates", "country": ""},
    "CLFI01": {"name": "Euroclear Finland Infinity System",
               "country": "Finland"},
    "CLFR01": {"name": "Euroclear France", "country": "France"},
    "CLGR01": {"name": "BOGS", "country": "Greece"},
    "CLHR01": {"name": "SKDD", "country": "Croatia"},
    "CLIT01": {"name": "Euronext Securities Milan",
               "country": "Italy"},
    "CLLT02": {"name": "Nasdaq CSD SE", "country": "Lithuania"},
    "CLLU01": {"name": "Clearstream Banking S.A.",
               "country": "Luxembourg"},
    "CLLU03": {"name": "LuxCSD", "country": "Luxembourg"},
    "CLLV02": {"name": "Nasdaq CSD SE", "country": "Latvia"},
    "CLMT01": {"name": "MaltaClear", "country": "Malta"},
    "CLNL01": {"name": "Euroclear Nederland",
               "country": "Netherlands"},
    "CLPT02": {"name": "Euronext Securities Porto",
               "country": "Portugal"},
    "CLSE01": {"name": "Euroclear Sweden VPC", "country": "Sweden"},
    "CLSI01": {"name": "KDD", "country": "Slovenia"},
    "CLSK01": {"name": "CDCP", "country": "Slovakia"},
}

IBERCLEAR_CODES = {"CLES01"}

LIMITATION_TEXT = (
    "No public instrument-level Iberclear admission registry "
    "exists. Iberclear membership can only be evidenced via the "
    "ECB eligible-assets ISSUER_CSD field (when the asset is "
    "Eurosystem-eligible) or equivalent instrument-specific "
    "publications. An ES-prefixed ISIN is a discovery signal, "
    "not evidence of Iberclear registration.")


def sss_for_csd_code(code: str) -> dict[str, str] | None:
    return SSS_BY_CSD_CODE.get((code or "").strip().upper())
