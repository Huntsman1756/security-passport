"""ECB eligible-assets dictionary — official codebook for
ISSUER_CSD, asset types, issuer groups and reference markets.

This replaces hand-curated labels with source-derived ones:
``CLBL01`` is a JOINT ICSD code (Euroclear Bank / Clearstream
Banking S.A.), not Clearstream alone. Every label here is
verbatim from the ECB dictionary page — a provenance-bearing
codebook, not a guess.
"""
from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

PROVIDER = "ecb_collateral_dictionary"
PARSER = "security_passport.providers.ecb_dictionary"
PARSER_VERSION = "1"

URL = ("https://www.ecb.europa.eu/mopo/coll/assets/guide/html/"
       "dictionary.en.html")

# page section title → store key
SECTIONS = {
    "Issuer CSDs": "issuer_csd",
    "Issuer Groups": "issuer_group",
    "Reference Markets": "reference_market",
    "Asset Types": "asset_type",
    "Haircut categories": "haircut_category",
}

_CODE = re.compile(r"^[A-Z]{2}[A-Z0-9]{2}\d{2}$")


def parse(html: str) -> dict[str, dict[str, str]]:
    """Parse the dictionary page → {section: {code: label}}."""
    soup = BeautifulSoup(html, "lxml")
    out: dict[str, dict[str, str]] = {}
    # each codebook is a <dl> under a definition-list block whose
    # title text is the section name
    for block in soup.select("div.definition-list"):
        title_el = block.select_one(".title p") or \
            block.select_one(".title")
        title = title_el.get_text(strip=True) if title_el else ""
        key = SECTIONS.get(title)
        if not key:
            continue
        entries: dict[str, str] = {}
        dl = block.find("dl")
        if dl:
            dts = dl.find_all("dt")
            dds = dl.find_all("dd")
            for dt, dd in zip(dts, dds, strict=False):
                code = dt.get_text(strip=True)
                label = " ".join(dd.get_text(" ", strip=True)
                                 .split())
                if _CODE.match(code) or code:
                    entries[code] = label
        out[key] = entries
    return out


def fetch() -> bytes:
    import urllib.request
    with urllib.request.urlopen(
            urllib.request.Request(
                URL, headers={"User-Agent":
                              "security-passport/0.1"}),
            timeout=120) as r:
        return bytes(r.read())


def csd_label(code: str, table: dict[str, str]) -> dict[str, Any]:
    """Label an ISSUER_CSD code using the dictionary table.

    ECB labels carry a trailing ``(Country)`` — split it into the
    country field; keep the rest verbatim."""
    label = table.get(code, "")
    country = ""
    m = re.search(r"\s*\(([^()]*)\)\s*$", label)
    if m:
        country = m.group(1)
        name = label[: m.start()].strip()
    else:
        name = label
    return {"code": code, "name": name, "country": country}
