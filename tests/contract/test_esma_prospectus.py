"""PRIII contract — captured real Solr payload → document graph."""
from __future__ import annotations

import json
from pathlib import Path

from security_passport.providers import esma_prospectus

CORPUS = Path(__file__).resolve().parent.parent / \
    "fixtures" / "corpus" / "priii"


def test_eph_bond_family() -> None:
    raw = json.loads(
        (CORPUS / "DE000A3LJCB4.json").read_text(encoding="utf-8"))
    fam = esma_prospectus.normalize_raw(raw)
    assert fam["isin"] == "DE000A3LJCB4"
    assert len(fam["filings"]) == 1
    f = fam["filings"][0]
    assert f["document_type"] == "STDA"
    assert f["home_member_state_code"] == "LU"
    assert f["is_passported"] is True
    assert "AT" in f["member_states"] or \
        "AUSTRIA" in f["member_states"]
    assert f["national_document_id"] == "C-028898"
    assert f["document_rfss_id"]
    assert f["download_url"].startswith(
        "https://registers.esma.europa.eu/publication/downloadFile")
    assert f["issuer_lei"] == "894500SN5GTABFSFWS54"
    assert f["issuer_name"]


def test_emtn_no_filings_is_clean_absence() -> None:
    raw = json.loads(
        (CORPUS / "XS2081615473.json").read_text(encoding="utf-8"))
    fam = esma_prospectus.normalize_raw(raw)
    assert fam["filings"] == []


def test_deterministic_sha() -> None:
    raw = json.loads(
        (CORPUS / "DE000A3LJCB4.json").read_text(encoding="utf-8"))
    a = esma_prospectus.normalize_raw(raw)
    b = esma_prospectus.normalize_raw(raw)
    assert a["sha256"] == b["sha256"]


def test_normalize_empty_raw() -> None:
    fam = esma_prospectus.normalize_raw(
        {"isin": "XSSE2WKP7HV5", "ifii": {"docs": []},
         "filings": []})
    assert fam["filings"] == []
    assert fam["sha256"]


def test_download_url_builds_rfss_link() -> None:
    url = esma_prospectus.download_url("12345,abc")
    assert "fileId=12345" in url and "checksum=abc" in url
    assert esma_prospectus.download_url("") == ""
