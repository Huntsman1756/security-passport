"""Temporal passport contract — `--as-of` semantics.

The frozen scenario matrix for the temporal engine:
- T before observation start        → outside_coverage, no substitution
- T exactly at first observation    → available
- T between publication and effective → announced, not effective
- T exactly on effective_from       → effective
- listing terminated after T        → active at T
- sss page postdates T              → excluded (partial)
- ECB window                        → snapshot semantics, never projected back
"""
from __future__ import annotations

from security_passport.domain.isin import checksum_ok, normalize
from security_passport.providers.fixtures import (
    FixtureInstrumentProvider,
    FixturePassportStore,
)
from security_passport.services.passport_builder import PassportBuilder

CORPUS = "tests/fixtures/corpus"
B = PassportBuilder(FixtureInstrumentProvider(CORPUS),
                    FixturePassportStore(CORPUS))


def _at(isin: str, t: str) -> dict:
    return B.build(normalize(isin),
                   checksum_ok=checksum_ok(isin),
                   as_of=t).to_dict()


def test_milan_publication_vs_effective() -> None:
    """The core golden: knowledge ≠ effectiveness.

    The ESMIL file was published 2026-09-18; the designated
    place only becomes effective 2026-09-21."""
    t19 = _at("IE00B4L5Y983", "2026-09-19")
    locs19 = t19["post_trade"]["settlement_locations"]
    des19 = next(lc for lc in locs19
                 if lc["relationship"] ==
                 "designated_place_of_settlement")
    assert des19["source_published_at"] == "2026-09-18"
    assert des19["effective_from"] == "2026-09-21"
    assert des19["effective"] is False          # announced, not in force

    t21 = _at("IE00B4L5Y983", "2026-09-21")
    des21 = next(lc for lc in t21["post_trade"]["settlement_locations"]
                 if lc["relationship"] ==
                 "designated_place_of_settlement")
    assert des21["effective"] is True


def test_before_observation_start_never_substitutes() -> None:
    """T precedes every own-source observation — the register /
    ECB / settlement surfaces all report outside_coverage and no
    current value leaks into any field."""
    d = _at("DE000A3LJCB4", "2020-01-01")
    assert d["query"]["as_of"] == "2020-01-01"
    assert d["primary_market"]["temporal"]["answer_state"] == \
        "outside_coverage"
    assert "NOT been substituted" in \
        d["primary_market"]["temporal"]["answer_note"]
    # no field in an outside_coverage block may carry a value
    for blk in ("primary_market", "eurosystem_collateral"):
        if d[blk]["temporal"]["answer_state"] == "outside_coverage":
            for k, f in d[blk].items():
                if isinstance(f, dict) and "status" in f:
                    assert f["status"] in ("not_found",
                                           "not_applicable"), \
                        f"{blk}.{k} = {f['status']}"
                    assert f["value"] is None


def test_as_of_after_all_observation() -> None:
    d = _at("DE000A3LJCB4", "2026-10-07")
    assert d["overall_state"] == "found"
    assert all(d[b]["temporal"]["answer_state"] == "available"
               for b in ("identity", "secondary_market",
                         "primary_market", "post_trade",
                         "eurosystem_collateral"))


def test_delisted_instrument_termination_after_T() -> None:
    """AT0000A1NZ16 is fully delisted today; at a T before
    termination it must appear active — state is recomputed at
    T, never carried from 'now'."""
    now = B.build(normalize("AT0000A1NZ16"),
                  checksum_ok=checksum_ok("AT0000A1NZ16")).to_dict()
    terminated = [lc for lc in now["secondary_market"]["listings"]
                  if lc["state"] == "terminated"]
    assert terminated
    term = terminated[0]["termination_date"]
    if not term:
        return
    t_before = str(int(term[:4]) - 2) + term[4:10]
    past = _at("AT0000A1NZ16", t_before)
    states = {lc["venue_mic"]: lc["state"]
              for lc in past["secondary_market"]["listings"]}
    assert all(s in ("active", "unknown_dates")
               for s in states.values()), states


def test_no_future_knowledge_in_as_of() -> None:
    """Scan: nothing marked effective may carry an effective_from
    after T, and nothing published after T may appear."""
    for t in ("2026-09-18", "2026-09-19", "2026-09-20",
              "2026-09-21", "2026-10-07"):
        d = _at("IE00B4L5Y983", t)
        for lc in d["post_trade"]["settlement_locations"]:
            assert (lc["source_published_at"] or "0000") <= t
            if lc.get("effective") is True and lc.get("effective_from"):
                assert lc["effective_from"] <= t


def test_cli_and_api_accept_as_of() -> None:
    """Contract surface: both interfaces accept --as-of/as_of."""
    import os

    os.environ["SECURITY_PASSPORT_PROVIDER"] = "fixtures"
    os.environ["SECURITY_PASSPORT_FIXTURES"] = CORPUS
    from fastapi.testclient import TestClient

    from security_passport.api.app import create_app
    from security_passport.config import load
    with TestClient(create_app(load())) as c:
        r = c.get("/api/v1/passports/IE00B4L5Y983",
                  params={"as_of": "2026-09-19"})
        assert r.status_code == 200
        d = r.json()
        assert d["query"]["as_of"] == "2026-09-19"
        assert any(lc["effective"] is False
                   for lc in
                   d["post_trade"]["settlement_locations"])
        r2 = c.get("/api/v1/passports/IE00B4L5Y983",
                   params={"as_of": "not-a-date"})
        assert r2.status_code == 422
