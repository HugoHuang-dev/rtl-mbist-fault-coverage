# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : generate_fault_manifest.py
# Module  : generate_fault_manifest
# -----------------------------------------------------------------------------
"""Generate the frozen, exhaustive single-fault universe for Step 6."""

import csv
from pathlib import Path
from project_config import result_dir


PROJECT = Path(__file__).resolve().parents[1]
RESULTS = result_dir("step06")
TYPES = ((1, "SA0"), (2, "SA1"), (3, "Rising_TF"), (4, "Falling_TF"))
PILOT_ADDRESSES = (0, 1, 7, 15, 31, 47, 62, 63)
PILOT_BITS = (0, 7, 2, 5, 3, 4, 6, 1)
FIELDS = ("fault_id", "fault_type", "fault_name", "fault_addr", "fault_bit")


def generate() -> list[dict]:
    rows = []
    for fault_type, fault_name in TYPES:
        for address in range(64):
            for bit in range(8):
                rows.append({
                    "fault_id": f"F{len(rows):04d}",
                    "fault_type": fault_type,
                    "fault_name": fault_name,
                    "fault_addr": address,
                    "fault_bit": bit,
                })
    assert len(rows) == 2048
    assert len({row["fault_id"] for row in rows}) == 2048
    assert len({(row["fault_type"], row["fault_addr"], row["fault_bit"])
                for row in rows}) == 2048
    for fault_type, _ in TYPES:
        assert sum(row["fault_type"] == fault_type for row in rows) == 512
    return rows


def write_manifest(rows: list[dict], output: Path = RESULTS) -> tuple[Path, Path, Path]:
    output.mkdir(parents=True, exist_ok=True)
    manifest = output / "fault_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    packed = output / "campaign.hex"
    packed.write_text("".join(
        f"{(int(row['fault_type']) << 9) | (int(row['fault_addr']) << 3) | int(row['fault_bit']):03x}\n"
        for row in rows), encoding="ascii")
    pilot_ids = {
        (fault_type - 1) * 512 + address * 8 + bit
        for fault_type, _ in TYPES
        for address, bit in zip(PILOT_ADDRESSES, PILOT_BITS)
    }
    pilot_rows = [row for index, row in enumerate(rows) if index in pilot_ids]
    assert len(pilot_rows) == 32
    pilot = output / "pilot_manifest.csv"
    with pilot.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(pilot_rows)
    return manifest, packed, pilot


if __name__ == "__main__":
    paths = write_manifest(generate())
    print(f"MANIFEST_PASS faults=2048 pilot=32 paths={','.join(path.name for path in paths)}")
