"""Rule registry — versions append-only, refs fail closed."""
from __future__ import annotations

import pytest

from security_passport.domain.rules import REGISTRY
from security_passport.rules import ref


def test_all_rules_registered() -> None:
    ids = {m.rule_id for m in REGISTRY.all()}
    assert {"instrument_type", "dated_instrument_scope",
            "venue_state", "first_admission",
            "eurosystem_eligibility", "settlement_path",
            "issuer_lei_adjudication", "entity_role",
            "haircut_display"} <= ids


def test_ref_returns_versioned() -> None:
    r = ref("venue_state")
    assert r.rule_id == "venue_state"
    assert r.rule_version >= 1
    assert r.limitations


def test_ref_unknown_fails() -> None:
    with pytest.raises(KeyError):
        ref("nonexistent_rule")
