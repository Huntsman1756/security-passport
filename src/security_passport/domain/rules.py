"""Versioned derivation/inference rules.

Every ``derived`` or ``inferred`` field must name the rule that
produced it. Rules are registered, versioned, and documented with
their legal/operational basis and limitations — a transformation
hidden inside an undocumented function is a defect.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuleRef:
    """Reference to the versioned rule behind a derived/inferred
    field. ``inputs`` records which assertions fed the rule so the
    explanation is materialized, not recomputed."""

    rule_id: str
    rule_version: int
    inputs: tuple[dict[str, Any], ...] = ()
    basis: str = ""
    limitations: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "inputs": list(self.inputs),
            "basis": self.basis,
            "limitations": self.limitations,
        }


@dataclass(frozen=True)
class RuleMeta:
    """Registered rule metadata — documentation surface."""

    rule_id: str
    version: int
    name: str
    basis: str
    limitations: str


class RuleRegistry:
    """In-code registry; versions are append-only.

    A behaviour change requires a version bump so historical
    passports keep pointing at the rule that produced them.
    """

    def __init__(self) -> None:
        self._rules: dict[str, RuleMeta] = {}

    def register(self, meta: RuleMeta) -> None:
        key = f"{meta.rule_id}.v{meta.version}"
        if key in self._rules:
            raise ValueError(f"duplicate rule registration: {key}")
        self._rules[key] = meta

    def get(self, rule_id: str, version: int | None = None
            ) -> RuleMeta:
        if version is None:
            versions = [m for k, m in self._rules.items()
                        if m.rule_id == rule_id]
            if not versions:
                raise KeyError(f"unregistered rule: {rule_id}")
            return max(versions, key=lambda m: m.version)
        try:
            return self._rules[f"{rule_id}.v{version}"]
        except KeyError:
            raise KeyError(
                f"unregistered rule: {rule_id}.v{version}") from None

    def all(self) -> list[RuleMeta]:
        return sorted(self._rules.values(),
                      key=lambda m: (m.rule_id, m.version))


REGISTRY = RuleRegistry()


def ref(rule_id: str, inputs: tuple[dict[str, Any], ...] = (),
        version: int | None = None) -> RuleRef:
    """Build a RuleRef against the registry — fails closed on
    unregistered rule ids."""
    meta = REGISTRY.get(rule_id, version)
    return RuleRef(rule_id=meta.rule_id, rule_version=meta.version,
                   inputs=inputs, basis=meta.basis,
                   limitations=meta.limitations)
