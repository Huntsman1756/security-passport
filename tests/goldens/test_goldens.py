"""Golden corpus — every expectation in goldens.yaml verified +
the release gate (unsupported_assertions = 0)."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]

from security_passport.domain.isin import checksum_ok, normalize
from security_passport.providers.fixtures import (
    FixtureInstrumentProvider,
    FixturePassportStore,
)
from security_passport.services.passport_builder import PassportBuilder
from security_passport.services.validate import (
    ValidationReport,
    check_passport,
)

CORPUS = "tests/fixtures/corpus"
GOLDENS = yaml.safe_load(
    Path("tests/fixtures/goldens.yaml").read_text(
        encoding="utf-8"))["goldens"]

_builder = PassportBuilder(
    FixtureInstrumentProvider(CORPUS),
    FixturePassportStore(CORPUS))
_report = ValidationReport()


def _resolve(d: dict, dotted: str):
    parts = dotted.split(".", 1)
    blk = d.get(parts[0])
    if isinstance(blk, dict):
        return blk.get(parts[1])
    return None


@pytest.mark.parametrize("g", GOLDENS, ids=lambda g: g["isin"])
def test_golden(g: dict) -> None:
    if not g.get("fixture"):
        return
    isin = normalize(g["isin"])
    p = _builder.build(isin, checksum_ok=checksum_ok(isin))
    check_passport(p, _report)
    d = p.to_dict()
    for key, want in (g.get("expected") or {}).items():
        if key == "overall_state":
            assert d["overall_state"] == want, f"{isin}: {key}"
        elif key.endswith("_at_least"):
            blk, fld = key.split(".", 1)
            fld = fld.removesuffix("_at_least")
            got = (d.get(blk) or {}).get(fld)
            n = len(got) if isinstance(got, list) else (
                got.get("value") if isinstance(got, dict) else 0)
            assert (n or 0) >= want, f"{isin}: {key} {n} < {want}"
        elif key == "api_error":
            continue
        else:
            f = _resolve(d, key) or {}
            for attr, wv in (want or {}).items():
                got = f.get(attr)
                assert got == wv, \
                    f"{isin}: {key}.{attr} = {got!r} != {wv!r}"


def test_release_gate() -> None:
    """unsupported_assertions must be zero across the corpus."""
    assert _report.unsupported == [], _report.unsupported[:5]
    assert _report.provenance_coverage == 1.0
