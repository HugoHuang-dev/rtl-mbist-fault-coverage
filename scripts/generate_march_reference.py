# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : generate_march_reference.py
# Module  : generate_march_reference
# -----------------------------------------------------------------------------
"""Generate the Step 1 March C- request oracle; no RTL or simulator dependency."""

import csv
from collections import Counter
from pathlib import Path


DEPTH = 64
DATA_WIDTH = 8
ZERO = 0
ONE = (1 << DATA_WIDTH) - 1
OUT = Path(__file__).resolve().parents[1] / "specs" / "march_c_minus_64x8.csv"

# This is a declarative algorithm specification, separate from future controller RTL.
PHASES = (
    ("M0", "up", (("write", ZERO),)),
    ("M1", "up", (("read", ZERO), ("write", ONE))),
    ("M2", "up", (("read", ONE), ("write", ZERO))),
    ("M3", "down", (("read", ZERO), ("write", ONE))),
    ("M4", "down", (("read", ONE), ("write", ZERO))),
    ("M5", "up", (("read", ZERO),)),
)


def generate():
    rows = []
    shadow = [None] * DEPTH  # Undefined power-up state; M0 must write every address.
    for phase, direction, operations in PHASES:
        addresses = range(DEPTH) if direction == "up" else range(DEPTH - 1, -1, -1)
        for address in addresses:
            for operation, value in operations:
                if operation == "read":
                    if shadow[address] != value:
                        raise AssertionError(
                            f"Specification reads {phase} address {address} as {value:02X}, "
                            f"but independent shadow RAM contains {shadow[address]}"
                        )
                else:
                    shadow[address] = value
                rows.append(
                    {
                        "seq": len(rows),
                        "phase": phase,
                        "direction": direction,
                        "address": address,
                        "operation": operation,
                        "expected_read": f"0x{value:02X}" if operation == "read" else "",
                        "write_data": f"0x{value:02X}" if operation == "write" else "",
                    }
                )
    return rows


def validate(rows):
    assert len(rows) == 10 * DEPTH == 640
    assert Counter(row["operation"] for row in rows) == {"write": 320, "read": 320}
    assert Counter(row["phase"] for row in rows) == {
        "M0": 64, "M1": 128, "M2": 128, "M3": 128, "M4": 128, "M5": 64
    }
    assert all(row["seq"] == index for index, row in enumerate(rows))
    for phase, direction, operations in PHASES:
        phase_rows = [row for row in rows if row["phase"] == phase]
        expected_addresses = range(DEPTH) if direction == "up" else range(DEPTH - 1, -1, -1)
        assert [row["address"] for row in phase_rows] == [
            address for address in expected_addresses for _ in operations
        ]
        assert [row["operation"] for row in phase_rows] == [
            operation for _ in range(DEPTH) for operation, _ in operations
        ]


def main():
    rows = generate()
    validate(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} requests to {OUT}")
    print("Phases: M0=64, M1=128, M2=128, M3=128, M4=128, M5=64")
    print("Reads=320, writes=320; all read expectations match shadow RAM")


if __name__ == "__main__":
    main()
