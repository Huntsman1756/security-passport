"""Passport builder — assertions → adjudicated blocks → passport.

Assembles one passport per request from (a) the upstream
InstrumentProvider pinned to one generation and (b) the own-source
PassportStore pinned to one published generation. All statuses are
assigned here; providers never decide epistemology.
"""
from __future__ import annotations

from datetime import UTC, datetime
from datetime import date as _Date
from typing import Any

from security_passport.domain.evidence import Assertion, EvidenceRef
from security_passport.domain.fields import PassportField, TemporalCoverage
from security_passport.domain.passport import Passport, PassportBlock
from security_passport.domain.status import (
    FieldStatus,
    QualityFlag,
    SourceTimeSemantics,
    TemporalAnswerState,
    TemporalBasis,
)
from security_passport.providers import ecb_dictionary
from security_passport.providers.base import (
    InstrumentProvider,
    IssuerAssertionFact,
    ListingFact,
    PassportStore,
    ProviderError,
    SettlementLocationFact,
)
from security_passport.providers.iberclear import (
    IBERCLEAR_CODES,
    LIMITATION_TEXT,
    sss_for_csd_code,
)
from security_passport.rules import ref
from security_passport.temporal import (
    NormalizedDate,
    min_real_date,
    normalize_firds_date,
)

_OI_DS = "firds_projection"
_PRIII_DS = "priii_documents"
_ECB_DS = "ea_csv"
_SSS_DS = "eligible_sss_links"

CFI_CLASS = {"C": "collective_investment", "D": "debt",
             "E": "equity", "F": "future", "H": "structured",
             "I": "other", "J": "option", "O": "otc_derivative",
             "R": "referential", "S": "swap"}
UNDATED_LETTERS = {"C", "E"}


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _d(s: str | None) -> _Date | None:
    """Best-effort ISO/period string → date."""
    import datetime as _dt
    s = (s or "")[:10]
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%y%m%d", "%Y-%m"):
        try:
            return _dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _month_end(period: str | None) -> _Date | None:
    """"2026-05" → 2026-05-31."""
    import calendar
    d = _d(period)
    if d is None:
        return None
    import datetime as _dt
    return _dt.date(d.year, d.month,
                    calendar.monthrange(d.year, d.month)[1])


def _oi_ev(provider_locator: str, *, dataset: str = _OI_DS,
           record_id: str, raw: Any = None,
           upstream_artifact: str = "",
           retrieved_at: str = "") -> EvidenceRef:
    """Evidence pointing at the upstream-served record, carrying
    upstream artifact provenance through verbatim."""
    return EvidenceRef(
        provider="openinstrument", dataset=dataset,
        record_id=record_id,
        source_locator=provider_locator,
        retrieved_at=retrieved_at,
        raw_value=raw,
        upstream_provider="esma_firds",
        upstream_artifact=upstream_artifact,
        upstream_locator=provider_locator)


def _ecb_ev(record_id: str, snapshot: str, retrieved_at: str,
            raw: Any = None) -> EvidenceRef:
    return EvidenceRef(
        provider="ecb_eligible_assets", dataset=_ECB_DS,
        record_id=record_id,
        artifact_id=f"ea_csv_{snapshot}",
        source_locator=("ecb.europa.eu eligible marketable "
                        "assets daily list"),
        retrieved_at=retrieved_at,
        effective_at=snapshot,
        raw_value=raw,
        parser_version="ecb_assets.v1")


def _priii_ev(record_id: str, artifact: str, observed_at: str,
              raw: Any = None) -> EvidenceRef:
    return EvidenceRef(
        provider="esma_priii", dataset=_PRIII_DS,
        record_id=record_id, artifact_id=artifact,
        source_locator=("registers.esma.europa.eu solr "
                        "esma_registers_priii_documents"),
        retrieved_at=observed_at, raw_value=raw,
        parser_version="esma_prospectus.v1")


def _artifact_ev(record_id: str, provider: str, file_date: str,
                 observed_at: str,
                 artifact_sha: str) -> EvidenceRef:
    return EvidenceRef(
        provider=provider, dataset="instrument_csd_evidence",
        record_id=record_id, artifact_id=artifact_sha,
        published_at=file_date, retrieved_at=observed_at,
        parser_version="euronext_esmil.v1")


def _sss_ev(record_id: str, dataset: str, stamp: str,
            observed_at: str, raw: Any = None) -> EvidenceRef:
    return EvidenceRef(
        provider="ecb_sss_links", dataset=dataset,
        record_id=record_id,
        source_locator="ecb.europa.eu eligible SSS/links pages",
        retrieved_at=observed_at, published_at=stamp,
        raw_value=raw, parser_version="ecb_sss.v1")


def _mic_ev(mic_code: str) -> EvidenceRef:
    return EvidenceRef(
        provider="iso10383_mic", dataset="mic",
        record_id=mic_code,
        source_locator="iso20022.org ISO10383_MIC.csv",
        parser_version="mic.v1")


def _oi_state_field(name: str, value: Any, state: str,
                    ev: EvidenceRef,
                    searched: list[str]) -> PassportField:
    """Map upstream adjudication state → passport status."""
    if state == "conflict":
        return PassportField(
            name=name, value=None, status=FieldStatus.CONFLICT,
            evidence=[ev],
            explanation=("Upstream preserves a provider conflict; "
                         "candidate values are not exported via "
                         "the v1 contract for this field."),
            searched_sources=searched)
    if value in (None, ""):
        return PassportField.not_found(
            name, searched_sources=searched,
            explanation="No assertion in upstream projection.")
    return PassportField.reported(
        name, value, [ev],
        searched_sources=searched)


