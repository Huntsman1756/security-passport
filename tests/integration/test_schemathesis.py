"""Schemathesis property-based API testing — generated cases from
the OpenAPI schema, checking for 500s, schema mismatches and
invalid-input acceptance. Runs fully offline in fixture mode."""
from __future__ import annotations

import os

os.environ.setdefault("SECURITY_PASSPORT_PROVIDER", "fixtures")
os.environ.setdefault("SECURITY_PASSPORT_FIXTURES",
                      "tests/fixtures/corpus")

import pytest
import schemathesis
from hypothesis import settings

from security_passport.api.app import create_app
from security_passport.config import load

app = create_app(load())
schema = schemathesis.openapi.from_asgi("/api/openapi.json", app)


# ISO 6166 checksum rejection (422 INVALID_ISIN) is deliberate
# domain behaviour: most schema-compliant strings are NOT valid
# ISINs. OpenAPI cannot express a Luhn check in a pattern, so the
# positive-data-acceptance check is excluded for path params.
_EXCLUDED = [schemathesis.checks.positive_data_acceptance]


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
@schema.parametrize()
@settings(max_examples=60, deadline=None,
          suppress_health_check=[
              __import__("hypothesis").HealthCheck.too_slow])
def test_api_contract(case) -> None:
    """Schemathesis case — response must match the schema and
    never be a 5xx (a fallen source is a clean 503 with an error
    body, not a crash)."""
    response = case.call_and_validate(excluded_checks=_EXCLUDED)
    assert response.status_code < 500, (
        f"{case.operation.method} {case.path} → "
        f"{response.status_code}")
