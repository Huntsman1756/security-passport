"""Capture fixture corpus from live sources — operator tool.

Reads OpenInstrument API payloads for the golden ISINs, slices the
ECB eligible-assets CSV to fixture rows, captures ESMA PRIII Solr
responses, ECB SSS/links pages, and the ISO 10383 MIC rows needed
by the fixture venues. Everything lands under
``tests/fixtures/corpus/`` so the repo is self-demonstrating.

Run:  python scripts/capture_fixtures.py
Requires: OPENINSTRUMENT_URL (default http://127.0.0.1:8765),
network access to ESMA/ECB/ISO.
"""
from __future__ import annotations

import gzip
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tests" / "fixtures" / "corpus"
OI = __import__("os").environ.get(
    "OPENINSTRUMENT_URL", "http://127.0.0.1:8090")
UA = {"User-Agent": "security-passport fixture capture"}

ISINS = [
    # v0.1 corpus
    "DE000A3LJCB4", "XS2081615473", "DE0007164600", "ES0113900J37",
    "ES0000101966", "IE0007SRI1C7", "LU0003549028",
    # expanded corpus (v0.1.1)
    "FR0013154002",   # FR equity (Sartorius)
    "IT0004729759",   # IT equity (Sesa)
    "ES0155092036",   # ES SICAV (fund-ish CFI C)
    "IE00BYYJHC15",   # IE UCITS share class
    "DE000A2GSP56",   # covered bond (ECB, CLDE01)
    "XS2525255647",   # covered bond (ECB, CLBL01)
    "IT0024182286",   # option with issuer-LEI conflict
    "AT0000A1NZ16",   # fully delisted
    "DE0005874846",   # FIRDS sentinel first_trade_date
    "DE0001150548",   # German Bund
    "ES0105015012",   # ES public debt candidate
    "FR001400YGG3",   # FR instrument
    "DE000DN48XD7",   # DE debt candidate (PRIII-only evidence)
    "IE00B4L5Y983",   # iShares ETF share class
    "IT0005282527",   # IT BTP sovereign
    "FR0000120271",   # TotalEnergies (multi-venue equity)
    "NL0000235190",   # Airbus (NL equity)
    "XS0971721963",   # RU sovereign (sanctions-era edge case)
    "ES0000012E44",   # ES sovereign (CLES01 — Iberclear evidence)
    "IT0005678443",   # IT bank bond (CLIT01 — Euronext Milan)
    "FR0129714681",   # FR covered (CLFR01 — Euroclear France)
    "ES0113211835",   # ES equity (BBVA)
]
# ISINs whose PRIII families are captured (absence is also data —
# an empty family file is a checked source, not a gap).
PRIII_ISINS = ISINS

OI_PATHS = [
    ("instrument", "/v1/instruments/{i}"),
    ("listings", "/v1/instruments/{i}/listings"),
    ("issuer", "/v1/instruments/{i}/issuer"),
    ("identifiers", "/v1/instruments/{i}/identifiers"),
    ("evidence", "/v1/instruments/{i}/evidence"),
    ("v2", "/v2/instruments/{i}"),
]

SOLR = ("https://registers.esma.europa.eu/solr/"
        "esma_registers_priii_documents/select")


def fetch(url: str, binary: bool = False):
    req = urllib.request.Request(url, headers=UA)
    raw = urllib.request.urlopen(req, timeout=120).read()
    return raw if binary else raw.decode("utf-8", "replace")


def oi(path: str) -> dict:
    try:
        return json.loads(fetch(OI + path))
    except Exception as e:  # noqa: BLE001 — capture records the
        # contract failure verbatim instead of crashing; upstream
        # /v1/evidence 503s when its hardcoded snapshot lags.
        return {"_capture_error": f"{type(e).__name__}: {e}"}


def solr(q: str, rows: int = 200) -> dict:
    p = urllib.parse.urlencode({"q": q, "wt": "json",
                                "rows": str(rows)})
    return json.loads(fetch(SOLR + "?" + p))["response"]