class PassportBuilder:
    def __init__(self, provider: InstrumentProvider,
                 store: PassportStore,
                 warnings: list[str] | None = None,
                 venue: Any = None) -> None:
        self._p = provider
        self._s = store
        self._v = venue          # VenueContextProvider | None
        self._warnings: list[str] = list(warnings or [])
        self._searched: dict[str, set[str]] = {}

    def _note(self, *parts: str) -> None:
        self._warnings.append(":".join(parts))

    def _searched_add(self, field_name: str, src: str) -> None:
        self._searched.setdefault(field_name, set()).add(src)

    # ================= main entry =====================================

    def build(self, isin: str, checksum_ok: bool,
              as_of: str | None = None) -> Passport:
        """Build the passport. With ``as_of=T`` each block selects
        only evidence admissible at T *before* adjudication — the
        current passport is never built and then truncated."""
        import datetime as _dt

        T = _dt.date.fromisoformat(as_of) if as_of else None
        searched_oi = f"openinstrument ({self._p.name()})"
        identity = self._identity(isin, searched_oi, checksum_ok, T)
        secondary = self._secondary(isin, searched_oi, T)
        primary = self._primary(isin, T)
        self._iic_roles(isin, primary, T)
        ecb = self._collateral(isin, T)
        post = self._post_trade(isin, ecb, T)

        overall = self._overall(identity, primary, secondary,
                                post, ecb)
        gen = self._s.generation()
        return Passport(
            isin=isin,
            generated_at=_now(),
            generation=gen,
            openinstrument_generation=self._p.generation(),
            overall_state=overall,
            identity=identity,
            primary_market=primary,
            secondary_market=secondary,
            post_trade=post,
            eurosystem_collateral=ecb,
            temporal_coverage={
                "identity": {"basis": "reconstructed",
                             "source": "openinstrument/firds",
                             "note": "provider publication time; "
                                     "left-censored at baseline"},
                "primary_market": {"basis": "observed_history"},
                "secondary_market": {"basis": "reconstructed"},
                "post_trade": {"basis": "observed_history"},
                "eurosystem_collateral": {"basis": "current_only"}},
            source_summary=self._source_summary(),
            warnings=self._warnings,
            valid_checksum=checksum_ok,
            as_of=as_of)

    def _source_summary(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = [
            {"provider": "openinstrument",
             "generation": self._p.generation(),
             "basis": "reconstructed"},
            {"provider": "ecb_eligible_assets",
             "snapshot": self._s.ecb_snapshot(),
             "basis": "current_only"}]
        meta: dict[str, Any] = getattr(self._s, "meta", lambda: {})() or {}
        if "mode" in meta:
            out.append({"provider": "fixtures", "mode": "demo"})
        return out

    def _temporal(self, b: PassportBlock,
                  T: _Date | None, basis: TemporalBasis,
                  semantics: SourceTimeSemantics,
                  answer_state: TemporalAnswerState | None = None,
                  note: str = "",
                  coverage_start: str | None = None,
                  coverage_end: str | None = None) -> None:
        b.temporal = TemporalCoverage(
            basis=basis,
            coverage_start=coverage_start,
            coverage_end=coverage_end,
            left_censored=(basis == TemporalBasis.RECONSTRUCTED),
            source_time_semantics=semantics,
            requested_as_of=T.isoformat() if T else None,
            answer_state=(answer_state.value if answer_state
                          else None),
            answer_note=note)

    def _earliest_listing_date(
            self, isin: str) -> _Date | None:
        """Earliest provider-published date evidencing the
        instrument's existence — admission, request, or first
        trade across listings."""
        try:
            listings = self._p.listings(isin)
        except ProviderError:
            return None
        dates: list[_Date] = []
        for li in listings:
            for raw in (li.admission_approval_date,
                        li.admission_request_date,
                        li.first_trade_date):
                nd = normalize_firds_date(raw)
                dd = _d(nd.value)
                if dd is not None:
                    dates.append(dd)
        return min(dates) if dates else None

    def _self_declared_not_found(self, b: PassportBlock,
                                 names: list[str],
                                 searched: list[str],
                                 why: str) -> None:
        for n in names:
            b.fields[n] = PassportField.not_found(
                n, searched_sources=searched, explanation=why)

    # ================= IDENTITY =======================================

    def _identity(self, isin: str, searched: str,
                  checksum_ok: bool, T: _Date | None = None) -> PassportBlock:
        b = PassportBlock(name="identity")
        b.temporal = TemporalCoverage(
            basis=TemporalBasis.RECONSTRUCTED,
            left_censored=True,
            source_time_semantics=(
                SourceTimeSemantics.PROVIDER_PUBLICATION_TIME))
        # reconstructed basis: the instrument is answerable at T
        # iff some provider-dated evidence of its existence is
        # already admissible at T.
        earliest = self._earliest_listing_date(isin)
        if T is not None and earliest is not None and earliest > T:
            self._temporal(
                b, T, TemporalBasis.RECONSTRUCTED,
                SourceTimeSemantics.PROVIDER_PUBLICATION_TIME,
                TemporalAnswerState.OUTSIDE_COVERAGE,
                note=("No provider-dated evidence of this "
                      "instrument's existence at "
                      f"{T.isoformat()} (earliest: "
                      f"{earliest.isoformat()}). Current data "
                      "has NOT been substituted."),
                coverage_start=earliest.isoformat())
            self._self_declared_not_found(
                b, ["isin", "cfi", "fisn", "instrument_name",
                    "issuer_lei", "issuer_name",
                    "notional_currency", "competent_authority",
                    "instrument_type", "maturity_date",
                    "firds_record_count"], [searched],
                "outside coverage at requested as_of")
            b.collections["identifiers"] = []
            b.collections["entity_roles"] = []
            return b
        if T is not None:
            self._temporal(
                b, T, TemporalBasis.RECONSTRUCTED,
                SourceTimeSemantics.PROVIDER_PUBLICATION_TIME,
                TemporalAnswerState.AVAILABLE,
                coverage_start=(earliest.isoformat()
                                if earliest else None))
        try:
            inst = self._p.instrument(isin)
        except ProviderError as e:
            self._note("identity", "openinstrument unavailable",
                       e.message)
            inst = None
        if inst is None or not inst.found:
            srcs = [searched]
            for n in ("isin", "cfi", "fisn", "instrument_name",
                      "issuer_lei", "issuer_name",
                      "notional_currency", "competent_authority"):
                b.fields[n] = PassportField.not_found(
                    n, searched_sources=srcs)
            b.fields["instrument_type"] = PassportField.not_found(
                "instrument_type", searched_sources=srcs)
            b.fields["maturity_date"] = PassportField.not_found(
                "maturity_date", searched_sources=srcs)
            b.collections["identifiers"] = []
            b.collections["entity_roles"] = []
            if inst is None:
                b.warnings.append("upstream instrument source "
                                  "unavailable")
            return b

        ev = _oi_ev(f"/v1/instruments/{isin}", record_id=isin,
                    retrieved_at=inst.firds_snapshot)
        b.fields["isin"] = PassportField.reported(
            "isin", isin, [ev])
        b.fields["cfi"] = _oi_state_field(
            "cfi", inst.cfi, inst.cfi_state, ev, [searched])
        b.fields["fisn"] = _oi_state_field(
            "fisn", inst.fisn, inst.fisn_state, ev, [searched])
        # display name: prefer full_name; fall back to FISN, each
        # carrying its OWN upstream state
        if inst.full_name:
            nf = _oi_state_field("instrument_name", inst.full_name,
                                 inst.full_name_state, ev,
                                 [searched])
        elif inst.fisn:
            nf = _oi_state_field("instrument_name", inst.fisn,
                                 inst.fisn_state, ev, [searched])
            nf.explanation = (
                "full_name unset upstream; displaying FISN as "
                "instrument name.")
            if inst.full_name_state == "conflict":
                nf.explanation += (" Upstream reports a "
                                   "provider conflict on "
                                   "full_name (venue-authored "
                                   "names differ).")
        else:
            nf = PassportField.not_found(
                "instrument_name", searched_sources=[searched])
        b.fields["instrument_name"] = nf
        b.fields["notional_currency"] = _oi_state_field(
            "notional_currency", inst.notional_currency,
            inst.notional_currency_state, ev, [searched])
        b.fields["competent_authority"] = _oi_state_field(
            "competent_authority", inst.competent_authority,
            inst.competent_authority_state, ev, [searched])
        b.fields["firds_record_count"] = PassportField.reported(
            "firds_record_count", inst.n_firds_records, [ev])

        letter = (inst.cfi_letter or (inst.cfi or "")[:1]).upper()
        if letter in CFI_CLASS:
            b.fields["instrument_type"] = PassportField.derived(
                "instrument_type", CFI_CLASS[letter], [ev],
                ref("instrument_type",
                    inputs=({"cfi": inst.cfi},)))
        else:
            b.fields["instrument_type"] = PassportField.not_found(
                "instrument_type", searched_sources=[searched])

        # maturity — reported only when a source carries it
        ecb_row = self._s.ecb_asset(isin)
        pr = self._s.priii(isin)
        mat_val = ""
        mat_ev: list[EvidenceRef] = []
        if ecb_row is not None and ecb_row.maturity_date:
            mat_val = ecb_row.maturity_date
            mat_ev.append(_ecb_ev(
                isin, ecb_row.snapshot,
                ecb_row.retrieved_at or
                self._s.ecb_retrieved_at(),
                raw=ecb_row.maturity_date))
        if pr and pr.documents:
            for d in pr.documents:
                if d.ifii_mat_exp_date:
                    mat_ev.append(_priii_ev(
                        d.root_id or isin, pr.artifact_id,
                        pr.observed_at, raw=d.ifii_mat_exp_date))
                    if not mat_val:
                        mat_val = d.ifii_mat_exp_date[:10]
        if letter in UNDATED_LETTERS and not mat_val:
            b.fields["maturity_date"] = PassportField.not_applicable(
                "maturity_date",
                ref("dated_instrument_scope",
                    inputs=({"cfi": inst.cfi},)),
                explanation=(f"CFI {letter}* instruments are "
                             "undated by construction."))
        elif mat_val:
            b.fields["maturity_date"] = PassportField.reported(
                "maturity_date", mat_val, mat_ev)
        else:
            b.fields["maturity_date"] = PassportField.not_found(
                "maturity_date",
                searched_sources=[searched, "ecb_eligible_assets",
                                  "esma_priii"])

        # issuer
        self._issuer(b, isin, searched, ev, inst)
        # identifiers (FIGI levels)
        try:
            idents = self._p.identifiers(isin)
        except ProviderError:
            idents = []
        b.collections["identifiers"] = [
            {"level": i.level, "scheme": i.scheme, "value": i.value,
             "provider": i.provider} for i in idents]
        return b

    def _issuer(self, b: PassportBlock, isin: str, searched: str,
                ev: EvidenceRef, inst: Any) -> None:
        try:
            iss = self._p.issuer(isin)
        except ProviderError as e:
            self._note("identity", "issuer endpoint", e.message)
            b.fields["issuer_lei"] = PassportField.not_found(
                "issuer_lei", searched_sources=[searched])
            b.fields["issuer_name"] = PassportField.not_found(
                "issuer_name", searched_sources=[searched])
            b.collections["entity_roles"] = []
            return
        if not iss.found:
            for n in ("issuer_lei", "issuer_name"):
                b.fields[n] = PassportField.not_found(
                    n, searched_sources=[searched])
            b.collections["entity_roles"] = []
            return
        if iss.state == "conflict":
            cands: dict[str, Assertion] = {}
            def pack(rows: tuple[IssuerAssertionFact, ...],
                     role: str) -> None:
                for a in rows:
                    if a.lei not in cands:
                        cands[a.lei] = Assertion(
                            value=a.lei, role=role,
                            evidence=_oi_ev(
                                a.locator or f"/v1/instruments/"
                                             f"{isin}/issuer",
                                record_id=isin, raw=a.lei))
            pack(iss.gleif_assertions, "gleif_isin_lei")
            pack(iss.firds_assertions, "firds_issuer_or_venue_operator")
            if len(cands) >= 2:
                b.fields["issuer_lei"] = PassportField.conflict(
                    "issuer_lei", list(cands.values()),
                    explanation=("Provider disagreement preserved "
                                 "by upstream adjudication; no "
                                 "automatic winner."),
                    searched_sources=[searched])
            else:
                # conflict state but candidates not reconstructable
                b.fields["issuer_lei"] = PassportField(
                    name="issuer_lei", value=None,
                    status=FieldStatus.CONFLICT, evidence=[ev],
                    explanation=("Upstream reports conflict but "
                                 "the candidates are not exported "
                                 "via the v1 contract."),
                    searched_sources=[searched])
        elif iss.canonical_lei:
            st = "corroborated" if iss.state == "corroborated" \
                else "single_source"
            b.fields["issuer_lei"] = PassportField.reported(
                "issuer_lei", iss.canonical_lei, [ev],
                rule=ref("issuer_lei_adjudication",
                         inputs=({"state": st},)),
                searched_sources=[searched])
        else:
            b.fields["issuer_lei"] = PassportField.not_found(
                "issuer_lei", searched_sources=[searched],
                explanation="No issuer LEI assertion found.")
        ent = iss.entity or {}
        nm = (ent.get("legal_name") or ent.get("legalName")
              or ent.get("name"))
        if nm:
            b.fields["issuer_name"] = PassportField.reported(
                "issuer_name", nm, [_oi_ev(
                    f"/v1/instruments/{isin}/issuer",
                    record_id=isin,
                    upstream_artifact=str(ent.get("locator") or ""),
                    raw=nm)])
        else:
            # corroborating issuer names from own sources
            alt_ev: list[EvidenceRef] = []
            alt_name = ""
            pr = self._s.priii(isin)
            if pr and pr.documents and pr.documents[0].issuer_name:
                alt_name = pr.documents[0].issuer_name
                alt_ev.append(_priii_ev(
                    pr.documents[0].root_id or isin,
                    pr.artifact_id, pr.observed_at,
                    raw=alt_name))
            ecb_row = self._s.ecb_asset(isin)
            if ecb_row and ecb_row.issuer_name:
                alt_ev.append(_ecb_ev(
                    isin, ecb_row.snapshot,
                    ecb_row.retrieved_at or
                    self._s.ecb_retrieved_at(),
                    raw=ecb_row.issuer_name))
                if not alt_name:
                    alt_name = ecb_row.issuer_name
            if alt_name and alt_ev:
                b.fields["issuer_name"] = PassportField.reported(
                    "issuer_name", alt_name, alt_ev,
                    explanation=("Issuer name from register/"
                                 "collateral sources; GLEIF entity "
                                 "lookup returned nothing."))
            else:
                b.fields["issuer_name"] = PassportField.not_found(
                    "issuer_name",
                    searched_sources=[
                        searched, "gleif (via upstream)",
                        "esma_priii", "ecb_eligible_assets"])
        # entity roles — fund roles when the upstream v2 surface has
        # them; FIRDS Issr semantics is always listed as its own role
        roles: list[dict[str, str]] = [{
            "role": "issuer_or_venue_operator",
            "lei": a.lei, "source": "esma_firds"}
            for a in iss.firds_assertions][:8]
        for a in iss.gleif_assertions[:4]:
            roles.append({"role": "isin_lei_mapping",
                          "lei": a.lei, "source": "gleif"})
        try:
            for r in self._p.fund_roles(isin):
                roles.append({"role": r["role"].lower(),
                              "lei": r["value"],
                              "source": "openinstrument_v2"})
        except ProviderError:
            pass
        # dedupe (role, lei)
        seen: set[tuple[str, str]] = set()
        dedup = []
        for r in roles:
            k = (r["role"], r["lei"])
            if k not in seen:
                seen.add(k)
                dedup.append(r)
        b.collections["entity_roles"] = dedup

    # ================= PRIMARY MARKET =================================

    def _primary(self, isin: str, T: _Date | None = None) -> PassportBlock:
        b = PassportBlock(name="primary_market")
        b.temporal = TemporalCoverage(
            basis=TemporalBasis.OBSERVED_HISTORY,
            source_time_semantics=SourceTimeSemantics.RETRIEVAL_TIME)
        pr = self._s.priii(isin)
        searched = ["esma_priii (esma_registers_priii_documents)"]
        # observed_history: PRIII evidence exists only from our
        # first observation — never substitute a later capture.
        obs_start = _d(pr.observed_at) if pr else None
        if T is not None:
            if obs_start is not None and obs_start > T:
                self._temporal(
                    b, T, TemporalBasis.OBSERVED_HISTORY,
                    SourceTimeSemantics.RETRIEVAL_TIME,
                    TemporalAnswerState.OUTSIDE_COVERAGE,
                    note=("Historical evidence unavailable before "
                          f"{obs_start.isoformat()} (first "
                          "observation of the PRIII corpus). "
                          "Current data has NOT been "
                          "substituted."),
                    coverage_start=obs_start.isoformat())
                self._self_declared_not_found(
                    b, ["prospectus_found", "home_member_state",
                        "approval_filing_date", "is_passported",
                        "host_member_states"], searched,
                    "outside coverage at requested as_of")
                b.collections["document_graph"] = []
                b.collections["fund_roles"] = []
                return b
            self._temporal(
                b, T, TemporalBasis.OBSERVED_HISTORY,
                SourceTimeSemantics.RETRIEVAL_TIME,
                TemporalAnswerState.AVAILABLE
                if pr is not None else
                TemporalAnswerState.UNAVAILABLE,
                note=("" if pr is not None else
                      "No PRIII observation for this ISIN in "
                      "this generation — coverage cannot be "
                      "bounded."),
                coverage_start=(obs_start.isoformat()
                                if obs_start else None))
        if pr is None:
            for n in ("prospectus_found", "home_member_state",
                      "approval_filing_date", "is_passported"):
                b.fields[n] = PassportField.not_found(
                    n, searched_sources=searched,
                    explanation=("ISIN not in the observed PRIII "
                                 "corpus of this generation."))
            b.collections["document_graph"] = []
            b.warnings.append("PRIII corpus does not cover this "
                              "ISIN in this generation")
            return b
        ev = _priii_ev(isin, pr.artifact_id, pr.observed_at)
        # at T: only documents approved/filed by T existed —
        # the register capture is admissible (T ≥ obs_start)
        # but its contents are filtered to T.
        docs: list[Any] = list(pr.documents)
        if T is not None:
            docs = [d for d in pr.documents
                    if (_d(d.approval_filing_date) or T) <= T]
        found = bool(docs)
        b.fields["prospectus_found"] = PassportField.reported(
            "prospectus_found", found, [ev],
            explanation=("Register search performed for this ISIN. "
                         if not found else ""),
            searched_sources=searched)
        if not found:
            for n in ("home_member_state", "approval_filing_date",
                      "is_passported"):
                b.fields[n] = PassportField.not_found(
                    n, searched_sources=searched,
                    explanation=("No filings returned by the "
                                 "register; may be exempt, out of "
                                 "scope, or unregistered — never "
                                 "asserted as 'no prospectus "
                                 "exists'."))
            b.collections["document_graph"] = []
            return b
        first = docs[0]
        evd = _priii_ev(first.root_id or isin, pr.artifact_id,
                        pr.observed_at,
                        raw=first.national_document_id)
        b.fields["home_member_state"] = PassportField.reported(
            "home_member_state",
            first.home_member_state_code or first.home_member_state,
            [evd])
        b.fields["approval_filing_date"] = PassportField.reported(
            "approval_filing_date",
            first.approval_filing_date[:10], [evd],
            raw_value=first.approval_filing_date)
        b.fields["is_passported"] = PassportField.reported(
            "is_passported", first.is_passported, [evd])
        b.fields["host_member_states"] = PassportField.reported(
            "host_member_states",
            sorted(set(first.member_states)), [evd])
        b.collections["document_graph"] = [
            self._doc_node(d, pr) for d in docs]
        return b

    def _doc_node(self, d: Any, pr: Any) -> dict[str, Any]:
        return {
            "root_id": d.root_id,
            "document_type": d.document_type,
            "document_type_descr": d.document_type_descr,
            "prospectus_type": d.prospectus_type,
            "structure_type": d.structure_type,
            "national_document_id": d.national_document_id,
            "home_member_state": d.home_member_state_code,
            "member_states": list(d.member_states),
            "is_passported": d.is_passported,
            "approval_filing_date": d.approval_filing_date[:10],
            "first_passporting_date": d.first_passporting_date[:10],
            "doc_last_update_date": d.doc_last_update_date,
            "download_url": d.download_url,
            "party_name": d.party_name,
            "issuer_lei": d.issuer_lei,
            "issuer_name": d.issuer_name,
            "offeror_lei": d.offeror_lei,
            "offeror_name": d.offeror_name,
            "related_document_ids": list(d.related_document_ids),
            "languages": d.document_languages,
            "status": "reported",
            "observed_at": pr.observed_at,
        }

    def _iic_roles(self, isin: str, b: PassportBlock,
                   T: _Date | None = None) -> None:
        """cnmv_iic registry roles for ES IIC share classes —
        fund/compartment/share-class + gestora/depositario as
        ROLES, never promoted to issuer identity."""
        r = self._s.iic_roles(isin)
        period_end = _month_end(r.period) if r else None
        if r is None or (T is not None and period_end is not None
                         and period_end > T):
            b.collections["fund_roles"] = []
            if T is not None and r is not None:
                for n in ("fund_vehicle", "fund_share_class",
                          "management_company", "depositary"):
                    b.fields[n] = PassportField.not_found(
                        n, searched_sources=["cnmv_iic registry"],
                        explanation=(
                            f"registry period {r.period} not "
                            f"published at {T.isoformat()}; "
                            "current data NOT substituted"))
            return
        ev = EvidenceRef(
            provider="openfunds_cnmv_iic",
            dataset="share_classes+funds",
            record_id=r.share_class_key,
            artifact_id=r.source_artifact_id,
            published_at=r.period,
            parser_version="cnmv_iic.adapters.fondregistro/0.1.0")
        b.collections["fund_roles"] = [{
            "fund_key": r.fund_key,
            "compartment_key": r.compartment_key,
            "share_class_key": r.share_class_key,
            "entity_type": r.entity_type,
            "fund_name": r.fund_name,
            "share_class_name": r.share_class_name,
            "compartment_name": r.compartment_name,
            "management_company": r.manager_name,
            "depositary": r.depositary_name,
            "management_company_reg": r.manager_reg_number,
            "depositary_reg": r.depositary_reg_number,
            "period": r.period,
            "status": "reported",
            "evidence": ev.to_dict()}]
        b.fields["fund_vehicle"] = PassportField.reported(
            "fund_vehicle", r.fund_name, [ev])
        b.fields["fund_share_class"] = PassportField.reported(
            "fund_share_class",
            f"{r.share_class_name} ({r.share_class_key})", [ev])
        b.fields["management_company"] = PassportField.reported(
            "management_company",
            {"name": r.manager_name,
             "reg_number": r.manager_reg_number}, [ev],
            explanation=("CNMV IIC registry role — never an "
                         "issuer identifier."))
        b.fields["depositary"] = PassportField.reported(
            "depositary",
            {"name": r.depositary_name,
             "reg_number": r.depositary_reg_number}, [ev],
            explanation=("CNMV IIC registry role — never an "
                         "issuer identifier."))

    # ================= SECONDARY MARKET ================================

    def _secondary(self, isin: str, searched: str,
                   T: _Date | None = None) -> PassportBlock:
        b = PassportBlock(name="secondary_market")
        b.temporal = TemporalCoverage(
            basis=TemporalBasis.RECONSTRUCTED,
            left_censored=True,
            source_time_semantics=(
                SourceTimeSemantics.PROVIDER_PUBLICATION_TIME))
        try:
            listings = self._p.listings(isin)
        except ProviderError as e:
            self._note("secondary_market", "listings", e.message)
            listings = []
        # as-of filtering: a listing is admissible at T iff some
        # provider-published date on it is already ≤ T; state is
        # then recomputed at T (terminated only if termination ≤ T).
        n_dropped = 0
        if T is not None and listings:
            admissible = []
            for li in listings:
                dates = []
                for x in (li.admission_approval_date,
                          li.admission_request_date,
                          li.first_trade_date):
                    d = _d(normalize_firds_date(x).value or "")
                    if d is not None:
                        dates.append(d)
                if dates and min(dates) > T:
                    n_dropped += 1
                    continue
                admissible.append(li)
            listings = admissible
            state = (TemporalAnswerState.PARTIAL
                     if n_dropped else TemporalAnswerState.AVAILABLE)
            self._temporal(
                b, T, TemporalBasis.RECONSTRUCTED,
                SourceTimeSemantics.PROVIDER_PUBLICATION_TIME,
                state,
                note=(f"{n_dropped} listing(s) postdate T "
                      "and are excluded" if n_dropped else ""))
        if not listings:
            b.fields["listing_count"] = PassportField.reported(
                "listing_count", 0, [_oi_ev(
                    f"/v1/instruments/{isin}/listings",
                    record_id=isin)],
                searched_sources=[searched])
            for n in ("first_admission_date",
                      "active_venue_count"):
                b.fields[n] = PassportField.not_found(
                    n, searched_sources=[searched])
            b.collections["listings"] = []
            return b
        rows: list[dict[str, Any]] = []
        adm_cands: list[NormalizedDate] = []
        n_active = 0
        for li in listings:
            rows.append(self._listing_row(li, T))
            state = rows[-1]["state"]
            if state == "active":
                n_active += 1
            for raw in (li.admission_approval_date,
                        li.admission_request_date,
                        li.first_trade_date):
                nd = normalize_firds_date(raw)
                if nd.value is not None:
                    adm_cands.append(nd)
        b.collections["listings"] = rows
        ev = _oi_ev(f"/v1/instruments/{isin}/listings",
                    record_id=isin)
        b.fields["listing_count"] = PassportField.reported(
            "listing_count", len(rows), [ev])
        b.fields["active_venue_count"] = PassportField.derived(
            "active_venue_count", n_active, [ev],
            ref("venue_state", inputs=(
                {"n_listings": len(rows)},)))
        best = min_real_date(adm_cands)
        if best is not None and best.value:
            flags = list(best.flags)
            b.fields["first_admission_date"] = PassportField.derived(
                "first_admission_date", best.value, [ev],
                ref("first_admission",
                    inputs=({"n_candidates": len(adm_cands)},)),
                quality_flags=flags,
                raw_value=best.raw)
        else:
            nf = PassportField.not_found(
                "first_admission_date",
                searched_sources=[searched],
                explanation=("All admission-date evidence was "
                             "sentinel/unknown."))
            if adm_cands or any(
                    normalize_firds_date(x).is_sentinel
                    for li in listings
                    for x in (li.admission_approval_date,
                              li.admission_request_date,
                              li.first_trade_date)):
                nf.quality_flags.append(
                    QualityFlag.SOURCE_DEFAULT_VALUE)
            b.fields["first_admission_date"] = nf
        return b

    def _listing_row(self, li: ListingFact,
                     T: _Date | None = None) -> dict[str, Any]:
        adm = normalize_firds_date(li.admission_approval_date)
        req = normalize_firds_date(li.admission_request_date)
        trd = normalize_firds_date(li.first_trade_date)
        term = normalize_firds_date(li.termination_date)
        # venue state (venue_state.v1): terminated < active < pending
        term_d = _d(term.value or "")
        if term_d is not None and (T is None or term_d <= T):
            state = "terminated"
        elif T is not None and term_d is not None and term_d > T:
            state = "active"     # terminates after T — active at T
        elif adm.value or trd.value or req.value:
            state = "active"
        else:
            state = "unknown_dates"
        micf = self._s.mic(li.venue_mic)
        relf = self._s.mic(li.relevant_venue) \
            if li.relevant_venue else None
        opf = (self._s.mic(micf.operating_mic)
               if micf and micf.operating_mic != micf.mic
               else None)
        flags = []
        for nd in (adm, req, trd, term):
            for f in nd.flags:
                if f not in flags:
                    flags.append(f)
        vc = self._v.venue(li.venue_mic) if self._v else None
        row = {
            "venue_mic": li.venue_mic,
            "venue_name": micf.market_name if micf else "",
            "venue_mic_status": micf.status if micf else "",
            "oprt_sgmt": micf.oprt_sgmt if micf else "",
            "operating_mic": (micf.operating_mic if micf else ""),
            "operator": ((opf.legal_entity or opf.market_name)
                         if opf else
                         (micf.legal_entity or micf.market_name)
                         if micf else ""),
            "operator_lei": ((opf.lei if opf else
                             (micf.lei if micf else "")) or
                             (micf.lei if micf else "")),
            "market_category": (micf.market_category
                                if micf else ""),
            "rulebook_family": (vc.rulebook_ref or None
                                if vc else None),
            "rulebook_state": (vc.rulebooks[0].get("state")
                               if vc and vc.rulebooks else
                               "unconfigured" if vc is None else
                               None),
            "relevant_venue": li.relevant_venue,
            "relevant_venue_name": relf.market_name if relf else "",
            "issuer_requested_admission":
                li.issuer_requested_admission,
            "admission_approval_date": adm.value,
            "admission_approval_date_raw": adm.raw,
            "first_trade_date": trd.value,
            "first_trade_date_raw": trd.raw,
            "termination_date": term.value,
            "termination_date_raw": term.raw,
            "state": state,
            "quality_flags": [f.value for f in flags],
            "evidence": _oi_ev(
                li.locator or "firds", record_id=li.locator or
                f"{li.venue_mic}",
                raw={"adm": li.admission_approval_date,
                     "trd": li.first_trade_date,
                     "term": li.termination_date}).to_dict(),
            "mic_evidence": _mic_ev(li.venue_mic).to_dict()
            if micf else None,
        }
        if vc is not None and vc.rulebooks:
            row["rulebooks"] = [
                {"family": rb.get("family"),
                 "name": rb.get("name"),
                 "state": rb.get("state"),
                 "documents": [
                     {"title": doc.get("title"),
                      "document_id": doc.get("document_id"),
                      "effective_from": doc.get("effective_from"),
                      "sha256": doc.get("sha256"),
                      "captured_at": doc.get("captured_at")}
                     for doc in (rb.get("documents") or [])]}
                for rb in vc.rulebooks]
        return row

    # ================= EUROSYSTEM COLLATERAL ==========================

    def _collateral(self, isin: str, T: _Date | None = None) -> PassportBlock:
        b = PassportBlock(name="eurosystem_collateral")
        b.temporal = TemporalCoverage(
            basis=TemporalBasis.CURRENT_ONLY,
            coverage_start=None, coverage_end=None,
            source_time_semantics=SourceTimeSemantics.EFFECTIVE_TIME)
        snap = self._s.ecb_snapshot()
        searched = [f"ecb_eligible_assets ea_csv_{snap}"]
        snap_d = _d(f"20{snap}" if len(snap) == 6 else snap)
        retrieved_d = _d(self._s.ecb_retrieved_at())
        if T is not None:
            # single-snapshot store: answerable iff T sits inside
            # [snapshot publication, capture]. Before publication
            # we cannot substitute the current list backwards;
            # after capture a later snapshot may already exist.
            if snap_d and snap_d > T:
                self._temporal(
                    b, T, TemporalBasis.CURRENT_ONLY,
                    SourceTimeSemantics.EFFECTIVE_TIME,
                    TemporalAnswerState.OUTSIDE_COVERAGE,
                    note=(f"Requested {T.isoformat()} precedes "
                          f"the held snapshot ({snap}). The "
                          "current eligible-assets list has "
                          "NOT been projected backwards."),
                    coverage_start=snap_d.isoformat())
                self._self_declared_not_found(
                    b, ["eligible", "haircut_category", "haircut",
                        "asset_type", "issuer_csd",
                        "ecb_snapshot"], searched,
                    "outside coverage at requested as_of")
                return b
            later = (retrieved_d is not None and
                     snap_d is not None and
                     retrieved_d > snap_d)
            self._temporal(
                b, T, TemporalBasis.CURRENT_ONLY,
                SourceTimeSemantics.EFFECTIVE_TIME,
                TemporalAnswerState.AVAILABLE,
                note=("single-snapshot store — the snapshot is "
                      "the published state at T when "
                      "T ≥ snapshot date" +
                      ("; snapshots published after capture are "
                       "not held" if later else "")),
                coverage_start=(snap_d.isoformat()
                                if snap_d else None),
                coverage_end=(retrieved_d.isoformat()
                              if retrieved_d else None))
        row = self._s.ecb_asset(isin)
        # absence evidence points at the enumeration itself, not a
        # row that does not exist
        if row is None:
            ev = _ecb_ev(f"ea_csv_{snap}", snap,
                         self._s.ecb_retrieved_at())
            b.fields["eligible"] = PassportField.derived(
                "eligible", False, [ev],
                ref("eurosystem_eligibility",
                    inputs=({"snapshot": snap},)),
                searched_sources=searched,
                explanation=("ISIN absent from the authoritative "
                             "eligible-assets enumeration for this "
                             "snapshot — not eligible as of that "
                             "date."))
            for n in ("haircut_category", "asset_type", "haircut",
                      "issuer_csd"):
                b.fields[n] = PassportField.not_found(
                    n, searched_sources=searched)
            b.fields["ecb_snapshot"] = PassportField.reported(
                "ecb_snapshot", snap, [ev])
            return b
        ev = _ecb_ev(isin, snap, row.retrieved_at or
                     self._s.ecb_retrieved_at(),
                     raw={"issuer_csd": row.issuer_csd})
        b.fields["eligible"] = PassportField.derived(
            "eligible", True, [ev],
            ref("eurosystem_eligibility",
                inputs=({"snapshot": snap},)),
            searched_sources=searched)
        b.fields["ecb_snapshot"] = PassportField.reported(
            "ecb_snapshot", snap, [ev])
        b.fields["haircut_category"] = PassportField.reported(
            "haircut_category", row.haircut_category, [ev])
        b.fields["asset_type"] = PassportField.reported(
            "asset_type", row.asset_type, [ev])
        if row.haircut:
            b.fields["haircut"] = PassportField.reported(
                "haircut", row.haircut, [ev], unit="percent",
                rule=ref("haircut_display"))
        else:
            b.fields["haircut"] = PassportField.not_found(
                "haircut", searched_sources=searched)
        b.fields["issuer_csd"] = PassportField.reported(
            "issuer_csd", row.issuer_csd, [ev])
        for n, v in (("denomination_currency",
                      row.denomination_currency),
                     ("ecb_maturity_date", row.maturity_date),
                     ("coupon_rate", row.coupon_rate),
                     ("coupon_definition", row.coupon_definition),
                     ("issuer_group", row.issuer_group),
                     ("guarantor_name", row.guarantor_name),
                     ("covered_bond_flag", row.covered_bond_flag),
                     ("climate_factor", row.climate_factor)):
            if v:
                b.fields[n] = PassportField.reported(n, v, [ev])
        return b

    # ================= POST-TRADE =====================================

    def _post_trade(self, isin: str,
                    ecb_block: PassportBlock,
                    T: _Date | None = None) -> PassportBlock:
        b = PassportBlock(name="post_trade")
        b.temporal = TemporalCoverage(
            basis=TemporalBasis.OBSERVED_HISTORY,
            source_time_semantics=SourceTimeSemantics.RETRIEVAL_TIME)
        searched = ["ecb_eligible_assets", "ecb_sss_links",
                    "iberclear (public documentation)",
                    "euronext_esmil", "euronext_frs"]
        if T is not None:
            self._temporal(
                b, T, TemporalBasis.OBSERVED_HISTORY,
                SourceTimeSemantics.RETRIEVAL_TIME,
                TemporalAnswerState.AVAILABLE)
        # four separate assertions that must never merge:
        #   issuer CSD (ECB collateral-reference semantics)
        #   CSDs that admit this ISIN (instrument-level)
        #   CSD↔CSD links (infrastructure topology)
        #   route assessments (inference over the above)

        # ---- issuer CSD — ECB collateral-reference semantics ----------
        issuer_sss_name = ""
        issuer_sss_code = ""
        row = self._s.ecb_asset(isin)
        if T is not None:
            snap_d = _d(f"20{self._s.ecb_snapshot()}")
            if snap_d is not None and snap_d > T:
                # ECB evidence unpublished at T — same window as
                # the collateral block; do not project backwards.
                row = None
        if row is not None and row.issuer_csd:
            code = row.issuer_csd
            issuer_sss_code = code
            # prefer the official ECB dictionary codebook from the
            # generation; curated map is the offline fallback
            mapped = None
            dict_label = self._s.csd_codes().get(code, "")
            if dict_label:
                mapped = ecb_dictionary.csd_label(
                    code, self._s.csd_codes())
            if mapped is None:
                mapped = sss_for_csd_code(code)
            ev = _ecb_ev(isin, row.snapshot,
                         row.retrieved_at or self._s.ecb_retrieved_at(),
                         raw={"ISSUER_CSD": code})
            scope = "eurosystem_collateral_reference"
            if mapped:
                issuer_sss_name = mapped["name"]
                b.fields["issuer_csd"] = PassportField.reported(
                    "issuer_csd",
                    {"code": code, "name": mapped["name"],
                     "country": mapped["country"],
                     "scope": scope}, [ev])
            else:
                b.fields["issuer_csd"] = PassportField.reported(
                    "issuer_csd",
                    {"code": code, "name": "", "scope": scope}, [ev],
                    quality_flags=[
                        QualityFlag.POSSIBLE_SOURCE_DEFAULT])
                issuer_sss_name = code
        else:
            b.fields["issuer_csd"] = PassportField.not_found(
                "issuer_csd", searched_sources=searched,
                explanation=("No instrument-specific issuer-CSD "
                             "evidence. The ECB list only reports "
                             "issuer CSD for eligible assets; an "
                             "ISIN prefix is never used as a "
                             "substitute."))
        # Iberclear — explicit absence unless ECB says CLES01
        if issuer_sss_code in IBERCLEAR_CODES:
            b.fields["iberclear_admitted"] = PassportField.reported(
                "iberclear_admitted", True,
                b.fields["issuer_csd"].evidence,
                explanation=("ECB eligible-assets reports "
                             "ISSUER_CSD=CLES01 (Iberclear-ARCO)."))
        else:
            b.fields["iberclear_admitted"] = PassportField.not_found(
                "iberclear_admitted", searched_sources=searched,
                explanation=LIMITATION_TEXT)
        # ---- infrastructure topology ------------------------------------
        sss = self._s.eligible_sss()
        links = self._s.eligible_links()
        if T is not None:
            # the pages' own "last updated" is the admissibility
            # bound: content observed after T may reflect a later
            # revision — excluded, never projected back.
            stamp_d = _d((sss[0].page_stamp if sss else "") or
                         (links[0].page_stamp if links else ""))
            if stamp_d is not None and stamp_d > T:
                sss, links = [], []
                if b.temporal is not None:
                    import dataclasses
                    b.temporal = dataclasses.replace(
                        b.temporal,
                        answer_state=(
                            TemporalAnswerState.PARTIAL.value),
                        answer_note=(
                            "SSS/link topology excluded: page "
                            "content postdates T "
                            f"({stamp_d.isoformat()} > T)."))
        stamp = (sss[0].page_stamp if sss else "") or (
            links[0].page_stamp if links else "")
        obs = (sss[0].observed_at if sss else "") or (
            links[0].observed_at if links else "")
        b.collections["eligible_sss"] = [
            {"name": s.name, "country": s.country,
             "status": "reported",
             "evidence": _sss_ev(
                 s.name, "eligible_sss", s.page_stamp,
                 s.observed_at).to_dict()}
            for s in sss]
        # links touching the issuer CSD — context, never routes
        relevant = [lnk for lnk in links
                    if issuer_sss_name and (
                        issuer_sss_name in lnk.issuer_sss
                        or issuer_sss_name in lnk.investor_sss)]
        b.collections["link_topology"] = [
            {"investor_csd": lnk.investor_sss,
             "issuer_csd": lnk.issuer_sss,
             "link_type": "direct" if not lnk.intermediaries
             else "relayed",
             "intermediaries": list(lnk.intermediaries),
             "operated_by": lnk.operated_by,
             "status": "reported",
             "evidence": _sss_ev(
                 f"{lnk.investor_sss}->{lnk.issuer_sss}",
                 "eligible_links", lnk.page_stamp,
                 lnk.observed_at).to_dict()}
            for lnk in relevant]
        if sss:
            b.fields["eligible_sss_count"] = PassportField.reported(
                "eligible_sss_count", len(sss),
                [_sss_ev("eligible_sss_page", "eligible_sss",
                         stamp, obs)])
        else:
            b.fields["eligible_sss_count"] = PassportField.not_found(
                "eligible_sss_count", searched_sources=searched)
        # ---- instrument-level settlement locations ----------------------
        locs = self._s.settlement_locations(isin)
        n_inadmissible = 0
        if T is not None:
            # knowledge at T: the source file must be published
            # by T; effectiveness is a per-location annotation —
            # never merge published_at with effective_from.
            admissible = []
            for r in locs:
                pub = _d(r.source_published_at)
                if pub is not None and pub > T:
                    n_inadmissible += 1
                    continue
                admissible.append(r)
            locs = admissible
        def _eff(r: SettlementLocationFact) -> bool:
            efd = _d(r.effective_from)
            return (r.relationship in (
                "issuer_csd", "current_place_of_settlement")
                or (efd is not None and T is not None
                    and efd <= T))
        b.collections["settlement_locations"] = [
            {"csd": r.csd_name,
             "csd_code": r.csd_code,
             "relationship": r.relationship,
             "mic": r.other_mic or r.mic,
             "market": r.market,
             "settlement_currency": r.settlement_currency,
             "scope": r.scope,
             "source_published_at": r.source_published_at,
             "effective_from": r.effective_from or None,
             "effective": _eff(r) if T is not None else None,
             "note": r.note or None,
             "status": "reported",
             "provider": r.provider,
             "evidence": _artifact_ev(
                 f"{r.provider}:{r.isin}:{r.relationship}",
                 r.provider,
                 r.source_published_at, r.observed_at,
                 artifact_sha=r.artifact_sha256).to_dict()}
            for r in locs]
        if locs:
            b.fields["settlement_location_count"] = \
                PassportField.reported(
                    "settlement_location_count", len(locs),
                    [_artifact_ev(f"esmil:{isin}", locs[0].provider,
                                  locs[0].source_published_at,
                                  locs[0].observed_at,
                                  locs[0].artifact_sha256)],
                    searched_sources=searched)
        else:
            b.fields["settlement_location_count"] = \
                PassportField.not_found(
                    "settlement_location_count",
                    searched_sources=searched,
                    explanation=("No instrument-level CSD-published "
                                 "admission file lists this ISIN. "
                                 "Absence is not ineligibility — only "
                                 "files actually searched are "
                                 "declared."))
        # ---- route assessments — inference, clearly labelled ------------
        assessments: list[dict[str, Any]] = []
        loc_names = {r.csd_name for r in locs if r.csd_name}
        target_names = loc_names | (
            {issuer_sss_name} if issuer_sss_name else set())
        if target_names and relevant:
            for lnk in relevant:
                assessments.append({
                    "from_sss": lnk.investor_sss,
                    "to_sss": lnk.issuer_sss,
                    "status": "inferred",
                    "assessment": "topology_only",
                    "explanation": ("topology exists — usable for "
                                    "THIS ISIN only if the ISIN is "
                                    "additionally admitted at the "
                                    "investor SSS, which is not "
                                    "evidenced"),
                    "rule": "settlement_path.v1",
                    "limitations": LIMITATION_TEXT,
                    "evidence": _sss_ev(
                        f"{lnk.investor_sss}->{lnk.issuer_sss}",
                        "eligible_links", lnk.page_stamp,
                        lnk.observed_at).to_dict()})
        if not assessments:
            assessments.append({
                "from_sss": None, "to_sss": None,
                "status": "not_found",
                "assessment": "not_assessable",
                "explanation": ("no route asserted — settlement-path "
                                "assessment requires (a) a reported "
                                "issuer/settlement CSD and (b) "
                                "instrument-specific admission "
                                "evidence at an investor SSS"),
                "rule": "settlement_path.v1",
                "limitations": LIMITATION_TEXT,
                "evidence": None})
        b.collections["route_assessments"] = assessments
        # assessment — derived statement of what evidence exists
        if issuer_sss_name:
            txt = (f"Issuer SSS reported as {issuer_sss_name} "
                   f"({issuer_sss_code}) by the ECB eligible-assets "
                   f"snapshot. Eligible-link topology to/from that "
                   f"SSS exists in the Eurosystem list where shown. "
                   f"This does not establish that this ISIN is "
                   f"admitted to, held through, or operationally "
                   f"settleable over any link.")
        else:
            txt = ("Insufficient evidence to assert a settlement "
                   "path: no instrument-specific issuer-SSS "
                   "evidence was found, and SSS-link topology is "
                   "never used as a substitute for "
                   "instrument-level admission evidence.")
        assess_ev: list[EvidenceRef] = []
        if issuer_sss_name:
            assess_ev = list(b.fields["issuer_csd"].evidence)
        elif sss:
            assess_ev = [_sss_ev("eligible_sss_page",
                                 "eligible_sss", stamp, obs)]
        if not assess_ev:
            b.fields["assessment"] = PassportField.not_found(
                "assessment", searched_sources=searched,
                explanation=("No admissible post-trade evidence "
                             "at the requested date — nothing to "
                             "assess, and no current value has "
                             "been substituted."))
            return b
        b.fields["assessment"] = PassportField.derived(
            "assessment", txt, assess_ev,
            ref("settlement_path",
                inputs=({"issuer_sss": issuer_sss_code or None},
                        {"links_for_sss": len(relevant)})),
            searched_sources=searched)
        return b

    # ================= overall =========================================

    def _overall(self, *blocks: PassportBlock) -> str:
        idb = blocks[0]
        isin_f = idb.fields.get("isin")
        if isin_f is None or isin_f.status is FieldStatus.NOT_FOUND:
            return "unknown"
        n_missing = 0
        for b in blocks:
            flds = list(b.fields.values())
            if flds and all(
                    f.status in (FieldStatus.NOT_FOUND,
                                 FieldStatus.NOT_APPLICABLE)
                    for f in flds):
                n_missing += 1
        if n_missing >= len(blocks) - 1:
            return "partial"
        if n_missing:
            return "partial"
        return "found"
