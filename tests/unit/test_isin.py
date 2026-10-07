"""ISIN validation — structure + Luhn checksum."""
from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from security_passport.domain.isin import (
    checksum_ok,
    normalize,
    structural_ok,
    valid,
)

# verified against real instruments
VALID = [
    "DE000A3LJCB4", "XS2081615473", "DE0007164600", "ES0113900J37",
    "ES0000101966", "IE0007SRI1C7", "LU0003549028", "US0378331005",
    "XSSE2WKP7HV5",
]
INVALID = [
    "DE000A3LJCB0",   # bad check digit
    "XX0000000001",   # valid shape, wrong check
    "DE000A3LJCB",    # too short
    "DE000A3LJCB44",  # too long
    "D3000A3LJCB4",   # digit in country code
    "DE000A3LJCBA",   # letter check digit
    "", "DE", "XX",
]


@pytest.mark.parametrize("isin", VALID)
def test_valid_isins(isin: str) -> None:
    assert structural_ok(isin)
    assert checksum_ok(isin)
    assert valid(isin)


@pytest.mark.parametrize("isin", INVALID)
def test_invalid_isins(isin: str) -> None:
    assert not valid(isin)


def test_normalize_uppercases() -> None:
    assert normalize("  de000a3ljcb4 ") == "DE000A3LJCB4"


def test_lowercase_input_normalizes_then_validates() -> None:
    assert valid(normalize("de000a3ljcb4"))


@given(st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
               min_size=0, max_size=20))
def test_property_never_crashes(s: str) -> None:
    valid(s)
    checksum_ok(s)


@given(st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
               min_size=12, max_size=12))
def test_property_12char_never_crashes(s: str) -> None:
    checksum_ok(s)


def test_mutation_detection() -> None:
    """Single-char mutation of a valid ISIN almost always breaks
    the checksum — test a few deterministic swaps."""
    base = "DE000A3LJCB4"
    for i, ch in ((2, "1"), (5, "Z"), (10, "Z")):
        mutated = base[:i] + ch + base[i + 1:]
        assert not checksum_ok(mutated), mutated
