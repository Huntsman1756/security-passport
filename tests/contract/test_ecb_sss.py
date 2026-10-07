"""ECB SSS/links contract — captured real pages → topology."""
from __future__ import annotations

from pathlib import Path

import pytest

from security_passport.providers import ecb_sss

CORPUS = Path(__file__).resolve().parent.parent / \
    "fixtures" / "corpus" / "ecb_sss"

SSS_HTML = (CORPUS / "sss_page.html").read_text(encoding="utf-8")
LINKS_HTML = (CORPUS / "links_page.html").read_text(encoding="utf-8")


def test_sss_page_parses() -> None:
    sss = ecb_sss.parse_sss_page(SSS_HTML)
    names = {s.name for s in sss}
    assert any("Iberclear" in n for n in names)
    assert any("Clearstream" in n for n in names)
    assert len(sss) >= 15


def test_links_page_parses() -> None:
    links = ecb_sss.parse_links_page(LINKS_HTML)
    assert len(links) >= 40
    # a relayed link carries intermediaries
    relayed = [lnk for lnk in links if lnk.intermediaries]
    assert relayed
    # Iberclear appears as investor SSS
    ib = [lnk for lnk in links if "Iberclear" in lnk.investor_sss]
    assert ib


def test_page_stamps() -> None:
    out = ecb_sss.parse_pages(SSS_HTML, LINKS_HTML)
    assert out["links_page_stamp"]
    assert out["sss_page_stamp"]


def test_fail_closed_on_empty_page() -> None:
    with pytest.raises(ecb_sss.SchemaError):
        ecb_sss.parse_links_page("<html><body>nope</body></html>")
