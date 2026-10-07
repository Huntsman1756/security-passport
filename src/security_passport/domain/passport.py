"""Passport root contract — schema_version 1.

The JSON shape emitted by the API, CLI ``--json``, and consumed by
the frontend. Frozen per schema version; additive fields require a
contract note, breaking changes a version bump.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from security_passport.domain.fields import PassportField, TemporalCoverage

SCHEMA_VERSION = "1"


@dataclass
class PassportBlock:
    """One of the five named sections."""

    name: str
    fields: dict[str, PassportField] = field(default_factory=dict)
    collections: dict[str, Any] = field(default_factory=dict)
    temporal: TemporalCoverage | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            k: f.to_dict() for k, f in self.fields.items()}
        for k, v in self.collections.items():
            out[k] = v
        if self.temporal is not None:
            out["temporal"] = self.temporal.to_dict()
        if self.warnings:
            out["warnings"] = list(self.warnings)
        return out

    def all_fields(self) -> list[PassportField]:
        """Materialized fields — collections may embed
        PassportField dicts already serialized."""
        return list(self.fields.values())


@dataclass
class Passport:
    """The root object — one ISIN, one generation pair, five blocks."""

    isin: str
    generated_at: str
    generation: str
    openinstrument_generation: str
    overall_state: str
    identity: PassportBlock
    primary_market: PassportBlock
    secondary_market: PassportBlock
    post_trade: PassportBlock
    eurosystem_collateral: PassportBlock
    temporal_coverage: dict[str, Any]
    source_summary: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)
    passport_id: str = ""
    valid_checksum: bool = True
    as_of: str | None = None

    def blocks(self) -> list[PassportBlock]:
        return [self.identity, self.primary_market,
                self.secondary_market, self.post_trade,
                self.eurosystem_collateral]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "passport_id": self.passport_id,
            "isin": self.isin,
            "valid_checksum": self.valid_checksum,
            "generated_at": self.generated_at,
            "generation": self.generation,
            "openinstrument_generation": self.openinstrument_generation,
            "overall_state": self.overall_state,
            **({"query": {"as_of": self.as_of}}
               if self.as_of else {}),
            "identity": self.identity.to_dict(),
            "primary_market": self.primary_market.to_dict(),
            "secondary_market": self.secondary_market.to_dict(),
            "post_trade": self.post_trade.to_dict(),
            "eurosystem_collateral":
                self.eurosystem_collateral.to_dict(),
            "temporal_coverage": self.temporal_coverage,
            "source_summary": self.source_summary,
            "warnings": self.warnings,
        }

    def unsupported_assertions(self) -> list[str]:
        """Release-gate scan: every materialized field must satisfy
        its status contract. Returns ``block.field: error`` strings."""
        bad: list[str] = []
        for block in self.blocks():
            for f in block.all_fields():
                for err in f.integrity_errors():
                    bad.append(f"{block.name}.{f.name}: {err}")
        return bad
