"""Builder integration — passports over the fixture corpus."""
from __future__ import annotations

import pytest

from security_passport.providers.fixtures import (
    FixtureInstrumentProvider,
    FixturePassportStore,
)
from security_passport.services.passport_builder import PassportBuilder

CORPUS = "tests/fixtures/corpus"


@pytest.fixture(scope="module")
def builder() -> PassportBuilder:
    return PassportBuilder(FixtureInstrumentProvider(CORPUS),
                           FixturePassportStore(CORPUS))


def _field(p: dict, block: str, name: str) -> dict:
    return (p[block].get(name) or {})


def test_eph_bond_passport(builder: PassportBuilder) -> None:
    d = builder.build("DE000A3LJCB4", True).to_dict()
    assert d["overall_state"] == "found"
    idf = d["identity"]
    assert idf["cfi"]["value"] == "DBFUGB"
    assert idf["cfi"]["status"] == "reported"
    assert idf["issuer_lei"]["value"] == "894500SN5GTABFSFWS54"
    pm = d["primary_market"]
    assert pm["prospectus_found"]["value"] is True
    assert pm["home_member_state"]["value"] == "LU"
    assert pm["is_passported"]["value"] is True
    docs = pm["document_graph"]
    assert len(docs) == 1
    assert docs[0]["document_type"] == "STDA"
    sm = d["secondary_market"]
    assert len(sm["listings"]) == 16
    assert sm["first_admission_date"]["status"] == "derived"
    assert sm["first_admission_date"]["value"] == "2023-05-08"
    ec = d["eurosystem_collateral"]
    assert ec["eligible"]["value"] is False
    assert ec["eligible"]["status"] == "derived"
    assert ec["eligible"]["rule"]["rule_id"] == \
        "eurosystem_eligibility"
    pt = d["post_trade"]
    assert pt["issuer_csd"]["status"] == "not_found"
    assert d["post_trade"]["route_assessments"][0][
        "state"] == "not_assessable"
    assert pt["assessment"]["status"] == "derived"


def test_ecb_eligible_emtn(builder: PassportBuilder) -> None:
    d = builder.build("XS2081615473", True).to_dict()
    ec = d["eurosystem_collateral"]
    assert ec["eligible"]["value"] is True
    assert ec["haircut_category"]["value"] == "L1D"
    assert ec["haircut"]["value"] == "11.5"
    pt = d["post_trade"]
    assert pt["issuer_csd"]["status"] == "reported"
    assert pt["issuer_csd"]["value"]["code"] == "CLBL01"
    assert "Clearstream" in pt["issuer_csd"]["value"]["name"]
    pm = d["primary_market"]
    assert pm["prospectus_found"]["value"] is False
    assert pm["prospectus_found"]["status"] == "reported"


def test_iberclear_evidence(builder: PassportBuilder) -> None:
    d = builder.build("ES0000101966", True).to_dict()
    pt = d["post_trade"]
    assert pt["issuer_csd"]["value"]["code"] == "CLES01"
    assert pt["issuer_csd"]["value"]["name"] == "Iberclear (ARCO)"
    assert pt["iberclear_admitted"]["value"] is True
    assert pt["iberclear_admitted"]["status"] == "reported"


def test_no_iberclear_inference_for_spanish_equity(
        builder: PassportBuilder) -> None:
    """ES prefix is a discovery signal, never evidence."""
    d = builder.build("ES0113900J37", True).to_dict()
    pt = d["post_trade"]
    assert pt["iberclear_admitted"]["status"] == "not_found"
    assert pt["issuer_csd"]["status"] == "not_found"


def test_preserved_issuer_conflict(builder: PassportBuilder) -> None:
    d = builder.build("IE0007SRI1C7", True).to_dict()
    f = d["identity"]["issuer_lei"]
    assert f["status"] == "conflict"
    assert f["value"] is None
    assert len(f["alternatives"]) >= 2


def test_equity_maturity_not_applicable(
        builder: PassportBuilder) -> None:
    d = builder.build("DE0007164600", True).to_dict()
    f = d["identity"]["maturity_date"]
    assert f["status"] == "not_applicable"
    assert f["rule"]["rule_id"] == "dated_instrument_scope"


def test_unknown_isin_degrades(builder: PassportBuilder) -> None:
    d = builder.build("XSSE2WKP7HV5", True).to_dict()
    assert d["overall_state"] == "unknown"
    for blk in ("identity", "primary_market", "secondary_market",
                "post_trade", "eurosystem_collateral"):
        fields = [v for v in d[blk].values()
                  if isinstance(v, dict) and "status" in v]
        assert fields, blk
        assert all(f["status"] in ("not_found", "not_applicable",
                                   "derived", "reported")
                   for f in fields), blk


def test_no_silent_nulls(builder: PassportBuilder) -> None:
    """Every contract field exists with an explicit status."""
    d = builder.build("XSSE2WKP7HV5", True).to_dict()
    for blk in ("identity", "primary_market", "secondary_market",
                "post_trade", "eurosystem_collateral"):
        for k, v in d[blk].items():
            if k in ("listings", "document_graph",
                     "entity_roles", "identifiers",
                     "eligible_sss", "link_topology",
                     "settlement_locations", "route_assessments",
                     "temporal", "warnings"):
                continue
            assert "status" in v, f"{blk}.{k} has no status"


def test_determinism(builder: PassportBuilder) -> None:
    """Same inputs → same semantic output (timestamps excluded)."""
    a = builder.build("DE000A3LJCB4", True).to_dict()
    b = builder.build("DE000A3LJCB4", True).to_dict()
    a.pop("generated_at")
    b.pop("generated_at")
    assert a == b
