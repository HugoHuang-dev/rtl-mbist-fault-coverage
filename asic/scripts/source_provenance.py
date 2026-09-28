# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : source_provenance.py
# Module  : source_provenance
# -----------------------------------------------------------------------------
"""Match historical ASIC input bytes and the shared ProjectIII RTL bodies."""
import hashlib
import re
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "evidence/asic_integration/source_snapshot.zip"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def body(data):
    lines = data.splitlines(keepends=True)
    if len(lines) >= 8 and b"Hugo's MBIST Project" in lines[1]:
        lines = lines[8:]
    return b"".join(lines).replace(b"\r\n", b"\n").strip()


def verify_frozen(name, expected):
    current = (ROOT / name).read_bytes()
    if sha(current) == expected:
        return "exact_bytes"
    if Path(name).suffix not in (".v", ".sv"):
        raise ValueError(f"Frozen non-RTL input differs: {name}")
    with ZipFile(ARCHIVE) as frozen:
        original = frozen.read(name)
    if sha(original) != expected or body(original) != body(current):
        raise ValueError(f"Frozen RTL body differs: {name}")
    return "same_body_header_or_line_endings_only"


def toolchain_hashes(path):
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})\s+(.+)", line)
        if not match:
            continue
        name = match[2].replace("\\", "/")
        key = next((prefix + name.split("/" + prefix, 1)[1]
                    for prefix in ("asic/", "rtl/") if "/" + prefix in name),
                   Path(name).name)
        result[key] = match[1]
    return result
