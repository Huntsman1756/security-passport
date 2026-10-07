"""Update pipeline — scheduled own-source ingestion.

Steps (spec §62):

1. acquire lock (one updater at a time)
2. pin the upstream generation (informational, recorded)
3. fetch own sources → immutable raw archive
4. normalize into a staging generation
5. build manifest (per-file sha + semantic fingerprint)
6. validate the generation
7. atomically publish CURRENT

A failure at any step leaves CURRENT untouched. Re-running with no
new data must be identity-preserving (same semantic fingerprint).
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from security_passport import evidence
from security_passport.providers import (
    ecb_assets,
    ecb_sss,
    esma_prospectus,
    mic,
)
from security_passport.storage import generations

UPDATE_LOCK = "update.lock"

# ISINs we ingest PRIII for at update time — the observed corpus.
# Grows when operators run `security-passport refresh <isin>`.
DEFAULT_PRIII_CORPUS: list[str] = []


class UpdateError(Exception):
    pass


def _lock_path(data_root: Path) -> Path:
    return data_root / UPDATE_LOCK


def acquire_lock(data_root: Path) -> Path:
    """Single-writer lockfile; refuses on a live lock."""
    lp = _lock_path(data_root)
    data_root.mkdir(parents=True, exist_ok=True)
    try:
        fd = lp.open("x", encoding="utf-8")
    except FileExistsError as e:
        raise UpdateError(
            f"update lock held: {lp} — remove if stale") from e
    fd.write(json.dumps({"locked_at": evidence.utcnow()}))
    fd.close()
    return lp


def release_lock(lp: Path) -> None:
    import contextlib
    with contextlib.suppress(FileNotFoundError):
        lp.unlink()


def _write_parquet(rows: list[dict[str, Any]],
                   path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        # write an empty table with a stable schema so the store
        # can always open the file
        table = pa.table({"_empty": pa.array([], type=pa.string())})
    else:
        table = pa.Table.from_pylist(rows)
    pq.write_table(table, path)


def build_stores(
        staging: Path,
        ecb_rows: list[dict[str, Any]],
        sss_payload: dict[str, Any],
        mic_rows: dict[str, Any],
        priii_payloads: list[dict[str, Any]],
        meta: dict[str, Any]) -> None:
    stores = staging / "stores"
    stores.mkdir(parents=True, exist_ok=True)
    _write_parquet(ecb_rows, stores / "ecb_assets.parquet")
    _write_parquet(
        [{"mic": r.mic, "operating_mic": r.operating_mic,
          "oprt_sgmt": r.oprt_sgmt, "market_name": r.market_name,
          "acronym": r.acronym, "country": r.country,
          "city": r.city, "status": r.status, "lei": r.lei}
         for r in mic_rows.values()],
        stores / "mic.parquet")
    (stores / "sss.json").write_text(
        json.dumps(sss_payload, sort_keys=True, ensure_ascii=False,
                   indent=1), encoding="utf-8")
    priii_dir = stores / "priii"
    priii_dir.mkdir(exist_ok=True)
    for payload in priii_payloads:
        isin = payload.get("isin") or ""
        if isin:
            (priii_dir / f"{isin}.json").write_text(
                json.dumps(payload, sort_keys=True,
                           ensure_ascii=False, indent=1),
                encoding="utf-8")
    (stores / "meta.json").write_text(
        json.dumps(meta, sort_keys=True, ensure_ascii=False,
                   indent=1), encoding="utf-8")


def run_update(
        data_root: Path,
        priii_isins: list[str] | None = None,
        *,
        fetch_fn: Any = None,
        priii_fn: Any = None,
        upstream_generation: str = "") -> dict[str, Any]:
    """One full update cycle. ``fetch_fn``/``priii_fn`` are
    injectable for tests/offline rebuilds."""
    data_root = Path(data_root)
    lp = acquire_lock(data_root)
    try:
        fetched: dict[str, Any] = {}
        meta: dict[str, Any] = {}

        if fetch_fn is None:
            # ---- ECB eligible assets --------------------------------
            url, snap = ecb_assets.latest_url()
            if not url:
                raise UpdateError(
                    "ECB download area: no ea_csv link found")
            raw, sha = ecb_assets.download(url)
            art = evidence.archive_raw(
                data_root, "ecb_eligible_assets", raw, "csv.gz")
            ecb_rows = [ecb_assets.normalize(r, snap,
                                           evidence.utcnow())
                        for r in ecb_assets.parse(raw)]
            meta["ecb_eligible_assets"] = {
                "url": url, "snapshot": snap, "sha256": sha,
                "rows": len(ecb_rows),
                "retrieved_at": art["retrieved_at"]}
            evidence.append_observation(
                data_root, "ecb_eligible_assets",
                {"snapshot": snap, "sha256": sha,
                 "rows": len(ecb_rows)})
            fetched["ecb_rows"] = ecb_rows

            # ---- ECB SSS + links ------------------------------------
            sss_html, sss_sha = ecb_sss.fetch(ecb_sss.SSS_PAGE)
            links_html, links_sha = ecb_sss.fetch(ecb_sss.LINKS_PAGE)
            evidence.archive_raw(data_root, "ecb_sss_links",
                                 sss_html.encode(), "html")
            evidence.archive_raw(data_root, "ecb_sss_links",
                                 links_html.encode(), "html")
            sss_payload = ecb_sss.parse_pages(sss_html, links_html)
            sss_payload["observed_at"] = evidence.utcnow()
            meta["ecb_sss_links"] = {
                "sss_page_stamp": sss_payload["sss_page_stamp"],
                "links_page_stamp": sss_payload["links_page_stamp"],
                "n_sss": len(sss_payload["sss"]),
                "n_links": len(sss_payload["links"])}
            evidence.append_observation(
                data_root, "ecb_sss_links",
                {"sss_sha": sss_sha, "links_sha": links_sha,
                 "sss_page_stamp": sss_payload["sss_page_stamp"],
                 "links_page_stamp":
                     sss_payload["links_page_stamp"]})
            fetched["sss_payload"] = sss_payload

            # ---- MIC registry -----------------------------------------
            mic_bytes = mic.download()
            evidence.archive_raw(data_root, "iso10383_mic",
                                 mic_bytes, "csv")
            fetched["mic_rows"] = mic.parse(
                mic.decode_csv(mic_bytes))
            meta["iso10383_mic"] = {
                "rows": len(fetched["mic_rows"])}

            # ---- PRIII observed corpus ---------------------------------
            payloads: list[dict[str, Any]] = []
            for isin in sorted(set(
                    priii_isins or DEFAULT_PRIII_CORPUS)):
                fam = (priii_fn or
                       esma_prospectus.family_for_isin)(isin)
                fam["observed_at"] = evidence.utcnow()
                payloads.append(fam)
                evidence.archive_raw(
                    data_root, "esma_priii",
                    json.dumps(fam, sort_keys=True,
                               ensure_ascii=False).encode(), "json")
                evidence.append_observation(
                    data_root, "esma_priii",
                    {"isin": isin, "sha256": fam.get("sha256"),
                     "n_filings": len(fam.get("filings") or [])})
            meta["esma_priii"] = {"isin_count": len(payloads)}
            fetched["priii_payloads"] = payloads
        else:
            fetched = dict(fetch_fn())
            meta.update(fetched.pop("meta", {}) or {})

        meta["openinstrument_generation"] = upstream_generation

        # ---- staging generation --------------------------------------
        read_root = data_root / "read"
        read_root.mkdir(parents=True, exist_ok=True)
        generations.clean_build_dirs(read_root)
        name = generations.next_name(read_root)
        staging = read_root / f".build-{name}"
        staging.mkdir(parents=True)
        build_stores(
            staging,
            ecb_rows=fetched.get("ecb_rows") or [],
            sss_payload=fetched.get("sss_payload") or {},
            mic_rows=fetched.get("mic_rows") or {},
            priii_payloads=fetched.get("priii_payloads") or [],
            meta=meta)

        # ---- manifest + validate + publish ----------------------------
        man = {
            "schema_version": "1",
            "generation": name,
            "created_at": evidence.utcnow(),
            "providers": meta,
            "files": generations.inventory(staging),
        }
        man["semantic_fingerprint"] = \
            generations.semantic_fingerprint(man)
        (staging / "manifest.json").write_text(
            json.dumps(man, indent=1, sort_keys=True),
            encoding="utf-8")
        errs = generations.validate(staging)
        if errs:
            shutil.rmtree(staging)
            raise UpdateError(
                f"generation validation failed: {errs}")
        published = generations.publish(read_root, staging, name)
        return {"published": name, "root": str(published),
                "manifest": man}
    finally:
        release_lock(lp)


def rollback(data_root: Path, name: str) -> dict[str, str]:
    read_root = Path(data_root) / "read"
    generations.rollback(read_root, name)
    return {"restored": name}
