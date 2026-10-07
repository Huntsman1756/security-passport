"""security-passport CLI.

    security-passport <ISIN>                 human-readable passport
    security-passport <ISIN> --json          contract JSON
    security-passport <ISIN> --sources       searched-source summary
    security-passport <ISIN> --explain X     deterministic field
                                             explanation
    security-passport update                 ingest own sources →
                                             publish generation
    security-passport validate               golden-corpus release gate
    security-passport doctor                 environment check
    security-passport status                 service/generation state
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Any

import typer

from security_passport import __version__
from security_passport.config import load
from security_passport.domain.isin import checksum_ok, normalize
from security_passport.providers.fixtures import (
    FixtureInstrumentProvider,
    FixturePassportStore,
)
from security_passport.services.passport_builder import PassportBuilder

app = typer.Typer(
    name="security-passport",
    help="Evidence-backed operational passport for European "
         "financial instruments.",
    no_args_is_help=False)


def _runtime() -> tuple[Any, Any]:
    s = load()
    if s.provider == "openinstrument_api":
        from security_passport.providers.openinstrument.api import (
            OpenInstrumentApiProvider,
        )
        from security_passport.storage import generations
        from security_passport.storage.store import GenerationStore
        gen = generations.current(s.data_root / "read")
        store = (GenerationStore(gen) if gen
                 else FixturePassportStore(s.fixtures_dir))
        return OpenInstrumentApiProvider(
            s.openinstrument_url), store
    return (FixtureInstrumentProvider(s.fixtures_dir),
            FixturePassportStore(s.fixtures_dir))


def _status_color(status: str) -> str:
    return status


def _fmt_value(v: Any) -> str:
    if v is None:
        return "—"
    if isinstance(v, dict):
        return v.get("name") or v.get("code") or json.dumps(
            v, ensure_ascii=False)
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    return str(v)


def _print_field(label: str, f: dict[str, Any],
                 indent: str = "") -> None:
    val = _fmt_value(f.get("value"))
    st = f.get("status", "")
    tag = {"reported": "reported", "derived": "derived",
           "inferred": "inferred", "conflict": "CONFLICT",
           "not_found": "not found",
           "not_applicable": "n/a"}.get(st, st)
    flags = f.get("quality_flags") or []
    suffix = f"  [{tag}]" if tag else ""
    if flags:
        suffix += f"  ({', '.join(flags)})"
    print(f"{indent}{label:<22}{val:<44}{suffix}")


def _print_passport(d: dict[str, Any]) -> None:
    print()
    print("SECURITY PASSPORT")
    print("─" * 66)
    print(f"ISIN        {d['isin']}")
    print(f"Generated   {d['generated_at']}   generation "
          f"{d['generation']}   upstream "
          f"{d.get('openinstrument_generation') or '—'}")
    print(f"State       {d['overall_state']}")
    for w in d.get("warnings") or []:
        print(f"  warning: {w}")
    ident = d["identity"]
    print()
    print("IDENTITY")
    for k, label in (("cfi", "CFI"), ("fisn", "FISN"),
                     ("instrument_name", "Name"),
                     ("instrument_type", "Type"),
                     ("issuer_lei", "Issuer LEI"),
                     ("issuer_name", "Issuer"),
                     ("notional_currency", "Currency"),
                     ("maturity_date", "Maturity")):
        f = ident.get(k)
        if f:
            _print_field(label, f)
    roles = ident.get("entity_roles") or []
    if roles:
        print(f"  {'Entity roles':<22}" + "; ".join(
            f"{r['role']}={r['lei'][:12]}…" for r in roles[:4]))
    pm = d["primary_market"]
    print()
    print("PRIMARY MARKET")
    pf = pm.get("prospectus_found") or {}
    _print_field("Prospectus", pf)
    for k, label in (("home_member_state", "Home state"),
                     ("host_member_states", "Passport states"),
                     ("approval_filing_date", "Approval date"),
                     ("is_passported", "Passported")):
        f = pm.get(k)
        if f:
            _print_field(label, f)
    for doc in pm.get("document_graph") or []:
        print(f"    doc: {doc['document_type_descr'] or doc['document_type']}"
              f"  {doc['national_document_id']}"
              f"  approved {doc['approval_filing_date']}")
    sm = d["secondary_market"]
    print()
    print("SECONDARY MARKET")
    for k, label in (("listing_count", "Listings"),
                     ("active_venue_count", "Active venues"),
                     ("first_admission_date", "First admission")):
        f = sm.get(k)
        if f:
            _print_field(label, f)
    for li in (sm.get("listings") or [])[:14]:
        st = li["state"]
        nm = li.get("venue_name") or li["venue_mic"]
        print(f"    {li['venue_mic']:<6}{nm[:34]:<36}{st}")
    if len(sm.get("listings") or []) > 14:
        print(f"    … {len(sm['listings']) - 14} more")
    pt = d["post_trade"]
    print()
    print("POST-TRADE")
    for k, label in (("issuer_sss", "Issuer SSS"),
                     ("iberclear_admitted", "Iberclear"),
                     ("possible_paths", "Possible paths")):
        f = pt.get(k)
        if f:
            _print_field(label, f)
    asm = pt.get("assessment") or {}
    if asm.get("value"):
        print(f"  assessment: {asm['value']}")
    ec = d["eurosystem_collateral"]
    print()
    print("EUROSYSTEM COLLATERAL")
    for k, label in (("eligible", "Eligible"),
                     ("ecb_snapshot", "Snapshot"),
                     ("haircut_category", "Haircut category"),
                     ("haircut", "Haircut"),
                     ("asset_type", "Asset type"),
                     ("issuer_csd", "Issuer CSD")):
        f = ec.get(k)
        if f:
            _print_field(label, f)
    print()
    print("PROVENANCE")
    counts: dict[str, int] = {}
    for blk in ("identity", "primary_market", "secondary_market",
                "post_trade", "eurosystem_collateral"):
        for v in d[blk].values():
            if isinstance(v, dict) and "status" in v:
                counts[v["status"]] = counts.get(
                    v["status"], 0) + 1
    print("  " + "   ".join(f"{k}={v}"
                            for k, v in sorted(counts.items())))
    print()


def _explain(p: dict[str, Any], query: str) -> int:
    """Deterministic explanation — value, status, evidence, rule,
    alternatives, limitations. No LLM."""
    q = query.lower().replace("-", "_")
    for blk_name in ("identity", "primary_market", "secondary_market",
                     "post_trade", "eurosystem_collateral"):
        blk = p.get(blk_name) or {}
        if q in (blk_name, blk_name.replace("_", "-")):
            print(f"BLOCK {blk_name}")
            for k, f in blk.items():
                if isinstance(f, dict) and "status" in f:
                    _print_field(k, f, indent="  ")
            return 0
        f = blk.get(q)
        if isinstance(f, dict) and "status" in f:
            print(f"FIELD {blk_name}.{q}")
            print(f"  value:   {_fmt_value(f.get('value'))}")
            print(f"  status:  {f.get('status')}")
            if f.get("explanation"):
                print(f"  why:     {f['explanation']}")
            r = f.get("rule")
            if r:
                print(f"  rule:    {r['rule_id']}.v"
                      f"{r['rule_version']}")
                if r.get("limitations"):
                    print(f"  limits:  {r['limitations']}")
            for e in f.get("evidence") or []:
                print(f"  evidence: {e['provider']}/"
                      f"{e['dataset']} rec={e['record_id']} "
                      f"art={e.get('artifact_id') or '—'} "
                      f"ret={e.get('retrieved_at') or '—'}")
                if e.get("raw_value") is not None:
                    print(f"           raw={e['raw_value']!r}")
            for a in f.get("alternatives") or []:
                print(f"  alternative: {a.get('value')!r} "
                      f"({a.get('role')})")
            if f.get("searched_sources"):
                print(f"  searched: {', '.join(f['searched_sources'])}")
            if f.get("quality_flags"):
                print(f"  flags:   {', '.join(f['quality_flags'])}")
            return 0
    print(f"no field or block named '{query}'", file=sys.stderr)
    return 2


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


def _lookup(isin: str, json_out: bool, sources: bool,
            explain: str) -> None:
    isin_n = normalize(isin)
    if not checksum_ok(isin_n):
        typer.secho(
            f"INVALID_ISIN: '{isin}' fails structure/checksum.",
            err=True, fg=typer.colors.RED)
        raise typer.Exit(2)
    prov, store = _runtime()
    try:
        p = PassportBuilder(prov, store).build(
            isin_n, checksum_ok=True)
    except Exception as e:
        typer.secho(f"SOURCE_UNAVAILABLE: {e}", err=True,
                    fg=typer.colors.RED)
        raise typer.Exit(3) from e
    d = p.to_dict()
    if explain:
        raise typer.Exit(_explain(d, explain))
    if sources:
        typer.echo(json.dumps(
            {"isin": isin_n, "source_summary": d["source_summary"]},
            indent=2))
        raise typer.Exit(0)
    if json_out:
        typer.echo(json.dumps(d, indent=2, ensure_ascii=False))
        raise typer.Exit(0)
    _print_passport(d)


@app.command()
def update(
        data_root: Annotated[Path | None, typer.Option(
            "--data-root")] = None,
        priii_isin: Annotated[list[str] | None, typer.Option(
            "--priii-isin",
            help="ISINs to ingest PRIII families for.")] = None) -> None:
    """Ingest own sources and publish a new generation."""
    s = load()
    root = data_root or s.data_root
    from security_passport.services.update import run_update
    upstream_gen = ""
    if s.provider == "openinstrument_api":
        try:
            from security_passport.providers.openinstrument.api import (
                OpenInstrumentApiProvider,
            )
            upstream_gen = OpenInstrumentApiProvider(
                s.openinstrument_url).generation()
        except Exception as e:
            typer.echo(f"warning: upstream generation probe "
                       f"failed: {e}")
    try:
        res = run_update(root, priii_isin or [],
                         upstream_generation=upstream_gen)
    except Exception as e:
        typer.secho(f"update failed: {e}", err=True,
                    fg=typer.colors.RED)
        raise typer.Exit(1) from e
    typer.echo(f"published {res['published']}")
    for prov, meta in (res["manifest"].get("providers") or {}).items():
        if isinstance(meta, dict):
            det = " ".join(f"{k}={v}" for k, v in meta.items()
                           if k in ("snapshot", "rows", "n_sss",
                                    "n_links", "isin_count"))
            typer.echo(f"  {prov}: {det}")


@app.command()
def validate(
        goldens: Annotated[Path, typer.Option(
            "--goldens")] = Path("tests/fixtures/goldens.yaml")) -> None:
    """Run the assertion validator over the golden corpus."""
    import yaml  # type: ignore[import-untyped]

    from security_passport.services.validate import (
        ValidationReport,
        check_passport,
    )
    prov, store = _runtime()
    spec = yaml.safe_load(goldens.read_text(encoding="utf-8"))
    report = ValidationReport()
    failures: list[str] = []
    for g in spec.get("goldens") or []:
        isin = g["isin"]
        if not g.get("fixture"):
            continue
        p = PassportBuilder(prov, store).build(
            normalize(isin), checksum_ok=checksum_ok(isin))
        check_passport(p, report)
        exp = g.get("expected") or {}
        d = p.to_dict()
        for key, want in exp.items():
            if key == "overall_state":
                if d["overall_state"] != want:
                    failures.append(
                        f"{isin}: overall_state "
                        f"{d['overall_state']} != {want}")
                continue
            if key.endswith("_at_least"):
                continue
            parts = key.split(".", 1)
            if len(parts) != 2:
                continue
            blk, fld = parts
            f = (d.get(blk) or {}).get(fld) or {}
            for attr, wv in (want or {}).items():
                got = f.get(attr)
                if attr == "value" and got != wv:
                    failures.append(
                        f"{isin}: {key} value {got!r} != {wv!r}")
                elif attr == "status" and got != wv:
                    failures.append(
                        f"{isin}: {key} status {got!r} != {wv!r}")
    typer.echo(json.dumps(report.to_dict(), indent=2))
    if failures:
        typer.secho("golden expectation failures:", err=True,
                    fg=typer.colors.RED)
        for f in failures:
            typer.secho(f"  {f}", err=True)
    if not report.ok() or failures:
        raise typer.Exit(1)
    typer.echo("validate: PASS (unsupported_assertions = 0)")


@app.command()
def doctor() -> None:
    """Environment check — provider, store, generation."""
    s = load()
    typer.echo(f"security-passport {__version__}")
    typer.echo(f"provider mode : {s.provider}")
    typer.echo(f"data root     : {s.data_root}")
    typer.echo(f"fixtures      : {s.fixtures_dir} "
               f"({'ok' if s.fixtures_dir.exists() else 'MISSING'})")
    prov, store = _runtime()
    try:
        typer.echo(f"upstream gen  : {prov.generation()}")
    except Exception as e:
        typer.secho(f"upstream gen  : FAIL {e}",
                    fg=typer.colors.RED)
    try:
        typer.echo(f"store gen     : {store.generation()}")
        typer.echo(f"ecb snapshot  : {store.ecb_snapshot()}")
    except Exception as e:
        typer.secho(f"store         : FAIL {e}",
                    fg=typer.colors.RED)


@app.command()
def status() -> None:
    """Show generation and source freshness."""
    s = load()
    from security_passport.storage import generations
    read_root = s.data_root / "read"
    cur = generations.current(read_root)
    typer.echo(f"current generation: "
               f"{generations.generation_name(read_root) or 'none'}")
    if cur:
        man_p = cur / "manifest.json"
        if man_p.exists():
            man = json.loads(man_p.read_text(encoding="utf-8"))
            typer.echo(f"created_at      : {man.get('created_at')}")
            typer.echo(f"fingerprint     : "
                       f"{man.get('semantic_fingerprint')}")
            for prov, meta in (man.get("providers") or {}).items():
                if isinstance(meta, dict):
                    typer.echo(f"  {prov}: {meta}")


_COMMANDS = {"update", "validate", "doctor", "status", "rollback",
             "explain", "search"}


def main() -> None:
    """Entry point — supports `security-passport <ISIN> [options]`
    with options in any position, which click groups cannot."""
    argv = sys.argv[1:]
    if argv and not argv[0].startswith("-") \
            and argv[0] not in _COMMANDS:
        isin, rest = argv[0], argv[1:]
        json_out = "--json" in rest
        sources = "--sources" in rest
        explain = ""
        for i, a in enumerate(rest):
            if a == "--explain" and i + 1 < len(rest):
                explain = rest[i + 1]
            elif a.startswith("--explain="):
                explain = a.split("=", 1)[1]
        try:
            _lookup(isin, json_out, sources, explain)
        except typer.Exit as e:
            sys.exit(e.exit_code)
        return
    app()


if __name__ == "__main__":
    main()
