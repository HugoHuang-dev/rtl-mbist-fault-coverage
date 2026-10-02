# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : frozen_source.py
# Module  : frozen_source
# -----------------------------------------------------------------------------
"""Verify source snapshots tied to historical and rerun fault campaigns."""

from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "evidence" / "frozen_source_before_headers.zip"
SOURCES = {"rtl/" + name for name in (
    "address_generator.v", "data_generator.v", "memory_interface.v",
    "response_checker.v", "march_controller.v", "mbist_top.v",
)} | {"tb/" + name for name in (
    "fault_injector.sv", "faulty_memory.sv", "fault_reference_monitor.sv",
    "march_transaction_checker.sv", "tb_step06_campaign.sv",
)}


def strip_release_header(data: bytes) -> bytes:
    lines = data.splitlines(keepends=True)
    if len(lines) >= 8 and b"Hugo's MBIST Project" in lines[1]:
        boundaries = [i for i, line in enumerate(lines[:15]) if b"-----" in line]
        if len(boundaries) >= 3:
            return b"".join(lines[boundaries[2] + 1:])
    return data


def verify_step6_source_bodies(result_dir: Path) -> int:
    snapshot = result_dir / "source_snapshot.zip"
    historical = not snapshot.exists()
    if historical and result_dir.resolve() != (ROOT / "results/step06").resolve():
        raise ValueError("Campaign source_snapshot.zip is missing")
    checked = 0
    with ZipFile(ARCHIVE if historical else snapshot) as frozen:
        names = frozen.namelist()
        missing = SOURCES - set(names)
        if missing or any(names.count(name) != 1 for name in SOURCES):
            raise ValueError(f"missing source snapshot entries or duplicate sources: {sorted(missing)}")
        for name in frozen.namelist():
            if name not in SOURCES:
                continue
            original = frozen.read(name)
            current = (ROOT / name).read_bytes()
            comparable = strip_release_header(current) if historical else current
            if comparable.replace(b"\r\n", b"\n") != original.replace(b"\r\n", b"\n"):
                raise ValueError(f"source body differs from experiment snapshot: {name}")
            checked += 1
    return checked
