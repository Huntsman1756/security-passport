"""Export the frozen OpenAPI schema — the release-contract
baseline for oasdiff checks in CI.

    python scripts/export_openapi.py > openapi-baseline.json
"""
from __future__ import annotations

import json
import os
import sys

os.environ.setdefault("SECURITY_PASSPORT_PROVIDER", "fixtures")
os.environ.setdefault("SECURITY_PASSPORT_FIXTURES",
                      "tests/fixtures/corpus")

from security_passport.api.app import create_app  # noqa: E402
from security_passport.config import load  # noqa: E402


def main() -> None:
    app = create_app(load())
    json.dump(app.openapi(), sys.stdout, indent=1,
              ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
