"""ISO 10383 MIC registry — venue naming only.

Public CSV published by the registration authority (SWIFT for
ISO). We keep MIC + operating MIC + segment flag + market name +
country + status — enough to label venues honestly without
redistributing the registry.
"""
from __future__ import annotations

import csv
import io
import urllib.request
from dataclasses import dataclass

PARSER = "security_passport.providers.mic"
PARSER_VERSION = "1"
PROVIDER = "iso10383_mic"

MIC_URL = ("https://www.iso20022.org/sites/default/files/"
           "ISO10383_MIC/ISO10383_MIC.csv")
_UA = {"User-Agent": "security-passport/0.1.0"}


@dataclass(frozen=True)
class MicRow:
    mic: str
    operating_mic: str
    oprt_sgmt: str       # OPRT = operating, SGMT = segment
    market_name: str
    acronym: str
    country: str
    city: str
    status: str
    lei: str


def download() -> bytes:
    return urllib.request.urlopen(  # noqa: S310 — allowlisted ISO
        urllib.request.Request(MIC_URL, headers=_UA),
        timeout=120).read()


def decode_csv(raw: bytes) -> str:
    """The registry ships cp1252 (e.g. "BÖRSE" as 0xD6); utf-8-sig
    first for safety, cp1252 fallback."""
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252", "replace")


def parse(csv_text: str) -> dict[str, MicRow]:
    """MIC → row. The file carries header comments before the
    real header line; locate the line starting with "MIC"."""
    out: dict[str, MicRow] = {}
    reader = csv.reader(io.StringIO(csv_text))
    header_seen = False
    cols: list[str] = []
    for row in reader:
        if not row:
            continue
        if not header_seen:
            if row[0].strip().strip('"').upper() == "MIC":
                cols = [c.strip().upper() for c in row]
                header_seen = True
            continue
        rec = dict(zip(cols, row, strict=False))
        mic = rec.get("MIC", "").strip()
        if not mic:
            continue
        out[mic] = MicRow(
            mic=mic,
            operating_mic=rec.get("OPERATING MIC", "").strip(),
            oprt_sgmt=rec.get("OPRT/SGMT", "").strip(),
            market_name=rec.get(
                "MARKET NAME-INSTITUTION DESCRIPTION", "").strip(),
            acronym=rec.get("ACRONYM", "").strip(),
            country=rec.get(
                "ISO COUNTRY CODE (ISO 3166)", "").strip(),
            city=rec.get("CITY", "").strip(),
            status=rec.get("STATUS", "").strip(),
            lei=rec.get("LEI", "").strip())
    return out
