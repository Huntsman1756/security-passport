"""Registered derivation/inference rules — append-only versions.

Each RuleMeta documents its operational/legal basis and its
limitations. A behaviour change requires a version bump; historical
passports keep referencing the version that produced them.
"""
from __future__ import annotations

from security_passport.domain.rules import REGISTRY, RuleMeta


def _register() -> None:
    r = REGISTRY.register
    r(RuleMeta(
        rule_id="instrument_type", version=1,
        name="CFI letter → instrument class",
        basis=("ISO 10962 CFI first letter maps to the asset "
               "category (C collective, D debt, E equity, "
               "F futures, H structured, I other, J options, "
               "O other/OTC, R referential, S swaps)."),
        limitations=("CFI is source-reported; the class label is a "
                     "deterministic decode, not an independent "
                     "classification.")))
    r(RuleMeta(
        rule_id="dated_instrument_scope", version=1,
        name="Maturity applicability by CFI class",
        basis=("Debt instruments (CFI D*) carry a maturity date; "
               "equities (E*) and collective investment shares "
               "(C*) are undated by construction."),
        limitations=("Fund-of-funds share classes and perpetual "
                     "debt are edge cases — perpetual debt reports "
                     "no maturity as reported absence, not N/A.")))
    r(RuleMeta(
        rule_id="venue_state", version=1,
        name="Listing lifecycle from FIRDS venue record",
        basis=("FIRDS TradgVnRltdAttrbts: a venue record with a "
               "termination date at/before the snapshot date is "
               "terminated; with admission/first-trade dates and "
               "no termination it is active; with only future "
               "dates it is pending."),
        limitations=("A record disappearing from FULINS between "
                     "snapshots is NOT a termination — upstream "
                     "history is required to distinguish. Sentinel "
                     "dates are excluded before comparison.")))
    r(RuleMeta(
        rule_id="first_admission", version=1,
        name="Earliest normalized admission evidence",
        basis=("Earliest non-sentinel date across "
               "admission_approval_date / admission_request_date / "
               "first_trade_date of all venue records; each "
               "candidate keeps its verbatim raw value."),
        limitations=("FIRDS unknown-date semantics may substitute "
                     "maturity/termination as defaults — flagged "
                     "as possible_source_default when suspicious; "
                     "left-censored before the upstream baseline.")))
    r(RuleMeta(
        rule_id="eurosystem_eligibility", version=1,
        name="ECB eligible-assets presence → eligibility",
        basis=("The ECB ea_csv is the authoritative enumeration "
               "of eligible marketable assets for the snapshot "
               "day. Presence ⇒ eligible; absence ⇒ not eligible "
               "as of that snapshot."),
        limitations=("Snapshot-scoped: says nothing about "
                     "eligibility before/after the snapshot. The "
                     "dataset does not distinguish 'never "
                     "eligible' from 'not yet ingested history'.")))
    r(RuleMeta(
        rule_id="settlement_path", version=1,
        name="Evidence-only settlement assessment",
        basis=("Eurosystem collateral framework: an asset is "
               "settleable through an SSS path only where the "
               "issuer SSS plus instrument-level admission/"
               "holding evidence in the investor SSS exists. "
               "SSS-link topology alone never establishes "
               "instrument settleability."),
        limitations=("v0.1 has no instrument-level investor-SSS "
                     "source; possible_paths therefore stays "
                     "not_found even where a plausible topology "
                     "exists. Absence of evidence is stated, "
                     "never resolved into an assertion.")))
    r(RuleMeta(
        rule_id="issuer_lei_adjudication", version=1,
        name="Upstream issuer-LEI state passthrough",
        basis=("OpenInstrument adjudicates FIRDS field 5 vs "
               "GLEIF ISIN-LEI with per-provider assertions; "
               "corroborated/single_source map to reported, "
               "conflict is preserved with both candidates."),
        limitations=("FIRDS field 5 is 'issuer or operator of "
                     "the trading venue', not strictly 'the "
                     "issuer' — the role qualifier is carried, "
                     "not relabelled.")))
    r(RuleMeta(
        rule_id="entity_role", version=1,
        name="Entity role typing (issuer vs vehicle vs manager)",
        basis=("PRIII child entities carry party roles "
               "(issuers, offerors); fund intelligence carries "
               "management-company roles. Distinct LEIs under "
               "distinct roles are relationships, not conflicts."),
        limitations=("Role coverage is source-dependent; absence "
                     "of a manager-LEI assertion does not mean "
                     "none exists.")))
    r(RuleMeta(
        rule_id="haircut_display", version=1,
        name="ECB-published haircut passthrough",
        basis=("The ea_csv publishes the currently applicable "
               "haircut per asset. We display it verbatim as "
               "reported rather than re-deriving it."),
        limitations=("Not a re-computation: the versioned haircut "
                     "schedule engine is a separate workstream; "
                     "reported haircut is snapshot-scoped.")))


_register()

from security_passport.domain.rules import ref  # noqa: E402

__all__ = ["REGISTRY", "ref"]
