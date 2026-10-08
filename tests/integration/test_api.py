"""API contract tests — fixture mode, no network."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ["SECURITY_PASSPORT_PROVIDER"] = "fixtures"
os.environ["SECURITY_PASSPORT_FIXTURES"] = "tests/fixtures/corpus"

from security_passport.api.app import create_app
from security_passport.config import load


@pytest.fixture(scope="module")
def client():
    with TestClient(create_app(load())) as c:
        yield c


def test_status(client: TestClient) -> None:
    r = client.get("/api/v1/status")
    assert r.status_code == 200
    assert r.json()["service"] == "security-passport"


def test_passport_ok(client: TestClient) -> None:
    r = client.get("/api/v1/passports/DE000A3LJCB4")
    assert r.status_code == 200
    d = r.json()
    assert d["schema_version"] == "1"
    assert set(d) >= {"identity", "primary_market",
                      "secondary_market", "post_trade",
                      "eurosystem_collateral"}
    assert r.headers.get("etag")


def test_invalid_isin_422(client: TestClient) -> None:
    r = client.get("/api/v1/passports/DE000A3LJCB0")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_ISIN"


def test_unknown_isin_partial_200(client: TestClient) -> None:
    r = client.get("/api/v1/passports/XSSE2WKP7HV5")
    assert r.status_code == 200
    assert r.json()["overall_state"] == "unknown"


def test_evidence_endpoint(client: TestClient) -> None:
    r = client.get("/api/v1/passports/DE000A3LJCB4/evidence")
    assert r.status_code == 200
    evs = r.json()["evidence"]
    assert evs
    assert all(e["provider"] and e["dataset"] for e in evs)


def test_sources_endpoint(client: TestClient) -> None:
    r = client.get("/api/v1/passports/DE000A3LJCB4/sources")
    assert r.status_code == 200
    assert r.json()["source_summary"]


def test_search(client: TestClient) -> None:
    r = client.get("/api/v1/search", params={"q": "DE000A3LJCB4"})
    assert r.status_code == 200
    assert r.json()["results"]


def test_health(client: TestClient) -> None:
    assert client.get("/health/live").status_code == 200
    r = client.get("/health/ready")
    assert r.status_code == 200
    assert r.json()["checks"]["provider"]


def test_security_headers(client: TestClient) -> None:
    r = client.get("/api/v1/status")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"


def test_status_exposes_demo_corpus(client: TestClient) -> None:
    demo = client.get("/api/v1/status").json()["demo"]
    isins = {c["isin"] for c in demo["corpus"]}
    assert "DE000A3LJCB4" in isins
    assert demo["captured_at"]


def test_scoped_endpoints_reject_invalid_isin(
        client: TestClient) -> None:
    for suffix in ("evidence", "sources"):
        r = client.get(f"/api/v1/passports/DE000A3LJCB0/{suffix}")
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "INVALID_ISIN"


def test_search_rejects_oversized_query(client: TestClient) -> None:
    r = client.get("/api/v1/search", params={"q": "x" * 65})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_QUERY"


def test_openapi_served_under_api_prefix(client: TestClient) -> None:
    assert client.get("/api/openapi.json").status_code == 200
    assert client.get("/api/docs").status_code == 200
