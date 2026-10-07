"""Generations — build → validate → atomic CURRENT publish.

Same pattern OpenInstrument proved upstream, at our scale:
a generation is a self-contained directory of stores + a manifest;
``CURRENT`` is a text file naming the live generation. Readers
pin CURRENT once per request — a mid-request flip never mixes
stores.

Publish protocol:

1. build candidate dir ``read/.build-<name>/``
2. write manifest (per-file sha256 inventory + semantic fingerprint)
3. validate (stores readable, schema, manifest verified)
4. rename to ``read/generation-<name>`` and write CURRENT atomically
   (tmp file + os.replace)

Rollback = write a previous generation name to CURRENT.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

CURRENT = "CURRENT"


def generation_name(read_root: Path) -> str | None:
    f = read_root / CURRENT
    if not f.exists():
        return None
    name = f.read_text(encoding="utf-8").strip()
    return name or None


def current(read_root: Path) -> Path | None:
    name = generation_name(read_root)
    if not name:
        return None
    p = read_root / name
    return p if p.is_dir() else None


def next_name(read_root: Path) -> str:
    existing = sorted(p.name for p in read_root.glob("generation-*")
                      if p.is_dir())
    n = 1
    if existing:
        n = int(existing[-1].rsplit("-", 1)[-1]) + 1
    return f"generation-{n:04d}"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(root: Path) -> dict[str, str]:
    """relative path → sha256 for every file in a generation."""
    out: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name != "manifest.json":
            out[p.relative_to(root).as_posix()] = sha256_file(p)
    return out


_VOLATILE = {"created_at", "retrieved_at", "observed_at",
             "generated_at", "locked_at"}


def _strip_volatile(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip_volatile(v) for k, v in obj.items()
                if k not in _VOLATILE}
    if isinstance(obj, list):
        return [_strip_volatile(v) for v in obj]
    return obj


def semantic_fingerprint(manifest: dict[str, Any]) -> str:
    """Deterministic fingerprint over semantic content — file
    inventory, volatile timestamps, and the generation name are
    excluded so an identical rebuild fingerprints identically."""
    sem = {k: v for k, v in manifest.items()
           if k not in ("files", "generation")}
    raw = json.dumps(_strip_volatile(sem), sort_keys=True,
                     ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def validate(root: Path) -> list[str]:
    """Generation-level integrity: manifest inventory verifies,
    manifest schema present, stores dir exists."""
    errs: list[str] = []
    man_path = root / "manifest.json"
    if not man_path.exists():
        return ["manifest.json missing"]
    try:
        man = json.loads(man_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"manifest.json invalid: {e}"]
    if man.get("schema_version") != "1":
        errs.append("manifest schema_version != 1")
    files = man.get("files") or {}
    for rel, sha in files.items():
        p = root / rel
        if not p.exists():
            errs.append(f"manifest file missing: {rel}")
        elif sha256_file(p) != sha:
            errs.append(f"sha mismatch: {rel}")
    if not (root / "stores").is_dir():
        errs.append("stores/ missing")
    return errs


def publish(read_root: Path, candidate: Path, name: str
            ) -> Path:
    """Candidate → generation-<name> + CURRENT flip (atomic)."""
    target = read_root / name
    if target.exists():
        raise FileExistsError(target)
    candidate.rename(target)
    tmp = read_root / ".CURRENT.tmp"
    tmp.write_text(name, encoding="utf-8")
    os.replace(tmp, read_root / CURRENT)
    return target


def rollback(read_root: Path, name: str) -> None:
    target = read_root / name
    if not target.is_dir():
        raise FileNotFoundError(f"no such generation: {name}")
    tmp = read_root / ".CURRENT.tmp"
    tmp.write_text(name, encoding="utf-8")
    os.replace(tmp, read_root / CURRENT)


def clean_build_dirs(read_root: Path) -> None:
    for p in read_root.glob(".build-*"):
        if p.is_dir():
            shutil.rmtree(p)
