"""Artifact store — content-addressed, write-once.

PORT_PATTERN: combines the OpenInstrument artifact-store model
(`openinstrument/artifacts/store.py` @ v0.4.0, MIT, same author —
ledger + sha256 identity + supersedes) with posttrade-europe's
capture discipline (`capture/store.py` + `models.py` @ d0f440a,
Apache-2.0 — RetrievalAttempt as first-class data: http_status,
etag, last_modified, redirect chain; failures recorded, not
dropped).

Layout under ``root``::

    blobs/<hh>/<sha256>        # write-once raw bytes
    artifacts.jsonl            # append-only SourceArtifact ledger
    attempts.jsonl             # append-only RetrievalAttempt ledger

Rules:
- Blob identity is SHA-256 of the payload bytes — never the URL.
- Same bytes re-registered → existing artifact, no new entry.
- Same locator with different bytes → new artifact, ``supersedes``
  the previous for that (provider, source_family, period).
- A failed retrieval is an observation: logged as an attempt with
  no blob, never silently dropped.
- Atomic write: tempfile → fsync → rename. Never modify a blob.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

BLOBS = "blobs"
ARTIFACTS = "artifacts.jsonl"
ATTEMPTS = "attempts.jsonl"


@dataclass(frozen=True)
class RetrievalAttempt:
    """One fetch attempt — success or failure. Failures are data."""
    attempt_id: str
    source_locator: str
    provider: str
    started_at: str
    completed_at: str
    status: str                # SUCCESS | HTTP_ERROR | NETWORK_ERROR | ...
    http_status: int | None = None
    etag: str | None = None
    last_modified: str | None = None
    content_type: str | None = None
    byte_length: int | None = None
    blob_id: str | None = None   # sha256, only when bytes arrived
    error_class: str | None = None


@dataclass(frozen=True)
class SourceArtifact:
    """Metadata for one immutable blob — separate from the bytes."""
    source_id: str             # "<prefix>/<period>/<sha256>"
    provider: str
    source_family: str         # e.g. "ecb_eligible_assets"
    period: str                # natural dedupe key (snapshot/date)
    source_locator: str        # canonical URL/path
    retrieved_at: str          # ISO-8601 UTC
    sha256: str
    size_bytes: int
    content_type: str | None
    etag: str | None = None
    last_modified: str | None = None
    parser_version: str = ""   # version that normalized it — NOT the
    supersedes: str | None = None
    storage_path: str = ""     # relative to root


def utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds") \
        .replace("+00:00", "Z")


class ArtifactStore:
    """Write-once blob store + append-only ledgers."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        (self.root / BLOBS).mkdir(parents=True, exist_ok=True)

    # ---- blob storage ------------------------------------------------------

    def _blob_path(self, digest: str) -> Path:
        return self.root / BLOBS / digest[:2] / digest

    def _write_blob(self, digest: str, data: bytes) -> Path:
        target = self._blob_path(digest)
        if target.exists():
            return target  # idempotent — same content, same path
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=target.parent, suffix=".part")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, target)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        return target

    def read_blob(self, digest: str) -> bytes | None:
        p = self._blob_path(digest)
        return p.read_bytes() if p.exists() else None

    # ---- ledgers -----------------------------------------------------------

    def artifacts(self) -> list[SourceArtifact]:
        p = self.root / ARTIFACTS
        if not p.exists():
            return []
        return [SourceArtifact(**json.loads(ln))
                for ln in p.read_text(encoding="utf-8").splitlines()
                if ln.strip()]

    def attempts(self) -> list[RetrievalAttempt]:
        p = self.root / ATTEMPTS
        if not p.exists():
            return []
        return [RetrievalAttempt(**json.loads(ln))
                for ln in p.read_text(encoding="utf-8").splitlines()
                if ln.strip()]

    def _append_jsonl(self, name: str,
                      obj: RetrievalAttempt | SourceArtifact) -> None:
        with open(self.root / name, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(obj), sort_keys=True)
                    + "\n")

    def latest_for_period(
            self, period: str, *, provider: str,
            source_family: str | None = None) -> SourceArtifact | None:
        arts = [a for a in self.artifacts()
                if a.period == period and a.provider == provider
                and (source_family is None
                     or a.source_family == source_family)]
        return arts[-1] if arts else None

    def by_sha(self, digest: str) -> SourceArtifact | None:
        for a in self.artifacts():
            if a.sha256 == digest:
                return a
        return None

    # ---- capture -------------------------------------------------------------

    def record_attempt(self, attempt: RetrievalAttempt) -> None:
        self._append_jsonl(ATTEMPTS, attempt)

    def put_blob(
            self, *, data: bytes, provider: str, source_family: str,
            period: str, source_locator: str,
            content_type: str | None = None,
            etag: str | None = None,
            last_modified: str | None = None,
            retrieved_at: str | None = None,
            source_id_prefix: str = "sp",
            parser_version: str = "") -> tuple[SourceArtifact, bool]:
        """Store raw bytes → (artifact, created_new_version).

        Idempotent on identical bytes for the same
        (provider, source_family, period)."""
        digest = sha256(data).hexdigest()
        prior = self.latest_for_period(
            period, provider=provider, source_family=source_family)
        if prior is not None and prior.sha256 == digest:
            return prior, False

        path = self._write_blob(digest, data)
        artifact = SourceArtifact(
            source_id=f"{source_id_prefix}/{period}/{digest}",
            provider=provider,
            source_family=source_family,
            period=period,
            source_locator=source_locator,
            retrieved_at=retrieved_at or utcnow(),
            sha256=digest,
            size_bytes=len(data),
            content_type=content_type,
            etag=etag, last_modified=last_modified,
            parser_version=parser_version,
            supersedes=prior.source_id if prior else None,
            storage_path=str(path.relative_to(self.root)
                             ).replace("\\", "/"),
        )
        self._append_jsonl(ARTIFACTS, artifact)
        return artifact, True

    # ---- integrity -----------------------------------------------------------

    def verify(self, artifact: SourceArtifact) -> bool:
        data = self.read_blob(artifact.sha256)
        return data is not None \
            and sha256(data).hexdigest() == artifact.sha256

    def verify_all(self) -> list[str]:
        return [a.source_id for a in self.artifacts()
                if not self.verify(a)]
