"""Evidence layer — immutable raw archive + observation ledgers.

Backed by ``evidence.store.ArtifactStore`` (ported from the
OpenInstrument/posttrade-europe models — see
``docs/reuse/REUSE_AUDIT_V2.md``). Raw bytes are content-addressed
write-once blobs; retrieval attempts are first-class data.

``data/raw/artifacts/``
    blobs/<hh>/<sha256>, artifacts.jsonl, attempts.jsonl
``data/observations/``
    append-only provider journals (normalized observation records)
"""
from __future__ import annotations

import json
import urllib.request
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from security_passport import user_agent
from security_passport.evidence.store import (
    ArtifactStore,
    RetrievalAttempt,
    SourceArtifact,
    utcnow,
)

__all__ = [
    "ArtifactStore", "RetrievalAttempt", "SourceArtifact",
    "append_observation", "archive_raw", "capture_fetch",
    "read_observations", "store_for", "today", "utcnow",
]

_UA = {"User-Agent": user_agent() +
       " (+https://github.com/Huntsman1756/security-passport; "
       "public-data observation)"}


def today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def store_for(data_root: Path) -> ArtifactStore:
    return ArtifactStore(Path(data_root) / "raw" / "artifacts")


def archive_raw(data_root: Path, provider: str, payload: bytes,
                ext: str, retrieved_at: str | None = None,
                *, source_family: str = "",
                source_locator: str = "",
                period: str = "",
                parser_version: str = "") -> dict[str, Any]:
    """Write raw bytes to the immutable content-addressed store.

    Returns the artifact descriptor. Idempotent: identical bytes
    for the same (provider, family, period) return the existing
    artifact without a new ledger entry."""
    store = store_for(data_root)
    art, created = store.put_blob(
        data=payload,
        provider=provider,
        source_family=source_family or provider,
        period=period or (retrieved_at or today())[:10],
        source_locator=source_locator or provider,
        content_type=None,
        retrieved_at=retrieved_at,
        parser_version=parser_version)
    return {"sha256": art.sha256, "source_id": art.source_id,
            "storage_path": art.storage_path,
            "bytes": art.size_bytes,
            "retrieved_at": art.retrieved_at,
            "created": created}


def capture_fetch(
        data_root: Path, *, url: str, provider: str,
        source_family: str, period: str,
        source_page: str = "",
        parser_version: str = "",
        timeout: int = 120) -> tuple[bytes, SourceArtifact]:
    """Fetch → record RetrievalAttempt → store blob → return both.

    Failures are recorded as attempts with no blob and re-raised —
    the attempt ledger survives even when the fetch doesn't."""
    store = store_for(data_root)
    started = utcnow()
    status, ctype, etag, lastmod = "NETWORK_ERROR", None, None, None
    http_status: int | None = None
    data = b""
    err: str | None = None
    try:
        with urllib.request.urlopen(
                urllib.request.Request(url, headers=_UA),
                timeout=timeout) as resp:
            data = resp.read()
            http_status = resp.status
            ctype = resp.headers.get("Content-Type")
            etag = resp.headers.get("ETag")
            lastmod = resp.headers.get("Last-Modified")
            status = "SUCCESS" if resp.status < 400 else "HTTP_ERROR"
    except urllib.error.HTTPError as e:
        http_status = e.code
        status = "HTTP_ERROR"
        err = f"HTTP {e.code}"
        data = e.read() if e.fp else b""
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        status = ("TIMEOUT" if "timed out" in err.lower()
                  else "NETWORK_ERROR")
    attempt = RetrievalAttempt(
        attempt_id=uuid.uuid4().hex[:12],
        source_locator=url, provider=provider,
        started_at=started, completed_at=utcnow(),
        status=status, http_status=http_status,
        etag=etag, last_modified=lastmod,
        content_type=ctype,
        byte_length=len(data) if data else None,
        blob_id=None, error_class=err)
    if status != "SUCCESS" or not data:
        store.record_attempt(attempt)
        raise OSError(
            f"capture failed {provider}/{source_family} "
            f"{url}: {status} {err or ''}")
    art, _ = store.put_blob(
        data=data, provider=provider, source_family=source_family,
        period=period, source_locator=url,
        content_type=ctype, etag=etag, last_modified=lastmod,
        retrieved_at=started,
        parser_version=parser_version)
    attempt = RetrievalAttempt(
        **{**attempt.__dict__, "blob_id": art.sha256})
    store.record_attempt(attempt)
    return data, art


def append_observation(data_root: Path, provider: str,
                       record: dict[str, Any]) -> None:
    """Append one observed-history record to the provider journal."""
    obs = Path(data_root) / "observations"
    obs.mkdir(parents=True, exist_ok=True)
    record = dict(record)
    record.setdefault("observed_at", utcnow())
    with (obs / f"{provider}.jsonl").open("a",
                                        encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True,
                           ensure_ascii=False) + "\n")


def read_observations(data_root: Path, provider: str
                      ) -> list[dict[str, Any]]:
    p = Path(data_root) / "observations" / f"{provider}.jsonl"
    if not p.exists():
        return []
    return [json.loads(ln) for ln in
            p.read_text(encoding="utf-8").splitlines() if ln.strip()]
