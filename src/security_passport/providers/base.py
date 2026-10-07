"""Provider contracts — the seam between acquisition and domain.

``InstrumentProvider`` returns typed facts, never raw HTTP bodies.
Normalization (sentinels, statuses) happens in the passport
builder so providers stay thin and honest.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


# ---- upstream instrument facts -------------------------------------------

@dataclass(frozen=True)
class InstrumentFacts:
    """Canonical instrument row as served upstream."""

    isin: str
    found: bool
    cfi: str | None = None
    cfi_state: str = ""
    fisn: str | None = None
    fisn_state: str = ""
    full_name: str | None = None
    full_name_state: str = ""
    notional_currency: str | None = None
    notional_currency_state: str = ""
    issuer_lei: str | None = None
    issuer_lei_state: str = ""
    issuer_lei_assertions: int = 0
    competent_authority: str | None = None
    competent_authority_state: str = ""
    cfi_letter: str = ""
    firds_snapshot: str = ""
    n_firds_records: int = 0


@dataclass(frozen=True)
class ListingFact:
    """One ISIN×venue record — verbatim provider dates (sentinels
    included; normalization is a passport-layer rule)."""

    venue_mic: str
    relevant_venue: str
    issuer_requested_admission: str
    admission_approval_date: str | None
    admission_request_date: str | None
    first_trade_date: str | None
    termination_date: str | None
    locator: str


@dataclass(frozen=True)
class IssuerAssertionFact:
    lei: str
    locator: str
    venue: str = ""


@dataclass(frozen=True)
class IssuerFacts:
    isin: str
    found: bool
    canonical_lei: str | None = None
    state: str = ""
    assertion_count: int = 0
    gleif_assertions: tuple[IssuerAssertionFact, ...] = ()
    firds_assertions: tuple[IssuerAssertionFact, ...] = ()
    entity: dict[str, Any] | None = None


@dataclass(frozen=True)
class IdentifierFact:
    level: str
    scheme: str
    value: str
    provider: str = ""


@dataclass(frozen=True)
class SearchCandidate:
    isin: str
    full_name: str | None
    cfi: str | None = None
    kind: str = ""


@dataclass(frozen=True)
class UpstreamEvidence:
    """Artifact-level provenance carried through verbatim."""

    firds: tuple[dict[str, str], ...] = ()
    gleif: tuple[dict[str, str], ...] = ()
    other: tuple[dict[str, str], ...] = ()


class InstrumentProvider(Protocol):
    """Upstream instrument-facts port (ADR-002)."""

    def name(self) -> str: ...
    def generation(self) -> str: ...
    def instrument(self, isin: str) -> InstrumentFacts: ...
    def listings(self, isin: str) -> list[ListingFact]: ...
    def issuer(self, isin: str) -> IssuerFacts: ...
    def identifiers(self, isin: str) -> list[IdentifierFact]: ...
    def upstream_evidence(self, isin: str) -> UpstreamEvidence: ...
    def fund_roles(self, isin: str) -> list[dict[str, str]]: ...
    def search(self, q: str) -> list[SearchCandidate]: ...


# ---- own-source store facts ----------------------------------------------

@dataclass(frozen=True)
class EcbAssetFact:
    """One row of the ECB eligible marketable assets list."""

    isin: str
    haircut_category: str
    asset_type: str
    reference_market: str
    denomination_currency: str
    issuance_date: str
    maturity_date: str
    issuer_csd: str
    coupon_rate: str
    issuer_name: str
    issuer_residence: str
    issuer_group: str
    guarantor_name: str
    guarantor_residence: str
    guarantor_group: str
    coupon_definition: str
    haircut: str
    haircut_own_use: str
    covered_bond_flag: str
    climate_factor: str
    snapshot: str          # e.g. "261006"
    retrieved_at: str


@dataclass(frozen=True)
class PriiiDocument:
    """One prospectus filing (parent) with its instrument/issuer/
    related-document children resolved."""

    root_id: str
    document_type: str
    document_type_descr: str
    prospectus_type: str
    structure_type: str
    national_document_id: str
    home_member_state: str
    home_member_state_code: str
    member_states: tuple[str, ...]
    is_passported: bool
    approval_filing_date: str
    first_passporting_date: str
    last_passporting_date: str
    doc_last_update_date: str
    document_rfss_id: str
    download_url: str
    party_name: str
    issuer_lei: str
    issuer_name: str
    offeror_lei: str
    offeror_name: str
    related_document_ids: tuple[str, ...]
    document_languages: str
    ifii_doc_type: str
    ifii_mat_exp_date: str
    ifii_securities_type: str
    ifii_trading_venue: str


@dataclass(frozen=True)
class PriiiFacts:
    isin: str
    searched: bool
    documents: tuple[PriiiDocument, ...]
    observed_at: str
    artifact_id: str


@dataclass(frozen=True)
class SssFact:
    sss_id: str
    name: str
    country: str
    observed_at: str
    page_stamp: str          # "Last updated" date on the ECB page


@dataclass(frozen=True)
class SssLinkFact:
    investor_sss: str
    issuer_sss: str
    intermediaries: tuple[str, ...] = ()
    operated_by: str = ""
    observed_at: str = ""
    page_stamp: str = ""


@dataclass(frozen=True)
class MicFact:
    mic: str
    market_name: str
    operating_mic: str
    oprt_sgmt: str
    country: str
    status: str


class PassportStore(Protocol):
    """Read surface over the pinned own-source generation."""

    def generation(self) -> str: ...
    def ecb_asset(self, isin: str) -> EcbAssetFact | None: ...
    def ecb_snapshot(self) -> str: ...
    def ecb_retrieved_at(self) -> str: ...
    def priii(self, isin: str) -> PriiiFacts | None: ...
    def eligible_sss(self) -> list[SssFact]: ...
    def eligible_links(self) -> list[SssLinkFact]: ...
    def mic(self, mic: str) -> MicFact | None: ...


# ---- errors ---------------------------------------------------------------

@dataclass
class ProviderError(Exception):
    """A source is unreachable or returned an unusable contract.

    Carried per-block: a fallen provider degrades its fields to
    ``not_found``/warnings, never to invented values."""

    provider: str
    message: str
    code: str = "SOURCE_UNAVAILABLE"
    cause: Exception | None = field(default=None, compare=False)

    def __str__(self) -> str:
        return f"{self.provider}: {self.message}"
