"""Instrument-level post-trade evidence — ECB dictionary parse +
Euronext Securities Milan workbook adapter."""
from __future__ import annotations

from pathlib import Path

from security_passport.providers import ecb_dictionary

CORPUS = Path("tests/fixtures/corpus")


def test_dictionary_issuer_csd_codebook() -> None:
    html = (CORPUS / "ecb_dictionary" / "dictionary.en.html") \
        .read_text(encoding="utf-8", errors="replace")
    d = ecb_dictionary.parse(html)
    csd = d["issuer_csd"]
    assert len(csd) >= 25
    # the joint ICSD code — never "just Clearstream Lux"
    assert "Euroclear Bank" in csd["CLBL01"]
    assert "Clearstream Banking S.A." in csd["CLBL01"]
    assert csd["CLES01"] == "Iberclear (ARCO) (Spain)"
    assert csd["CLIT01"].startswith("Euronext Securities Milan")
    assert d["asset_type"]["AT01"] == "Bond"
    assert d["issuer_group"]["IG1"] == "Central Bank"


def test_esmil_settlement_locations() -> None:
    """Multi-location model: one ISIN legitimately carries
    issuer / designated / alternative settlement CSDs."""
    import json

    rows = json.loads(
        (CORPUS / "esmil" / "rows.json").read_text(
            encoding="utf-8"))["rows"]
    assert rows
    by_isin: dict[str, list[dict]] = {}
    for r in rows:
        by_isin.setdefault(r["isin"], []).append(r)
    assert all(r["state"] == "reported" for r in rows)
    # TotalEnergies: issuer Euroclear France + designated Euronext
    # Securities Milan (effective go-live) + alternatives
    locs = by_isin["FR0000120271"]
    rels = {r["relationship"]: r["csd_name"] for r in locs}
    assert rels["issuer_csd"] == "Euroclear France"
    assert rels["designated_place_of_settlement"] == \
        "Euronext Securities"
    # publication date (file) vs effective go-live date differ —
    # the temporal golden
    des = next(r for r in locs
               if r["relationship"] ==
               "designated_place_of_settlement")
    assert des["source_published_at"] == "2026-09-18"
    assert des["effective_from"] == "2026-09-21"
    # multi-alternative case — the ETF has 2 alternatives
    ie = by_isin["IE00B4L5Y983"]
    alts = [r["csd_name"] for r in ie
            if r["relationship"] ==
            "alternative_settlement_system"]
    assert set(alts) == {"Euroclear Bank", "Euroclear Nederland"}


def test_parse_workbook_full_width() -> None:
    """Workbook parses designated/alternative columns; formulas
    never leak as evidence."""
    from security_passport.providers import euronext_esmil

    rows = euronext_esmil.parse_workbook(
        Path("tests/fixtures/corpus/esmil_workbook.xlsx")
        .read_bytes()) if Path(
            "tests/fixtures/corpus/esmil_workbook.xlsx") \
        .exists() else None
    if rows is None:
        import pytest
        pytest.skip("full workbook not captured as fixture")
    for r in rows:
        assert not str(r.get("designated", "")).startswith("=")
        assert all(not a.startswith("=")
                   for a in r.get("alternatives") or [])
