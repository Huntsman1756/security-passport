"""Assertion validator — the release gate.

Walks materialized passports and enforces the field contract:

- reported  → >=1 evidence
- derived   → evidence + rule
- inferred  → evidence + rule + explanation
- conflict  → >=2 incompatible assertions OR a reported upstream
              conflict state (evidence + explanation)
- not_found → searched_sources non-empty

``unsupported_assertions = 0`` is a release requirement, not a
suggestion.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from security_passport.domain.passport import Passport


@dataclass
class ValidationReport:
    passports_checked: int = 0
    fields_checked: int = 0
    unsupported: list[str] = field(default_factory=list)
    reported: int = 0
    derived: int = 0
    inferred: int = 0
    conflicts: int = 0
    not_found: int = 0
    not_applicable: int = 0
    provenance_coverage: float = 0.0

    def ok(self) -> bool:
        return not self.unsupported

    def to_dict(self) -> dict[str, Any]:
        return {
            "passports_checked": self.passports_checked,
            "fields_checked": self.fields_checked,
            "unsupported_assertions": len(self.unsupported),
            "unsupported": self.unsupported,
            "status_counts": {
                "reported": self.reported,
                "derived": self.derived,
                "inferred": self.inferred,
                "conflict": self.conflicts,
                "not_found": self.not_found,
                "not_applicable": self.not_applicable,
            },
            "provenance_coverage": self.provenance_coverage,
        }


def check_passport(p: Passport, report: ValidationReport) -> None:
    report.passports_checked += 1
    positive = 0
    supported_positive = 0
    for block in p.blocks():
        for f in block.all_fields():
            report.fields_checked += 1
            st = f.status.value
            key = {"reported": "reported", "derived": "derived",
                   "inferred": "inferred", "conflict": "conflicts",
                   "not_found": "not_found",
                   "not_applicable": "not_applicable"}[st]
            setattr(report, key, getattr(report, key) + 1)
            for err in f.integrity_errors():
                report.unsupported.append(
                    f"{p.isin}/{block.name}.{f.name}: {err}")
            if st in ("reported", "derived", "inferred"):
                positive += 1
                if f.evidence and (
                        st == "reported" or f.rule is not None):
                    supported_positive += 1
    if positive:
        report.provenance_coverage = (
            (report.provenance_coverage
             * (report.passports_checked - 1)
             + supported_positive / positive)
            / report.passports_checked)
