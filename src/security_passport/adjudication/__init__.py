"""Adjudication — field-level conflict policy.

There is no global source hierarchy (docs/domain/conflict-policy.md);
authority is per-field. This module hosts the small policy helpers
the builder consults when two assertions disagree.
"""
from __future__ import annotations

from typing import Any

# Per-field authority — a policy may name a primary provider, but
# disagreement is preserved as alternatives regardless.
FIELD_AUTHORITIES: dict[str, list[str]] = {
    "cfi": ["esma_firds"],
    "fisn": ["esma_firds"],
    "notional_currency": ["esma_firds"],
    "issuer_lei": ["esma_firds", "gleif"],
    "prospectus_found": ["esma_priii"],
    "eligible": ["ecb_eligible_assets"],
    "issuer_sss": ["ecb_eligible_assets"],
}


def normalize_for_compare(value: Any) -> str:
    """Comparison normalization — LEIs uppercase, whitespace
    collapsed, numbers decimal-normalized. Never applied to the
    stored value, only to conflict detection."""
    if value is None:
        return ""
    s = str(value).strip()
    if len(s) == 20 and s.isalnum():  # LEI-shaped
        return s.upper()
    try:
        from decimal import Decimal
        return format(Decimal(s).normalize(), "f")
    except Exception:
        return " ".join(s.split()).upper()
