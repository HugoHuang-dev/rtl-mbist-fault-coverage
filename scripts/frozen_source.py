# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : frozen_source.py
# Module  : frozen_source
# -----------------------------------------------------------------------------
"""Verify source snapshots tied to historical and rerun fault campaigns."""

import hashlib
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "evidence" / "frozen_source_before_headers.zip"
CODE_SUFFIXES = {".v", ".sv", ".py", ".tcl", ".xdc", ".ps1"}
AUDITOR = "scripts/audit_step06.py"


def strip_release_header(data: bytes) -> bytes:
    lines = data.splitlines(keepends=True)
    if len(lines) >= 8 and b"Hugo's MBIST Project" in lines[1]:
        boundaries = [i for i, line in enumerate(lines[:15]) if b"-----" in line]
        if len(boundaries) >= 3:
            return b"".join(lines[boundaries[2] + 1:])
    return data


def verify_step6_source_fingerprints(manifest: Path) -> int:
    lines = manifest.read_text(encoding="utf-8").splitlines()
    checked = set()
    snapshot = manifest.parent / "source_snapshot.zip"
    historical = not snapshot.exists()
    if historical and manifest.resolve() != (ROOT / "results/step06/source_sha256.txt").resolve():
        raise ValueError("Campaign source_snapshot.zip is missing")
    with ZipFile(ARCHIVE if historical else snapshot) as frozen:
        archived_names = set(frozen.namelist())
        for line in lines:
            expected, name = line.split("  ", 1)
            if name in checked:
                raise ValueError(f"duplicate source fingerprint: {name}")
            checked.add(name)
            original = (frozen.read(name) if name in archived_names
                        else (ROOT / name).read_bytes())
            if hashlib.sha256(original).hexdigest().upper() != expected:
                raise ValueError(f"frozen source hash differs: {name}")
            current = (ROOT / name).read_bytes()
            if not historical and hashlib.sha256(current).hexdigest().upper() != expected:
                raise ValueError(f"current source differs from rerun snapshot: {name}")
            # The original experiment is checked against its original snapshot.
            # Current RTL/TB must still match; revised runner scripts belong to
            # separately recorded reruns and are not claimed as original inputs.
            if historical and Path(name).suffix in {".v", ".sv"}:
                comparable = (strip_release_header(current)
                              if Path(name).suffix in CODE_SUFFIXES else current)
                # Source text may use Windows CRLF after editing. Preserve the
                # archived byte hash above; ignore only line-ending differences
                # when comparing the current RTL/TB body.
                if comparable.replace(b"\r\n", b"\n") != original.replace(b"\r\n", b"\n"):
                    raise ValueError(f"source body differs from frozen evidence: {name}")
    return len(checked)
