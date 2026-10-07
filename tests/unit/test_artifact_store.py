"""Artifact store — ported OI/posttrade model."""
from __future__ import annotations

from pathlib import Path

from security_passport.evidence.store import (
    ArtifactStore,
    RetrievalAttempt,
)


def _put(s: ArtifactStore, data: bytes, period: str = "p1"):
    return s.put_blob(
        data=data, provider="ecb", source_family="ea",
        period=period, source_locator="https://x/y")


def test_content_addressed_write_once(tmp_path: Path) -> None:
    s = ArtifactStore(tmp_path)
    a1, c1 = _put(s, b"hello")
    a2, c2 = _put(s, b"hello")  # same bytes + period → same artifact
    assert c1 and not c2
    assert a1.sha256 == a2.sha256
    assert a1.source_id == a2.source_id
    assert s.read_blob(a1.sha256) == b"hello"


def test_changed_bytes_new_blob_supersedes(tmp_path: Path) -> None:
    s = ArtifactStore(tmp_path)
    a1, _ = _put(s, b"v1")
    a2, c2 = _put(s, b"v2")  # same locator/period, new bytes
    assert c2
    assert a2.sha256 != a1.sha256
    assert a2.supersedes == a1.source_id
    # both blobs preserved — never overwritten
    assert s.read_blob(a1.sha256) == b"v1"
    assert s.read_blob(a2.sha256) == b"v2"


def test_same_bytes_new_period_new_artifact(tmp_path: Path) -> None:
    s = ArtifactStore(tmp_path)
    a1, _ = _put(s, b"same", "p1")
    a2, c2 = _put(s, b"same", "p2")
    assert c2
    assert a1.sha256 == a2.sha256
    assert a1.source_id != a2.source_id


def test_metadata_separate_from_bytes(tmp_path: Path) -> None:
    s = ArtifactStore(tmp_path)
    a, _ = s.put_blob(
        data=b"data", provider="p", source_family="f",
        period="p", source_locator="https://x",
        content_type="text/csv", etag='"abc"',
        last_modified="Mon, 01 Jan 2024",
        parser_version="1")
    assert a.etag == '"abc"'
    assert a.last_modified == "Mon, 01 Jan 2024"
    assert a.content_type == "text/csv"
    assert a.parser_version == "1"


def test_attempt_ledger_records_failures(tmp_path: Path) -> None:
    s = ArtifactStore(tmp_path)
    s.record_attempt(RetrievalAttempt(
        attempt_id="a1", source_locator="https://x",
        provider="ecb", started_at="t", completed_at="t",
        status="NETWORK_ERROR", error_class="TimeoutError"))
    s.record_attempt(RetrievalAttempt(
        attempt_id="a2", source_locator="https://x",
        provider="ecb", started_at="t", completed_at="t",
        status="SUCCESS", http_status=200, etag='"e"',
        last_modified="d", content_type="text/plain",
        byte_length=4, blob_id="sha"))
    attempts = s.attempts()
    assert len(attempts) == 2
    assert attempts[0].status == "NETWORK_ERROR"
    assert attempts[1].etag == '"e"'


def test_verify_integrity(tmp_path: Path) -> None:
    s = ArtifactStore(tmp_path)
    a, _ = _put(s, b"bytes")
    assert s.verify(a)
    assert s.verify_all() == []
    # corrupt the blob
    p = s._blob_path(a.sha256)
    p.write_bytes(b"tampered")
    assert not s.verify(a)
    assert s.verify_all() == [a.source_id]
