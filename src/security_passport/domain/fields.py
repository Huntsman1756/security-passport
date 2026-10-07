"""PassportField — the adjudicated, displayable unit of truth.

Construction helpers enforce the invariants the release gate
checks (``reported`` needs evidence, ``derived`` needs evidence +
rule, ``inferred`` needs evidence + rule + explanation,
``conflict`` needs ≥2 assertions, ``not_found`` needs searched
sources). A field that violates them is a bug that fails
validation, not a rendering choice.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from security_passport.domain.evidence import Assertion, EvidenceRef
from security_passport.domain.rules import RuleRef
from security_passport.domain.status import (
    FieldStatus,
    QualityFlag,
    SourceTimeSemantics,
    TemporalBasis,
)


@dataclass(frozen=True)
class TemporalCoverage:
    """Honest temporal-basis declaration (ADR-005)."""

    basis: TemporalBasis
    coverage_start: str | None = None
    coverage_end: str | None = None
    left_censored: bool = False
    source_time_semantics: SourceTimeSemantics = (
        SourceTimeSemantics.RETRIEVAL_TIME)

    def to_dict(self) -> dict[str, Any]:
        return {
            "basis": self.basis.value,
            "coverage_start": self.coverage_start,
            "coverage_end": self.coverage_end,
            "left_censored": self.left_censored,
            "source_time_semantics": self.source_time_semantics.value,
        }


@dataclass
class PassportField:
    """One displayed value with full provenance."""

    name: str
    value: Any
    status: FieldStatus
    evidence: list[EvidenceRef] = field(default_factory=list)
    rule: RuleRef | None = None
    quality_flags: list[QualityFlag] = field(default_factory=list)
    temporal: TemporalCoverage | None = None
    alternatives: list[Assertion] = field(default_factory=list)
    searched_sources: list[str] = field(default_factory=list)
    explanation: str = ""
    raw_value: Any = None
    unit: str = ""

    # ---- construction helpers (enforce invariants) ----

    @classmethod
    def reported(cls, name: str, value: Any,
                 evidence: list[EvidenceRef],
                 **kw: Any) -> PassportField:
        assert evidence, f"reported field {name} requires evidence"
        return cls(name=name, value=value,
                   status=FieldStatus.REPORTED,
                   evidence=list(evidence), **kw)

    @classmethod
    def derived(cls, name: str, value: Any,
                evidence: list[EvidenceRef], rule: RuleRef,
                **kw: Any) -> PassportField:
        assert evidence, f"derived field {name} requires evidence"
        return cls(name=name, value=value,
                   status=FieldStatus.DERIVED,
                   evidence=list(evidence), rule=rule, **kw)

    @classmethod
    def inferred(cls, name: str, value: Any,
                 evidence: list[EvidenceRef], rule: RuleRef,
                 explanation: str,
                 **kw: Any) -> PassportField:
        assert evidence, f"inferred field {name} requires evidence"
        assert explanation, \
            f"inferred field {name} requires an explanation"
        return cls(name=name, value=value,
                   status=FieldStatus.INFERRED,
                   evidence=list(evidence), rule=rule,
                   explanation=explanation, **kw)

    @classmethod
    def conflict(cls, name: str,
                 assertions: list[Assertion],
                 explanation: str = "",
                 **kw: Any) -> PassportField:
        assert len(assertions) >= 2, \
            f"conflict field {name} requires >= 2 assertions"
        return cls(name=name, value=None,
                   status=FieldStatus.CONFLICT,
                   evidence=[a.evidence for a in assertions],
                   alternatives=list(assertions),
                   explanation=explanation, **kw)

    @classmethod
    def not_found(cls, name: str,
                  searched_sources: list[str],
                  explanation: str = "",
                  **kw: Any) -> PassportField:
        assert searched_sources, \
            f"not_found field {name} must name searched sources"
        return cls(name=name, value=None,
                   status=FieldStatus.NOT_FOUND,
                   searched_sources=list(searched_sources),
                   explanation=explanation, **kw)

    @classmethod
    def not_applicable(cls, name: str, rule: RuleRef,
                       explanation: str = "",
                       **kw: Any) -> PassportField:
        return cls(name=name, value=None,
                   status=FieldStatus.NOT_APPLICABLE,
                   rule=rule, explanation=explanation, **kw)

    # ---- integrity check (mirrors the release gate) ----

    def integrity_errors(self) -> list[str]:
        """Violations of the field contract — any nonempty result
        is an unsupported assertion."""
        errs: list[str] = []
        if self.status is FieldStatus.REPORTED and not self.evidence:
            errs.append("reported without evidence")
        if self.status is FieldStatus.DERIVED and (
                not self.evidence or self.rule is None):
            errs.append("derived requires evidence + rule")
        if self.status is FieldStatus.INFERRED and (
                not self.evidence or self.rule is None
                or not self.explanation):
            errs.append("inferred requires evidence + rule "
                        "+ explanation")
        if self.status is FieldStatus.CONFLICT and not (
                len(self.alternatives) >= 2
                or (self.evidence and self.explanation)):
            errs.append("conflict requires >= 2 assertions or "
                        "a reported upstream conflict state "
                        "(evidence + explanation)")
        if self.status is FieldStatus.NOT_FOUND and not (
                self.searched_sources):
            errs.append("not_found requires searched_sources")
        for e in self.evidence:
            if not (e.provider and e.dataset):
                errs.append("evidence missing provider/dataset")
        return errs

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "value": self.value,
            "status": self.status.value,
            "evidence": [e.to_dict() for e in self.evidence],
            "quality_flags": [f.value for f in self.quality_flags],
            "searched_sources": list(self.searched_sources),
        }
        if self.rule is not None:
            out["rule"] = self.rule.to_dict()
        if self.temporal is not None:
            out["temporal"] = self.temporal.to_dict()
        if self.alternatives:
            out["alternatives"] = [
                {"value": a.value,
                 "role": a.role,
                 "evidence": a.evidence.to_dict()}
                for a in self.alternatives]
        if self.explanation:
            out["explanation"] = self.explanation
        if self.raw_value is not None:
            out["raw_value"] = self.raw_value
        if self.unit:
            out["unit"] = self.unit
        return out
