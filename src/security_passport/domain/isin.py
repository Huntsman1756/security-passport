"""ISIN validation — ISO 6166 via python-stdnum.

ADOPT: `python-stdnum` (LGPL-2.1+, library use only — no code
copied) replaces a hand-rolled Luhn that shipped a real parity
bug. Security Passport keeps only input normalization, error
mapping and domain policy around it.

``checksum_ok`` = full stdnum ISIN validity: structure, check
digit *and* a real ISO 3166 issuance-prefix (an ``XX`` ISIN is
rejected even when its check digit is arithmetically consistent —
correct behaviour, enforced at the boundary).
"""
from __future__ import annotations

import re

from stdnum import isin as _isin
from stdnum import lei as _lei

_ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")


def normalize(raw: str) -> str:
    return raw.strip().upper()


def structural_ok(isin: str) -> bool:
    return bool(_ISIN_RE.match(isin))


def checksum_ok(isin: str) -> bool:
    """Full ISO 6166 validity via python-stdnum — structure, check
    digit, and a real ISO 3166 issuance prefix."""
    if not structural_ok(isin):
        return False
    return _isin.is_valid(isin)


def valid(isin: str) -> bool:
    return checksum_ok(isin)


def lei_ok(lei: str) -> bool:
    """ISO 17442 LEI validity — same dependency."""
    return _lei.is_valid(lei.strip().upper())