def main() -> None:
    oi_dir = OUT / "openinstrument"
    oi_dir.mkdir(parents=True, exist_ok=True)
    (OUT / "openinstrument" / "status.json").write_text(
        json.dumps(oi("/v1/status"), indent=1), encoding="utf-8")
    for isin in ISINS:
        for name, tpl in OI_PATHS:
            d = oi(tpl.format(i=isin))
            (oi_dir / f"{isin}.{name}.json").write_text(
                json.dumps(d, indent=1, default=str),
                encoding="utf-8")
            print("oi", isin, name, "ok")

    # ---- ECB eligible assets slice --------------------------------
    ecb_dir = OUT / "ecb_assets"
    ecb_dir.mkdir(exist_ok=True)
    page = fetch("https://www.ecb.europa.eu/mopo/coll/assets/html/"
                 "list-MID.en.html")
    import re
    href = re.search(r'href="([^"]*/ea_csv_\d{6}\.csv\.gz)"',
                     page).group(1)
    url = "https://www.ecb.europa.eu" + href
    raw = fetch(url, binary=True)
    txt = gzip.decompress(raw).decode("utf-16")
    lines = txt.split("\r\n")
    hdr, kept = lines[0], []
    wanted = set(ISINS) | {"XS2009128617", "DE000A3H2598"}
    for ln in lines[1:]:
        if ln.strip() and ln.split("\t")[0] in wanted:
            kept.append(ln)
    out = hdr + "\r\n" + "\r\n".join(kept) + "\r\n"
    (ecb_dir / "ea_slice.csv").write_bytes(out.encode("utf-16"))
    print("ecb slice rows:", len(kept), "from", href)

    # ---- PRIII ----------------------------------------------------
    priii_dir = OUT / "priii"
    priii_dir.mkdir(exist_ok=True)
    for isin in PRIII_ISINS:
        fam = {"isin": isin, "ifii": solr(f'ifii_isin:"{isin}"'),
               "filings": []}
        for doc in fam["ifii"]["docs"]:
            root = doc.get("_root_")
            if not root:
                continue
            fam["filings"].append({
                "root": root,
                "parent": solr(f'_root_:"{root}" AND type_s:parent'),
                "children": solr(f'_root_:"{root}" AND type_s:child')})
        (priii_dir / f"{isin}.json").write_text(
            json.dumps(fam, indent=1, default=str), encoding="utf-8")
        print("priii", isin, "filings:", len(fam["filings"]))

    # ---- ECB SSS + links pages ------------------------------------
    sss_dir = OUT / "ecb_sss"
    sss_dir.mkdir(exist_ok=True)
    for name, url in [
        ("sss_page",
         "https://www.ecb.europa.eu/mopo/coll/coll/eligiblesss/"
         "html/index.en.html"),
        ("links_page",
         "https://www.ecb.europa.eu/mopo/coll/coll/ssslinks/"
         "html/index.en.html")]:
        (sss_dir / f"{name}.html").write_text(
            fetch(url), encoding="utf-8")
        print("ecb", name, "saved")

    # ---- MIC slice --------------------------------------------------
    mic_dir = OUT / "mic"
    mic_dir.mkdir(exist_ok=True)
    mics: set[str] = set()
    for isin in ISINS:
        d = json.loads((oi_dir / f"{isin}.listings.json")
                       .read_text(encoding="utf-8"))
        for r in d.get("listings") or []:
            for k in ("venue_mic", "relevant_venue"):
                if r.get(k):
                    mics.add(r[k])
    mics |= {"XETR", "XFRA", "XMAD", "XLUX", "WBDM"}
    try:
        mcsv = fetch("https://www.iso20022.org/sites/default/files/"
                     "ISO10383_MIC/ISO10383_MIC.csv")
    except Exception as e:  # noqa: BLE001
        print("MIC download failed:", e)
        mcsv = ""
    if mcsv:
        mlines = mcsv.splitlines()
        hdr_i = next(i for i, ln in enumerate(mlines)
                     if ln.startswith('"MIC"'))
        kept = [ln for ln in mlines[hdr_i:]
                if ln.split(",")[0].strip('"') in mics
                or ln.lstrip('"').startswith("MIC,")]
        (mic_dir / "mic_slice.csv").write_text(
            "\n".join(kept) + "\n", encoding="utf-8")
        print("mic rows:", len(kept))
    (mic_dir / "wanted.json").write_text(
        json.dumps(sorted(mics), indent=1), encoding="utf-8")

    # ---- manifest ---------------------------------------------------
    man = {"captured_at": "2026-10-07",
           "openinstrument": OI, "isins": ISINS,
           "ecb_snapshot": href, "mics": sorted(mics)}
    (OUT / "manifest.json").write_text(
        json.dumps(man, indent=1), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
