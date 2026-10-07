"""ISO 10383 MIC contract — cp1252 handling + lookup."""
from __future__ import annotations

from pathlib import Path

from security_passport.providers import mic

FIXTURE = Path(__file__).resolve().parent.parent / \
    "fixtures" / "corpus" / "mic" / "mic_slice.csv"


def test_parse_cp1252() -> None:
    rows = mic.parse(mic.decode_csv(FIXTURE.read_bytes()))
    assert rows
    xetr = rows.get("XETR")
    assert xetr is not None
    assert "XETRA" in xetr.market_name.upper() or \
        "XETR" in xetr.market_name.upper()


def test_oprt_sgmt_present() -> None:
    rows = mic.parse(mic.decode_csv(FIXTURE.read_bytes()))
    assert any(r.oprt_sgmt == "SGMT" for r in rows.values())
    assert any(r.oprt_sgmt == "OPRT" for r in rows.values())


def test_status_codes() -> None:
    rows = mic.parse(mic.decode_csv(FIXTURE.read_bytes()))
    statuses = {r.status for r in rows.values()}
    assert statuses <= {"ACTIVE", "DELETED", "MODIFIED", "EXPIRED",
                        ""}
