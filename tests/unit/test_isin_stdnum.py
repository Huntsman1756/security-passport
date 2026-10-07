"""Differential tests: retired custom Luhn vs python-stdnum.

The legacy algorithm is preserved verbatim here as an oracle for
the differential suite — after this suite demonstrates agreement
on all shared cases, the custom implementation was removed from
``domain/isin.py``. Note the deliberate semantic difference:
stdnum additionally enforces a real ISO 3166 issuance prefix, so
cases like ``XX0000000002`` (checksum-consistent, invalid prefix)
diverge by design.
"""
from __future__ import annotations

import re

from hypothesis import given
from hypothesis import strategies as st

from security_passport.domain.isin import (
    checksum_ok,
    valid,
)

_ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")


def legacy_checksum(isin: str) -> bool:
    """The retired implementation — kept only as a test oracle."""
    if not _ISIN_RE.match(isin):
        return False
    digits = "".join(str(ord(c) - 55) if c.isalpha() else c
                     for c in isin)
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


# real prefix ISINs where both implementations must agree
SHARED_VALID = [
    "DE000A3LJCB4", "XS2081615473", "DE0007164600", "ES0113900J37",
    "ES0000101966", "IE0007SRI1C7", "LU0003549028", "US0378331005",
    "XSSE2WKP7HV5", "LUJYU0POJ9N4", "DEI313MSF2D2",
]

SHARED_INVALID = [
    "DE000A3LJCB0", "US0378331006", "XS2081615474",
    "DE0007164609", "ES0113900J36", "IE0007SRI1C0",
]


def test_agree_on_valid() -> None:
    for s in SHARED_VALID:
        assert valid(s)
        assert legacy_checksum(s)


def test_agree_on_invalid() -> None:
    for s in SHARED_INVALID:
        assert not valid(s)
        assert not legacy_checksum(s)


def test_prefix_semantic_difference() -> None:
    """stdnum rejects XX/ZZ prefixes that legacy Luhn accepted —
    the stricter semantics are correct."""
    assert legacy_checksum("XX0000000002")  # arithmetic passes
    assert not valid("XX0000000002")        # but prefix is invalid
    assert not valid("ZZ0000000008")


@given(st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
               min_size=12, max_size=12))
def test_differential_property(s: str) -> None:
    """On every 12-char input: stdnum valid ⇒ legacy valid.
    (Legacy may accept non-country prefixes; never the reverse.)"""
    if valid(s):
        assert legacy_checksum(s), s


@given(st.text(min_size=0, max_size=20))
def test_never_crashes(s: str) -> None:
    checksum_ok(s)


def test_check_digit_math_spotcheck() -> None:
    """DE000A3LJCB + checkdigit — verified by hand twice."""
    from stdnum.isin import calc_check_digit
    assert calc_check_digit("DE000A3LJCB") == "4"
    assert calc_check_digit("US037833100") == "5"
