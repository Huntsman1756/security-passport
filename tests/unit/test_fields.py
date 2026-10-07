"""PassportField invariant enforcement — the contract the release
gate checks."""
from __future__ import annotations

import pytest

from security_passport.domain.evidence import Assertion, EvidenceRef
from security_passport.domain.fields import PassportField
from security_passport.domain.status import FieldStatus

EV = EvidenceRef(provider="p", dataset="d", record_id="r")


def test_reported_requires_evidence() -> None:
    with pytest.raises(AssertionError):
        PassportField.reported("f", "v", [])


def test_derived_requires_rule() -> None:
    from security_passport.domain.rules import RuleRef
    f = PassportField.derived("f", "v", [EV],
                            RuleRef(rule_id="r", rule_version=1))
    assert not f.integrity_errors()


def test_conflict_requires_two_or_reported_state() -> None:
    f = PassportField(name="f", value=None,
                      status=FieldStatus.CONFLICT)
    assert f.integrity_errors()
    f2 = PassportField.conflict(
        "f", [Assertion(value="a", evidence=EV),
              Assertion(value="b", evidence=EV)])
    assert not f2.integrity_errors()


def test_not_found_requires_searched_sources() -> None:
    with pytest.raises(AssertionError):
        PassportField.not_found("f", [])
    f = PassportField.not_found("f", ["src"])
    assert not f.integrity_errors()


def test_field_serializes() -> None:
    f = PassportField.reported("cfi", "DBFUGB", [EV])
    d = f.to_dict()
    assert d["value"] == "DBFUGB"
    assert d["status"] == "reported"
    assert d["evidence"][0]["provider"] == "p"
