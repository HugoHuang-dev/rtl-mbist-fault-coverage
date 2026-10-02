# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : source_provenance.py
# Module  : source_provenance
# -----------------------------------------------------------------------------
"""Match historical ASIC input bytes and the shared ProjectIII RTL bodies."""
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "evidence/asic_integration/source_snapshot.zip"


def body(data):
    lines = data.splitlines(keepends=True)
    if len(lines) >= 8 and b"Hugo's MBIST Project" in lines[1]:
        lines = lines[8:]
    return b"".join(lines).replace(b"\r\n", b"\n").strip()


def verify_source_body(name):
    current = (ROOT / name).read_bytes()
    with ZipFile(ARCHIVE) as frozen:
        original = frozen.read(name)
    if body(original) != body(current):
        raise ValueError(f"Archived RTL body differs: {name}")
