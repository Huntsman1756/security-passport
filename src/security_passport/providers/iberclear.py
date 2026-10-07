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

# ECB eligible-assets ISSUER_CSD codes are 6-char composites
# (CSD short code + country). Only names needed to label SSSs that
# appear in the Eurosystem eligible-SSS list are curated here;
# unknown codes are passed through verbatim with a quality flag.
SSS_BY_CSD_CODE: dict[str, dict[str, str]] = {
    "CLES01": {"name": "Iberclear-ARCO", "country": "Spain"},
    "CLDE01": {"name": "Clearstream Europe AG - CASCADE",
               "country": "Germany"},
    "CLBL01": {"name": "CBL (Clearstream Banking Luxembourg)",
               "country": "Luxembourg"},
    "CLFB01": {"name": "Euroclear France", "country": "France"},
    "EBBE01": {"name": "Euroclear Bank", "country": "Belgium"},
    "ENNL01": {"name": "Euroclear Nederland",
               "country": "Netherlands"},
    "NBBE01": {"name": "NBB-SSS", "country": "Belgium"},
    "OEAT01": {"name": "OeKB CSD GmbH", "country": "Austria"},
    "ESES01": {"name": "Euronext Securities Porto",
               "country": "Portugal"},
    "ESMI01": {"name": "Euronext Securities Milan",
               "country": "Italy"},
    "BOGR01": {"name": "BOGS", "country": "Greece"},
    "LULU01": {"name": "LuxCSD", "country": "Luxembourg"},
    "DKDK01": {"name": "Euronext Securities Copenhagen",
               "country": "Denmark"},
    "EFFI01": {"name": "Euroclear Nordics Oy", "country": "Finland"},
    "MTMT01": {"name": "MaltaClear", "country": "Malta"},
    "CDCZ01": {"name": "CSD Prague", "country": "Czech Republic"},
    "CDSK01": {"name": "CDCP", "country": "Slovakia"},
    "KDSI01": {"name": "KDD", "country": "Slovenia"},
    "NDLT01": {"name": "Nasdaq CSD SE", "country": "Baltics"},
    "SKHR01": {"name": "SKDD", "country": "Croatia"},
    "CDCY01": {"name": "CDCR", "country": "Cyprus"},
    "HUHU01": {"name": "KELER", "country": "Hungary"},
    "PLPL01": {"name": "KDPW", "country": "Poland"},
    "RORO01": {"name": "Depozitarul Central", "country": "Romania"},
    "BGBG01": {"name": "BNBGSSS", "country": "Bulgaria"},
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
