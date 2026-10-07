"""Temporal layer — sentinel-aware date normalization.

FIRDS uses ``9999-12-31`` sentinels for "not provided" dates and
maturity/termination dates as substitute values for unknown
admission dates (spec §16, §30). Raw values are never destroyed:
normalization returns ``(normalized, raw, flags)``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from security_passport.domain.status import QualityFlag

# FIRDS sentinel years treated as "unknown" — 9999-12-31 is the
# documented default; treat the whole 9xxx decade as sentinel for
# safety but flag semantic uncertainty.
_SENTINEL_YEAR_RE = re.compile(r"^9\d{3}-")

# Real-world FIRDS observations also carry time-of-day noise
# (e.g. "2030-07-17T23:59:59.999Z" as a maturity-like termination).
_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")


@dataclass
class NormalizedDate:
    """Result of sentinel-aware normalization.

    ``value`` is the ISO date (YYYY-MM-DD) or None when the source
    value encodes "unknown". ``raw`` always preserves the verbatim
    input. ``end_of_day`` marks values like ``T23:59:59`` which are
    conventionally "day-level" dates, not instants."""

    value: str | None
    raw: Any
    flags: list[QualityFlag] = field(default_factory=list)
    is_sentinel: bool = False
    end_of_day: bool = False


def normalize_firds_date(raw: Any) -> NormalizedDate:
    """Normalize one FIRDS date/datetime value.

    - None/empty -> clean null
    - 9xxx-year sentinels -> None + source_default_value flag
    - ISO datetimes -> date portion (end_of_day marked for
      T23:59:5x/T23:59:59.999 style closers)
    """
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return NormalizedDate(value=None, raw=raw)
    s = str(raw).strip()
    if _SENTINEL_YEAR_RE.match(s):
        return NormalizedDate(
            value=None, raw=raw, is_sentinel=True,
            flags=[QualityFlag.SOURCE_DEFAULT_VALUE])
    m = _DATE_RE.match(s)
    if not m:
        return NormalizedDate(
            value=None, raw=raw,
            flags=[QualityFlag.POSSIBLE_SOURCE_DEFAULT])
    end_of_day = bool(re.search(
        r"T2[13]:5[89]", s))  # T23:58/59 or T22:59 closers
    return NormalizedDate(value=f"{m.group(1)}-{m.group(2)}-"
                                f"{m.group(3)}",
                          raw=raw, end_of_day=end_of_day)


def min_real_date(dates: list[NormalizedDate]) -> NormalizedDate | None:
    """Earliest non-sentinel normalized date, or None.

    ``first_admission = min(dates)`` is only legal after sentinel
    removal — the verbatim raws of every candidate stay attached to
    the caller's evidence list."""
    real = [d for d in dates if d.value is not None]
    if not real:
        return None
    best = min(real, key=lambda d: d.value or "")
    merged = list(best.flags)
    if any(d.is_sentinel for d in dates) and (
            QualityFlag.SOURCE_DEFAULT_VALUE not in merged):
            merged.append(QualityFlag.SOURCE_DEFAULT_VALUE)
    return NormalizedDate(value=best.value, raw=best.raw,
                          flags=merged, end_of_day=best.end_of_day)
