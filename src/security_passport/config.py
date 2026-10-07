"""Runtime configuration — env-driven, no secrets in code."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    provider: str                 # fixtures | openinstrument_api
    openinstrument_url: str
    data_root: Path
    fixtures_dir: Path
    public_base_url: str
    cors_origins: tuple[str, ...]


def load() -> Settings:
    env = os.environ
    cors = env.get("SECURITY_PASSPORT_CORS_ORIGINS",
                   "http://localhost:5173")
    return Settings(
        provider=env.get("SECURITY_PASSPORT_PROVIDER", "fixtures"),
        openinstrument_url=env.get(
            "OPENINSTRUMENT_URL", "http://127.0.0.1:8000"),
        data_root=Path(env.get("SECURITY_PASSPORT_DATA", "data")),
        fixtures_dir=Path(env.get(
            "SECURITY_PASSPORT_FIXTURES",
            "tests/fixtures/corpus")),
        public_base_url=env.get(
            "PUBLIC_BASE_URL", "http://localhost:5173"),
        cors_origins=tuple(
            o.strip() for o in cors.split(",") if o.strip()))
