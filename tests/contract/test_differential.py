"""Differential: SP ECB store vs OpenInstrument's ecb_eligible
assertions — same source, two pipelines. UNEXPLAINED = release
blocker; SOURCE_VERSION_SKEW is expected (different snapshots)."""
from __future__ import annotations

import json
from pathlib import Path

from security_passport.providers.fixtures import FixturePassportStore
from security_passport.services.differential import (
    Verdict,
    compare_ecb_asset,
)

CORPUS = Path("tests/fixtures/corpus")
OI_FIXTURE = json.loads(
    (CORPUS / "openinstrument_ecb" / "rows.json").read_text(
        encoding="utf-8"))


def test_cross_pipeline_differential() -> None:
    store = FixturePassportStore(str(CORPUS))
    ours_snap = store.ecb_snapshot()
    theirs_ver = OI_FIXTURE["version"]
    assert ours_snap != theirs_ver  # skew is real, not assumed

    for isin in ("XS2081615473", "ES0000101966", "DE000A3LJCB4",
                 "DE0007164600", "IE0007SRI1C7", "LU0003549028",
                 "ES0113900J37", "XSSE2WKP7HV5"):
        ours = store.ecb_asset(isin)
        ours_row = ({"haircut_category": ours.haircut_category,
                     "asset_type": ours.asset_type,
                     "issuer_csd": ours.issuer_csd,
                     "haircut": ours.haircut,
                     "issuance_date": ours.issuance_date,
                     "maturity_date": ours.maturity_date,
                     "issuer_name": ours.issuer_name}
                    if ours else None)
        rep = compare_ecb_asset(
            isin, ours_row, ours_snap,
            OI_FIXTURE["rows"].get(isin), theirs_ver)
        assert rep.ok(), \
            f"{isin}: blocking diffs " + str(
            [(d.field, d.verdict.value) for d in rep.blocking])


def test_taxonomy_blocks_unexplained() -> None:
    rep = compare_ecb_asset(
        "X", {"haircut_category": "L1D", "asset_type": "AT02",
              "issuer_csd": "CLBL01", "haircut": "11.5",
              "issuance_date": "2020-01-01",
              "maturity_date": "2030-01-01",
              "issuer_name": "X"},
        "261006",
        {"haircut_category": "L2D", "asset_type": "AT02",
         "issuer_csd": "CLBL01", "haircut": "11.5",
         "issuance_date": "2020-01-01", "maturity_date": "2030-01-01",
         "issuer_name": "X"},
        "261006")   # same snapshot — no skew excuse
    assert not rep.ok()
    assert any(d.field == "haircut_category"
               and d.verdict is Verdict.UNEXPLAINED
               for d in rep.blocking)


def test_expected_transformation_classified() -> None:
    rep = compare_ecb_asset(
        "X", {"haircut_category": "L1D", "asset_type": "AT02",
              "issuer_csd": "CLBL01", "haircut": "11.5",
              "issuance_date": "2020-01-01",
              "maturity_date": "2030-01-01",
              "issuer_name": "epH group"},
        "261006",
        {"haircut_category": "L1D", "asset_type": "AT02",
         "issuer_csd": "CLBL01", "haircut": "11.5",
         "issuance_date": "2020-01-01", "maturity_date": "2030-01-01",
         "issuer_name": "EPH GROUP"},
        "261006")
    assert rep.ok()
    assert any(d.verdict is Verdict.EXPECTED_TRANSFORMATION
               for d in rep.diffs)


def test_version_skew_not_blocking() -> None:
    rep = compare_ecb_asset(
        "X", {"haircut_category": "L1D"}, "261006",
        {"haircut_category": "L1B"}, "260925")
    assert rep.ok()
    assert all(d.verdict is Verdict.SOURCE_VERSION_SKEW
               for d in rep.diffs if d.verdict is not Verdict.SAME)
