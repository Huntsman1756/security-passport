"""ISIN validation — structure, length, characters, check digit.

ISO 6166: 2 alpha country + 9 alphanumeric NSIN + 1 check digit
(Luhn over the digit-expanded string). Invalid inputs never reach
providers.
"""
from __future__ import annotations

import re

_ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")


def normalize(raw: str) -> str:
    """Uppercase + strip surrounding whitespace. Structural
    validation is separate — this only normalizes."""
    return raw.strip().upper()


def structural_ok(isin: str) -> bool:
    return bool(_ISIN_RE.match(isin))


def checksum_ok(isin: str) -> bool:
    """Luhn over the digit-expanded string (A=10…Z=35).

    Double every second digit counting from the right starting
    with the digit left of the check digit — i.e. odd indices in
    the reversed traversal."""
    if not structural_ok(isin):
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


def valid(isin: str) -> bool:
    return checksum_ok(isin)
