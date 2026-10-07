"""ECB eligible-assets contract — real UTF-16 TSV slice + schema
drift behavior (fail closed)."""
from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from security_passport.providers import ecb_assets

FIXTURE = Path(__file__).resolve().parent.parent / \
    "fixtures" / "corpus" / "ecb_assets" / "ea_slice.csv"


def test_parse_real_slice() -> None:
    rows = ecb_assets.parse(FIXTURE.read_bytes())
    assert len(rows) >= 8   # slice grows with the golden corpus
    by_isin = {r["ISIN_CODE"]: r for r in rows}
    assert "XS2081615473" in by_isin
    assert "ES0000101966" in by_isin
    assert by_isin["ES0000101966"]["ISSUER_CSD"] == "CLES01"
    assert by_isin["XS2081615473"]["HAIRCUT_CATEGORY"] == "L1D"


def test_normalize_dates_and_fields() -> None:
    rows = ecb_assets.parse(FIXTURE.read_bytes())
    n = ecb_assets.normalize(rows[0], snapshot="261006",
                             retrieved_at="t")
    assert n["issuance_date"].count("-") == 2
    assert n["maturity_date"].startswith("20")
    assert n["snapshot"] == "261006"


def test_schema_drift_fails_closed() -> None:
    bad = "ISIN_CODE\tFOO\nXX1\ty\r\n".encode("utf-16")
    with pytest.raises(ecb_assets.SchemaError):
        ecb_assets.parse(bad)


def test_gzip_wrapped_input() -> None:
    raw = FIXTURE.read_bytes()
    rows_plain = ecb_assets.parse(raw)
    rows_gz = ecb_assets.parse(gzip.compress(raw))
    assert rows_plain == rows_gz


def test_empty_rows_skipped() -> None:
    raw = FIXTURE.read_bytes()
    rows = ecb_assets.parse(raw)
    assert all(r["ISIN_CODE"].strip() for r in rows)
