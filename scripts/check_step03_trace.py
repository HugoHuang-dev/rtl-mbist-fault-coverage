# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : check_step03_trace.py
# Module  : check_step03_trace
# -----------------------------------------------------------------------------
"""Compare Step 3 simulator request traces with the frozen Step 1 CSV."""

import csv
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "specs" / "march_c_minus_64x8.csv"
TRACE = re.compile(r"^TRACE,(\d+),(\d+),(\d+),(\d+),([01]),([0-9a-fA-F]{2})$")
SUMMARY = re.compile(
    r"^CASE_PASS run=(\d+) requests=(\d+) reads=(\d+) writes=(\d+) "
    r"cycles=(\d+) pass=([01]) fail=([01]) errors=(\d+)$"
)


def check(log_path: Path) -> str:
    with ORACLE.open(newline="", encoding="utf-8") as stream:
        oracle = list(csv.DictReader(stream))
    assert len(oracle) == 640
    seen = {1: [], 2: []}
    summaries = {}
    raw = log_path.read_bytes()
    # Windows PowerShell 5.1 writes redirected native output as UTF-16LE.
    log = raw.decode("utf-16") if raw.startswith(b"\xff\xfe") else raw.decode("utf-8", errors="replace")
    for line in log.splitlines():
        match = TRACE.fullmatch(line.strip())
        if match:
            run, seq, phase, addr, write, data = match.groups()
            run = int(run)
            assert run in seen, f"Unexpected run {run}"
            seen[run].append((int(seq), int(phase), int(addr), int(write), int(data, 16)))
        match = SUMMARY.fullmatch(line.strip())
        if match:
            run, requests, reads, writes, cycles, passed, failed, errors = map(int, match.groups())
            assert run not in summaries
            summaries[run] = (requests, reads, writes, cycles, passed, failed, errors)
    assert "MBIST_TB_PASS normal_and_injected_continue" in log
    assert not re.search(r"FATAL|ERROR:", log), "Simulator reported an error"
    assert set(summaries) == {1, 2}
    for run in (1, 2):
        assert len(seen[run]) == 640, f"Run {run}: {len(seen[run])} requests"
        for index, (seq, phase, addr, write, data) in enumerate(seen[run]):
            row = oracle[index]
            assert seq == index == int(row["seq"]), f"Run {run}, row {index}: sequence"
            assert phase == int(row["phase"][1:]), f"Run {run}, row {index}: phase"
            assert addr == int(row["address"]), f"Run {run}, row {index}: address"
            assert write == (row["operation"] == "write"), f"Run {run}, row {index}: operation"
            if write:
                assert data == int(row["write_data"], 16), f"Run {run}, row {index}: data"
        requests, reads, writes, cycles, passed, failed, errors = summaries[run]
        assert (requests, reads, writes) == (640, 320, 320)
        assert (passed, failed, errors) == ((1, 0, 0) if run == 1 else (0, 1, 1))
        assert 900 <= cycles <= 1000
    return (
        f"TRACE_CHECK_PASS log={log_path.name} runs=2 requests=1280 "
        f"csv_rows=640 normal_cycles={summaries[1][3]} injected_cycles={summaries[2][3]}"
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/check_step03_trace.py results/step03/<run>.log")
    print(check(Path(sys.argv[1])))
