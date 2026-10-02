# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : audit_step08_ila.py
# Module  : audit_step08_ila
# -----------------------------------------------------------------------------
#!/usr/bin/env python3
"""Audit the original board ILA capture against the frozen March C− sequence."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT / "results" / "step08" / "hardware"
CAPTURE_DIR = HARDWARE / "ila_capture"
CAPTURE = CAPTURE_DIR / "2026-09-26_march_c_minus_64x8_full_run.ila"
SPEC = ROOT / "specs" / "march_c_minus_64x8.csv"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def number(row: dict[str, str], field: str) -> int:
    return int(row[field], 10)


def main() -> None:
    require(CAPTURE.is_file(), f"missing original ILA capture: {CAPTURE}")
    require(SPEC.is_file(), f"missing frozen sequence: {SPEC}")

    with zipfile.ZipFile(CAPTURE) as archive:
        require(archive.testzip() is None, "corrupt ILA archive")
        csv_bytes = archive.read("waveform.csv")
        vcd_bytes = archive.read("waveform.vcd")
    # These are exact copies of files inside the native Vivado .ila archive.
    (CAPTURE_DIR / "full_run_waveform.csv").write_bytes(csv_bytes)
    (CAPTURE_DIR / "full_run_waveform.vcd").write_bytes(vcd_bytes)

    samples = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig"))))
    with SPEC.open(newline="", encoding="utf-8") as stream:
        reference = list(csv.DictReader(stream))
    require(len(samples) == 1024, f"expected 1024 samples, got {len(samples)}")
    require(len(reference) == 640, f"expected 640 reference requests, got {len(reference)}")
    require(number(samples[0], "TRIGGER") == 1, "capture did not trigger at sample 0")
    require(number(samples[0], "start_pulse") == 1, "sample 0 lacks start pulse")

    for index, row in enumerate(samples):
        require(number(row, "Sample in Buffer") == index, f"noncontiguous sample {index}")
        require(number(row, "fail") == 0, f"FAIL asserted at sample {index}")
        require(number(row, "error_count[8:0]") == 0, f"error count at sample {index}")
        if index:
            prior = samples[index - 1]
            expected_count = number(prior, "accepted_count[9:0]") + number(prior, "req_valid")
            require(
                number(row, "accepted_count[9:0]") == expected_count,
                f"request counter mismatch at sample {index}",
            )
            expected_valid = number(prior, "req_valid") and not number(prior, "req_write")
            require(
                number(row, "rd_valid") == int(expected_valid),
                f"read response timing mismatch at sample {index}",
            )

    requests = [(index, row) for index, row in enumerate(samples) if number(row, "req_valid")]
    require(len(requests) == len(reference), f"expected 640 observed requests, got {len(requests)}")
    per_phase: Counter[str] = Counter()
    read_count = 0
    write_count = 0
    for sequence, ((sample_index, row), expected) in enumerate(zip(requests, reference)):
        phase = f"M{number(row, 'u_mbist/phase[2:0]')}"
        address = number(row, "req_addr[5:0]")
        operation = "write" if number(row, "req_write") else "read"
        require(number(expected, "seq") == sequence, f"bad reference index {sequence}")
        require(phase == expected["phase"], f"phase mismatch at request {sequence}")
        require(address == number(expected, "address"), f"address mismatch at request {sequence}")
        require(operation == expected["operation"], f"operation mismatch at request {sequence}")
        per_phase[phase] += 1
        if operation == "write":
            write_count += 1
            require(
                int(row["req_wdata[7:0]"], 16) == int(expected["write_data"], 16),
                f"write data mismatch at request {sequence}",
            )
        else:
            read_count += 1
            response = samples[sample_index + 1]
            require(number(response, "rd_valid") == 1, f"missing read response at request {sequence}")
            require(
                int(response["rd_data[7:0]"], 16) == int(expected["expected_read"], 16),
                f"read data mismatch at request {sequence}",
            )

    expected_per_phase = {"M0": 64, "M1": 128, "M2": 128, "M3": 128, "M4": 128, "M5": 64}
    require(dict(per_phase) == expected_per_phase, f"stage totals differ: {per_phase}")
    require(read_count == 320 and write_count == 320, "read/write totals differ")
    first_done = next((i for i, row in enumerate(samples) if number(row, "done")), None)
    first_pass = next((i for i, row in enumerate(samples) if number(row, "pass")), None)
    require(first_done == first_pass == 961, f"unexpected completion samples: {first_done}, {first_pass}")
    require(all(not number(row, "done") for row in samples[:first_done]), "premature DONE")
    require(all(number(row, "done") and number(row, "pass") for row in samples[first_done:]), "result not held")
    final = samples[-1]
    require(number(final, "accepted_count[9:0]") == 640, "final request count differs")
    require(number(final, "busy") == 0, "BUSY remained asserted")

    summary = {
        "status": "pass",
        "capture": str(CAPTURE.relative_to(ROOT)).replace("\\", "/"),
        "sample_count": len(samples),
        "trigger_sample": 0,
        "request_count": len(requests),
        "read_count": read_count,
        "write_count": write_count,
        "requests_by_phase": expected_per_phase,
        "last_request_sample": requests[-1][0],
        "last_request_phase": "M5",
        "last_request_address": number(requests[-1][1], "req_addr[5:0]"),
        "last_read_response_sample": max(i for i, row in enumerate(samples) if number(row, "rd_valid")),
        "first_done_sample": first_done,
        "first_pass_sample": first_pass,
        "final_done": number(final, "done"),
        "final_pass": number(final, "pass"),
        "final_fail": number(final, "fail"),
        "final_error_count": number(final, "error_count[8:0]"),
        "final_busy": number(final, "busy"),
        "final_accepted_count": number(final, "accepted_count[9:0]"),
        "scope": "one normal 64x8 FPGA BRAM run; no on-board fault injection",
    }
    (HARDWARE / "ila_audit.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"STEP08_HARDWARE_ILA_AUDIT_PASS samples={len(samples)} requests={len(requests)} "
        f"reads={read_count} writes={write_count} done_sample={first_done} pass=1 fail=0"
    )


if __name__ == "__main__":
    main()
