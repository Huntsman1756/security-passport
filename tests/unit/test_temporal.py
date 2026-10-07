"""Sentinel-aware date normalization — spec §16/§30."""
from __future__ import annotations

from security_passport.domain.status import QualityFlag
from security_passport.temporal import (
    min_real_date,
    normalize_firds_date,
)


def test_none_and_empty() -> None:
    assert normalize_firds_date(None).value is None
    assert normalize_firds_date("").value is None
    assert normalize_firds_date("  ").value is None


def test_sentinel_9999() -> None:
    nd = normalize_firds_date("9999-12-31T00:00:00")
    assert nd.value is None
    assert nd.is_sentinel
    assert nd.raw == "9999-12-31T00:00:00"  # raw preserved
    assert QualityFlag.SOURCE_DEFAULT_VALUE in nd.flags


def test_other_9xxx_years_flagged() -> None:
    nd = normalize_firds_date("9500-01-01")
    assert nd.value is None
    assert nd.is_sentinel


def test_iso_datetime_to_date() -> None:
    nd = normalize_firds_date("2023-06-21T13:36:15.024Z")
    assert nd.value == "2023-06-21"
    assert nd.raw == "2023-06-21T13:36:15.024Z"


def test_end_of_day_marker() -> None:
    nd = normalize_firds_date("2030-07-17T23:59:59.999Z")
    assert nd.value == "2030-07-17"
    assert nd.end_of_day


def test_malformed_kept_as_possible_default() -> None:
    nd = normalize_firds_date("not-a-date")
    assert nd.value is None
    assert QualityFlag.POSSIBLE_SOURCE_DEFAULT in nd.flags


def test_min_real_date_skips_sentinels() -> None:
    dates = [normalize_firds_date("9999-12-31T00:00:00"),
             normalize_firds_date("2024-05-01T00:00:00Z"),
             normalize_firds_date("2023-02-14T08:00:00Z")]
    best = min_real_date(dates)
    assert best is not None
    assert best.value == "2023-02-14"
    assert QualityFlag.SOURCE_DEFAULT_VALUE in best.flags


def test_min_real_date_all_sentinel() -> None:
    assert min_real_date([normalize_firds_date("9999-12-31")]
                         ) is None
