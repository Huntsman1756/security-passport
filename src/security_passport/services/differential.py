"""Differential comparison between Security Passport fields and
upstream assertions — drift detection, not silent resolution.

Every discrepancy is classified; only UNEXPLAINED is a failure:

- SAME                     values equal after normalization
- EXPECTED_TRANSFORMATION  documented shape change (dates, naming)
- SOURCE_VERSION_SKEW      inputs differ (different snapshots)
- SEMANTIC_DIFFERENCE      same source, different meaning
- BUG                      provable pipeline defect
- UNEXPLAINED              none of the above — release-blocking
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Verdict(StrEnum):
    SAME = "SAME"
    EXPECTED_TRANSFORMATION = "EXPECTED_TRANSFORMATION"
    SOURCE_VERSION_SKEW = "SOURCE_VERSION_SKEW"
    SEMANTIC_DIFFERENCE = "SEMANTIC_DIFFERENCE"
    BUG = "BUG"
    UNEXPLAINED = "UNEXPLAINED"


@dataclass
class FieldDiff:
    field: str
    ours: Any
    theirs: Any
    verdict: Verdict
    note: str = ""


@dataclass
class DiffReport:
    subject: str
    diffs: list[FieldDiff] = field(default_factory=list)

    def add(self, d: FieldDiff) -> None:
        self.diffs.append(d)

    @property
    def blocking(self) -> list[FieldDiff]:
        return [d for d in self.diffs
                if d.verdict in (Verdict.BUG, Verdict.UNEXPLAINED)]

    def ok(self) -> bool:
        return not self.blocking


def _norm_str(v: Any) -> str:
    return "" if v is None else str(v).strip()


def compare_ecb_asset(
        isin: str,
        ours: dict[str, Any] | None,
        ours_snapshot: str,
        theirs: dict[str, Any] | None,
        theirs_version: str) -> DiffReport:
    """SP eligible-assets row vs OpenInstrument ecb_eligible row.

    ``ours``/``theirs`` are normalized row dicts (or None when the
    ISIN is absent from that snapshot)."""
    rep = DiffReport(subject=f"ecb_eligible/{isin}")
    if ours is None and theirs is None:
        rep.add(FieldDiff("presence", False, False, Verdict.SAME))
        return rep
    if (ours is None) != (theirs is None):
        verdict = (Verdict.SOURCE_VERSION_SKEW
                   if ours_snapshot != theirs_version
                   else Verdict.UNEXPLAINED)
        rep.add(FieldDiff(
            "presence", ours is not None, theirs is not None,
            verdict,
            note=f"snapshots {ours_snapshot} vs {theirs_version}"))
        return rep
    assert ours is not None and theirs is not None

    same_snapshot = ours_snapshot == theirs_version
    skew = Verdict.SAME if same_snapshot else \
        Verdict.SOURCE_VERSION_SKEW

    # haircut category / asset type / issuer csd: code fields —
    # same value or a real discrepancy
    for name, ok, tk in (
            ("haircut_category", "haircut_category",
             "haircut_category"),
            ("asset_type", "asset_type", "asset_type"),
            ("issuer_csd", "issuer_csd", "issuer_csd")):
        ov, tv = _norm_str(ours.get(ok)), _norm_str(theirs.get(tk))
        v = (Verdict.SAME if ov == tv else
             (skew if not same_snapshot else Verdict.UNEXPLAINED))
        rep.add(FieldDiff(name, ov or None, tv or None, v,
                          "" if v is Verdict.SAME else
                          f"snapshots {ours_snapshot}/"
                          f"{theirs_version}"))

    # haircut: Decimal-as-string vs float-ish upstream
    o_h = ours.get("haircut")
    t_h = theirs.get("haircut")
    same_h = _norm_str(o_h) == _norm_str(t_h) or (
        o_h is not None and t_h is not None
        and str(o_h).rstrip("0").rstrip(".")
        == str(t_h).rstrip("0").rstrip("."))
    rep.add(FieldDiff(
        "haircut", o_h, t_h,
        Verdict.SAME if same_h else
        (skew if not same_snapshot else Verdict.UNEXPLAINED)))

    # dates: SP normalizes to ISO — expected transformation when
    # the same date appears in a different shape
    for name in ("issuance_date", "maturity_date"):
        ov = _norm_str(ours.get(name))
        tv = _norm_str(theirs.get(name))
        if ov == tv:
            v = Verdict.SAME
        elif ov and tv and ov.replace("-", "") == \
                tv.replace("-", "").replace("/", ""):
            v = Verdict.EXPECTED_TRANSFORMATION
        else:
            v = (skew if not same_snapshot else
                 Verdict.UNEXPLAINED)
        rep.add(FieldDiff(name, ov or None, tv or None, v))

    # names: case/whitespace-normalize → EXPECTED_TRANSFORMATION
    for name in ("issuer_name",):
        ov = _norm_str(ours.get(name))
        tv = _norm_str(theirs.get(name))
        if ov == tv:
            v = Verdict.SAME
        elif ov.upper() == tv.upper() or " ".join(
                ov.split()) == " ".join(tv.split()):
            v = Verdict.EXPECTED_TRANSFORMATION
        else:
            v = skew
        rep.add(FieldDiff(name, ov or None, tv or None, v))
    return rep
