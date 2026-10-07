"""Public-repository hygiene gate.

Fails on high-value findings only: personal absolute paths,
tracked env/secret files, hardcoded runtime-version strings,
obvious token patterns. Deliberately narrow — localhost,
fixture URLs, SHA256 digests, and docs examples are fine.
"""
from __future__ import annotations

import re
import subprocess
import sys

ROOT = subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"], text=True).strip()

TRACKED = subprocess.check_output(
    ["git", "ls-files"], cwd=ROOT, text=True).splitlines()

FINDINGS: list[str] = []

# 1. tracked files that must never be committed
for f in TRACKED:
    name = f.rsplit("/", 1)[-1]
    if name in (".env", ".env.local", ".env.production") \
            or name.endswith((".pem", ".key", ".pfx", ".p12")):
        FINDINGS.append(f"tracked secret-like file: {f}")

# 2. content scans on tracked text files
# source fixtures are verbatim captures — only secret patterns
# apply there; path hygiene applies to authored files.
PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"[A-Za-z]:[\\/]_?Proyectos"),
     "personal absolute project path"),
    (re.compile(r"[A-Za-z]:[\\/]Users[\\/][A-Za-z0-9_.-]+"),
     "personal user profile path"),
    (re.compile(r"ghp_[A-Za-z0-9]{20,}"), "GitHub PAT"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "API key pattern"),
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY"),
     "private key material"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
    (re.compile(r'security-passport/\d'),
     "hardcoded runtime version in User-Agent"),
]

# paths where version literals are legitimate historical records
VERSION_EXEMPT = re.compile(
    r"^(docs/release/|docs/adr/|docs/reuse/|tests/)")
SECRET_ONLY = re.compile(r"^(tests/fixtures/)")

for f in TRACKED:
    if f.endswith((".png", ".jpg", ".webp", ".parquet", ".xlsx",
                   ".pdf", ".whl", ".ico", ".woff2")):
        continue
    try:
        text = open(f"{ROOT}/{f}", encoding="utf-8",
                    errors="strict").read()
    except (OSError, UnicodeDecodeError):
        continue
    secret_only = bool(SECRET_ONLY.match(f))
    for i, line in enumerate(text.splitlines(), 1):
        for pat, label in PATTERNS:
            if secret_only and label not in (
                    "GitHub PAT", "API key pattern",
                    "private key material", "AWS access key"):
                continue
            if pat.search(line):
                if label == "hardcoded runtime version in " \
                        "User-Agent" and \
                        (VERSION_EXEMPT.match(f)
                         or "version(" in line
                         or f.endswith("test_version.py")):
                    continue
                FINDINGS.append(f"{f}:{i} {label}")

# 3. suspiciously large tracked blobs (> 3 MB)
for f in TRACKED:
    import os
    fp = os.path.join(ROOT, f)
    if os.path.isfile(fp) and os.path.getsize(fp) > 3 * 1024 * 1024:
        FINDINGS.append(f"oversized tracked file: {f} "
                        f"({os.path.getsize(fp) // 1048576} MB)")

if FINDINGS:
    print("PUBLIC HYGIENE FAIL")
    for f in FINDINGS:
        print(" ", f)
    sys.exit(1)
print(f"public hygiene: clean ({len(TRACKED)} tracked files)")
