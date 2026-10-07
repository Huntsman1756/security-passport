"""Public status vocabulary — the only states a field may carry.

``status`` answers *how we know*; ``QualityFlag`` answers *what is
wrong or notable about the evidence*. The two dimensions never
substitute for each other (ADR-004).
"""
from __future__ import annotations

from enum import Enum


class FieldStatus(str, Enum):
    """Epistemology of a passport field.

    REPORTED        — published directly by a source.
    DERIVED         — deterministic versioned transform over
                      reported facts.
    INFERRED        — operational conclusion sustained by a rule,
                      not literally published.
    NOT_FOUND       — searched reasonably, insufficient evidence.
    NOT_APPLICABLE  — the field does not apply to this instrument.
    CONFLICT        — incompatible assertions, no safe winner.
    """

    REPORTED = "reported"
    DERIVED = "derived"
    INFERRED = "inferred"
    NOT_FOUND = "not_found"
    NOT_APPLICABLE = "not_applicable"
    CONFLICT = "conflict"


class QualityFlag(str, Enum):
    """Source-quality diagnostics — never a status."""

    SOURCE_DEFAULT_VALUE = "source_default_value"
    POSSIBLE_SOURCE_DEFAULT = "possible_source_default"
    LATE_REPORT = "late_report"
    CORRECTED_AFTER_TERMINATION = "corrected_after_termination"
    SOURCE_CONFLICT = "source_conflict"
    HISTORICAL_LEFT_CENSORING = "historical_left_censoring"
    PARTIAL_TEMPORAL_COVERAGE = "partial_temporal_coverage"
    STALE_SOURCE = "stale_source"
    SCHEMA_MIGRATION = "schema_migration"


class TemporalAnswerState(str, Enum):
    """What the available evidence can honestly support at a
    requested date — orthogonal to ``FieldStatus``.

    AVAILABLE          — evidence admissible at T supports the
                         block's answer.
    PARTIAL            — part of the block is admissible at T; the
                         rest is explicitly marked.
    OUTSIDE_COVERAGE   — T precedes (or follows) the coverage we
                         can defend; no current value is
                         substituted.
    UNAVAILABLE        — the source family has no temporal
                         semantics we can honour.
    """

    AVAILABLE = "available"
    PARTIAL = "partial"
    OUTSIDE_COVERAGE = "outside_coverage"
    UNAVAILABLE = "unavailable"


class TemporalBasis(str, Enum):
    """How the temporal coverage behind a field was obtained."""

    NATIVE_HISTORY = "native_history"
    RECONSTRUCTED = "reconstructed"
    OBSERVED_HISTORY = "observed_history"
    CURRENT_ONLY = "current_only"


class SourceTimeSemantics(str, Enum):
    """What the source's timestamps actually mean."""

    PROVIDER_PUBLICATION_TIME = "provider_publication_time"
    EFFECTIVE_TIME = "effective_time"
    RETRIEVAL_TIME = "retrieval_time"
