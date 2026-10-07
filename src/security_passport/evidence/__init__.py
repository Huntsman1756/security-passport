"""Evidence acquisition helpers — raw archive layout.

``data/raw/<provider>/<retrieved_date>/<sha256>.<ext>`` — raw bytes
are never modified after write. Normalization reads from the
archive and records the artifact sha in the generation manifest.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utcnow() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def archive_raw(data_root: Path, provider: str, payload: bytes,
                ext: str, retrieved_at: str | None = None
                ) -> dict[str, Any]:
    """Write raw bytes to the immutable archive; return the
    artifact descriptor. Idempotent: identical bytes → same path."""
    sha = hashlib.sha256(payload).hexdigest()
    day = (retrieved_at or today())[:10]
    d = data_root / "raw" / provider / day
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{sha}.{ext}"
    if not p.exists():
        p.write_bytes(payload)
    return {"sha256": sha, "path": str(p), "bytes": len(payload),
            "retrieved_at": retrieved_at or utcnow()}


def append_observation(data_root: Path, provider: str,
                       record: dict[str, Any]) -> None:
    """Append one observed-history record to the provider journal."""
    obs = data_root / "observations"
    obs.mkdir(parents=True, exist_ok=True)
    record = dict(record)
    record.setdefault("observed_at", utcnow())
    with (obs / f"{provider}.jsonl").open("a",
                                        encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True,
                           ensure_ascii=False) + "\n")


def read_observations(data_root: Path, provider: str
                      ) -> list[dict[str, Any]]:
    p = data_root / "observations" / f"{provider}.jsonl"
    if not p.exists():
        return []
    return [json.loads(ln) for ln in
            p.read_text(encoding="utf-8").splitlines() if ln.strip()]
