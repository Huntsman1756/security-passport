"""Version single-source invariants.

`pyproject.toml` is the release authority; every runtime surface
must reflect the *installed* package version — never a literal.
"""
from __future__ import annotations

import re
from importlib.metadata import version as pkg_version
from pathlib import Path

import security_passport
from security_passport import __version__, user_agent

ROOT = Path(__file__).resolve().parents[2]


def test_init_version_is_installed_version() -> None:
    assert __version__ == pkg_version("security-passport")


def test_user_agent_carries_version() -> None:
    assert user_agent() == f"security-passport/{__version__}"


def test_no_hardcoded_runtime_version() -> None:
    """No `security-passport/<digit>` literal outside tests/docs —
    the only sanctioned version string is computed."""
    pat = re.compile(r"security-passport/\d")
    bad = []
    for p in (ROOT / "src").rglob("*.py"):
        for i, line in enumerate(
                p.read_text(encoding="utf-8").splitlines(), 1):
            if pat.search(line):
                bad.append(f"{p}:{i}")
    assert not bad, f"hardcoded version UA in: {bad}"


def test_fastapi_version_matches() -> None:
    from security_passport.api.app import create_app
    from security_passport.config import load
    assert create_app(load()).version == __version__


def test_web_package_has_no_redundant_version() -> None:
    import json
    d = json.loads(
        (ROOT / "web/package.json").read_text(encoding="utf-8"))
    assert "version" not in d
    assert d.get("packageManager", "").startswith("pnpm@")
