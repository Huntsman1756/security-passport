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


def test_esmil_workbook_parse() -> None:
    """The captured workbook slice proves instrument-level
    evidence exists in the corpus."""
    import json

    rows = json.loads(
        (CORPUS / "esmil" / "rows.json").read_text(
            encoding="utf-8"))["rows"]
    assert len(rows) == 5
    by_isin = {r["isin"]: r for r in rows}
    assert by_isin["FR0000120271"]["issuer_csd_name"] == \
        "Euroclear France"
    assert by_isin["FR0000120271"]["issuer_csd_code"] == "CLFR01"
    assert by_isin["IE00B4L5Y983"]["issuer_csd_code"] == "CLBE02"
    assert all(r["state"] == "reported" for r in rows)
