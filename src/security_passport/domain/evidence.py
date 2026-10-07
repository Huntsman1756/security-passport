"""Evidence references — the unit that makes an assertion checkable.

An ``EvidenceRef`` must let a reviewer reach the concrete source
record or document: provider + dataset + record/document identity +
artifact locator + timestamps. ``source = ESMA`` alone is never
sufficient.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvidenceRef:
    """Pointer to the concrete public evidence behind a claim.

    ``raw_value`` preserves the verbatim source value before any
    transformation — sentinel handling must never destroy it.
    ``upstream_*`` fields carry OpenInstrument's own provenance
    (artifact sha256 + record locator) when the evidence is served
    transitively.
    """

    provider: str
    dataset: str
    record_id: str
    artifact_id: str = ""
    source_locator: str = ""
    retrieved_at: str = ""
    published_at: str = ""
    effective_at: str = ""
    raw_value: Any = None
    parser_version: str = ""
    transformations: tuple[str, ...] = ()
    upstream_provider: str = ""
    upstream_artifact: str = ""
    upstream_locator: str = ""

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "provider": self.provider,
            "dataset": self.dataset,
            "record_id": self.record_id,
            "artifact_id": self.artifact_id,
            "source_locator": self.source_locator,
            "retrieved_at": self.retrieved_at,
            "published_at": self.published_at,
            "effective_at": self.effective_at,
            "raw_value": self.raw_value,
            "parser_version": self.parser_version,
            "transformations": list(self.transformations),
        }
        if self.upstream_provider:
            out["upstream"] = {
                "provider": self.upstream_provider,
                "artifact": self.upstream_artifact,
                "locator": self.upstream_locator,
            }
        return out


@dataclass(frozen=True)
class Assertion:
    """One provider's verbatim claim about one field.

    Assertions are never adjudicated at acquisition — conflicts are
    resolved (or preserved) at projection time, so the losing side
    of a disagreement is never destroyed.
    """

    value: Any
    evidence: EvidenceRef
    observed_at: str = ""
    role: str = ""  # entity role qualifier: issuer/offeror/guarantor/…
    notes: str = ""


@dataclass
class FieldInput:
    """All assertions gathered for one field before adjudication."""

    name: str
    assertions: list[Assertion] = field(default_factory=list)
    searched_sources: list[str] = field(default_factory=list)

    def add(self, value: Any, evidence: EvidenceRef,
            role: str = "", observed_at: str = "",
            notes: str = "") -> Assertion:
        a = Assertion(value=value, evidence=evidence, role=role,
                      observed_at=observed_at, notes=notes)
        self.assertions.append(a)
        return a
