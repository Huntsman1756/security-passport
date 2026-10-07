"""ECB eligible SSSs + eligible links — HTML observed evidence.

Two public ECB pages:

- ``/mopo/coll/coll/eligiblesss/`` — table: Country | SSS name.
- ``/mopo/coll/coll/ssslinks/`` — "List of eligible links":
  per-country sections listing "Investor SSS to Issuer SSS"
  optionally "via Intermediary" and "operated by X".

These pages have no machine contract — we parse them as observed
evidence: every retrieval is archived with its sha256 and the
page's own "Last updated" stamp. A link between two SSSs is
topology evidence only; it never implies instrument eligibility.
"""
from __future__ import annotations

import hashlib
import re
import urllib.request
from dataclasses import dataclass
from typing import Any

PARSER = "security_passport.providers.ecb_sss"
PARSER_VERSION = "1"
PROVIDER = "ecb_sss_links"

SSS_PAGE = ("https://www.ecb.europa.eu/mopo/coll/coll/eligiblesss/"
            "html/index.en.html")
LINKS_PAGE = ("https://www.ecb.europa.eu/mopo/coll/coll/ssslinks/"
              "html/index.en.html")
_UA = {"User-Agent": "security-passport/0.1.0"}

_LAST_UPDATED_RE = re.compile(
    r"Last updated:\s*([0-9]{1,2}\s+\w+\s+[0-9]{4})")


class SchemaError(Exception):
    """Page shape changed beyond recognition — fail closed."""


def fetch(url: str) -> tuple[str, str]:
    raw = urllib.request.urlopen(
        urllib.request.Request(url, headers=_UA),
        timeout=60).read()
    return raw.decode("utf-8", "replace"), \
        hashlib.sha256(raw).hexdigest()


def page_stamp(html: str) -> str:
    """Extract the page's own "Last updated" date (ISO)."""
    m = _LAST_UPDATED_RE.search(html)
    if not m:
        return ""
    from datetime import datetime
    try:
        return datetime.strptime(m.group(1), "%d %B %Y"
                                 ).strftime("%Y-%m-%d")
    except ValueError:
        return m.group(1)


@dataclass
class SssEntry:
    country: str
    name: str


@dataclass
class LinkEntry:
    investor_sss: str
    issuer_sss: str
    intermediaries: tuple[str, ...] = ()
    operated_by: str = ""


def parse_sss_page(html: str) -> list[SssEntry]:
    """Country | SSS table → entries. Fail closed if no table."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    out: list[SssEntry] = []
    for tr in soup.find_all("tr"):
        cells = [c.get_text(" ", strip=True)
                 for c in tr.find_all(["td", "th"])]
        if len(cells) >= 2 and cells[0] and cells[1] \
                and cells[0].lower() != "country":
            # a row may carry multiple SSS names in one cell
            names = [n.strip() for n in
                     re.split(r"\n|;", cells[1]) if n.strip()]
            for n in names:
                out.append(SssEntry(country=cells[0], name=n))
    if not out:
        raise SchemaError("eligible SSS page: no table rows parsed")
    return out


def parse_links_page(html: str) -> list[LinkEntry]:
    """Parse "X to Y[, operated by Z]" and "X via V to Y" lines.

    The page text under each country section lists one link per
    line. We keep the verbatim line as evidence and extract
    investor/intermediary/issuer roles from the 'to'/'via'
    structure."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    main = soup.find("main") or soup
    text = main.get_text("\n", strip=True)
    links: list[LinkEntry] = []
    current_investor = ""
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        # section headers look like "Country - SSS name"
        sec = re.match(r"^([A-Z][\w .&()'/-]+?)\s*-\s*"
                       r"([A-Z][\w .&()'/+-]+?)$", line)
        if sec and " to " not in line and "via" not in line:
            current_investor = sec.group(2).strip()
            continue
        m = re.match(r"^(.*?)\s+(via\s+.+?)?\s*to\s+(.+?)$", line)
        if not m:
            continue
        investor_raw, via_raw, issuer_raw = m.groups()
        investor = (investor_raw or "").strip() or current_investor
        operated_by = ""
        issuer = issuer_raw.strip()
        op = re.match(r"^(.*?),\s*operated by\s+(.+)$", issuer)
        if op:
            issuer, operated_by = op.group(1).strip(), \
                op.group(2).strip()
        inter: list[str] = []
        if via_raw:
            inter = [v.strip() for v in re.split(
                r"\s+via\s+", via_raw) if v.strip()]
        if not investor or not issuer:
            continue
        links.append(LinkEntry(
            investor_sss=investor, issuer_sss=issuer,
            intermediaries=tuple(inter), operated_by=operated_by))
    if not links:
        raise SchemaError("eligible links page: no links parsed")
    return links


def parse_pages(sss_html: str, links_html: str
                ) -> dict[str, Any]:
    return {
        "sss": [s.__dict__ for s in parse_sss_page(sss_html)],
        "links": [lnk.__dict__ | {"intermediaries":
                                list(lnk.intermediaries)}
                  for lnk in parse_links_page(links_html)],
        "sss_page_stamp": page_stamp(sss_html),
        "links_page_stamp": page_stamp(links_html),
        "sss_sha": hashlib.sha256(sss_html.encode()).hexdigest(),
        "links_sha": hashlib.sha256(links_html.encode()).hexdigest(),
    }
