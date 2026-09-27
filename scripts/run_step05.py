# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : run_step05.py
# Module  : run_step05
# -----------------------------------------------------------------------------
"""Directed, isolated fault-RAM and MBIST tests; no coverage calculation."""

import csv
import re
import subprocess
import sys
from pathlib import Path
from project_config import build_dir, result_dir, tool as tool_path, record_environment

from run_step04 import oracle_text


PROJECT = Path(__file__).resolve().parents[1]
WORK = build_dir("step05")
RESULTS = result_dir("step05")
RTL = [PROJECT / "rtl" / name for name in (
    "address_generator.v", "data_generator.v", "memory_interface.v",
    "response_checker.v", "march_controller.v", "mbist_top.v")]
FAULT = [PROJECT / "tb" / name for name in ("fault_injector.sv", "faulty_memory.sv")]
SUITES = {
    "unit": FAULT + [PROJECT / "tb" / "tb_faulty_memory_unit.sv"],
    "mbist": RTL + FAULT + [PROJECT / "tb" / name for name in (
        "fault_reference_monitor.sv", "march_transaction_checker.sv", "tb_step05_mbist.sv")],
}
TOPS = {"unit": "tb_faulty_memory_unit", "mbist": "tb_step05_mbist"}
CASES = (
    ("none_a7_b2", 0, 7, 2),
    ("sa0_a7_b2", 1, 7, 2),
    ("sa1_a7_b2", 2, 7, 2),
    ("rising_a7_b2", 3, 7, 2),
    ("falling_a7_b2", 4, 7, 2),
    ("sa0_a63_b7", 1, 63, 7),
    ("falling_a0_b0", 4, 0, 0),
)
RESULT = re.compile(
    r"FAULT_CASE_RESULT type=(\d+) addr=(\d+) bit=(\d+) activated=(\d+) "
    r"activations=(\d+) detected=(\d+) errors=(\d+) first_phase=(\d+) "
    r"first_addr=(\d+) first_expected=([0-9a-fA-F]{2}) first_actual=([0-9a-fA-F]{2})"
)
FIELDS = ("tool", "suite", "case", "fault_type", "fault_addr", "fault_bit",
          "activated", "activation_count", "detected", "error_count",
          "first_phase", "first_addr", "first_expected", "first_actual",
          "status", "detail", "run_log")


def command(args: list[str], cwd: Path, log: Path) -> tuple[int, str]:
    process = subprocess.run(args, cwd=cwd, capture_output=True, text=True, errors="replace")
    output = process.stdout + process.stderr
    log.write_text(output, encoding="utf-8")
    return process.returncode, output


def build(tool: str, suite: str) -> Path:
    directory = WORK / tool / suite
    directory.mkdir(parents=True, exist_ok=True)
    if suite == "mbist":
        (directory / "oracle.hex").write_text(oracle_text(), encoding="ascii")
    source_paths = [str(path) for path in SUITES[suite]]
    prefix = f"{tool}_{suite}"
    if tool == "icarus":
        code, output = command([tool_path("iverilog"), "-g2012", "-s", TOPS[suite],
                                "-o", "suite.vvp", *source_paths],
                               directory, RESULTS / f"{prefix}_compile.log")
        if code:
            raise RuntimeError(f"{prefix} compile failed: {output[-500:]}")
    else:
        code, output = command([tool_path("xvlog"), "-sv", *source_paths],
                               directory, RESULTS / f"{prefix}_compile.log")
        if code:
            raise RuntimeError(f"{prefix} compile failed: {output[-500:]}")
        code, output = command([tool_path("xelab"), TOPS[suite], "-s", "step05_snapshot"],
                               directory, RESULTS / f"{prefix}_elaborate.log")
        if code:
            raise RuntimeError(f"{prefix} elaborate failed: {output[-500:]}")
    return directory


def expected_result(fault_type: int, addr: int, bit: int) -> tuple[int, ...]:
    mask = 1 << bit
    if fault_type == 0:
        return 0, 0, 0, 0, 0, 0, 0, 0
    if fault_type == 1:
        return 1, 2, 1, 2, 2, addr, 255, 255 & ~mask
    if fault_type == 2:
        return 1, 3, 1, 3, 1, addr, 0, mask
    if fault_type == 3:
        return 1, 2, 1, 2, 2, addr, 255, 255 & ~mask
    return 1, 2, 1, 2, 3, addr, 0, mask


def run_case(tool: str, suite: str, directory: Path, case: tuple) -> dict:
    name, fault_type, addr, bit = case
    prefix = f"{tool}_{suite}_{name}"
    log_name = prefix + ".log"
    if tool == "icarus":
        args = [tool_path("vvp"), "suite.vvp", f"+FAULT_TYPE={fault_type}",
                f"+FAULT_ADDR={addr}", f"+FAULT_BIT={bit}"]
    else:
        # The 2018.3 Windows .bat wrapper needs literal inner quotes around
        # NAME=VALUE; otherwise it splits the value after '=' into a switch.
        args = [tool_path("xsim"), "step05_snapshot", "-runall",
                "-testplusarg", f'"FAULT_TYPE={fault_type}"',
                "-testplusarg", f'"FAULT_ADDR={addr}"',
                "-testplusarg", f'"FAULT_BIT={bit}"']
    code, output = command(args, directory, RESULTS / log_name)
    row = {field: "" for field in FIELDS}
    row.update(tool=tool, suite=suite, case=name, fault_type=fault_type,
               fault_addr=addr, fault_bit=bit, run_log=log_name)
    if code != 0 or re.search(r"\b(?:FATAL|Fatal|ERROR:|CHECKER_FAIL|FAULT_REF_FAIL)\b", output):
        raise RuntimeError(f"{prefix} simulator reported failure exit={code}: {output[-500:]}")
    if suite == "unit":
        marker = f"FAULT_UNIT_PASS type={fault_type} addr={addr} bit={bit}"
        if marker not in output:
            raise RuntimeError(f"{prefix} missing unit pass marker: {output[-500:]}")
    else:
        matches = RESULT.findall(output)
        if len(matches) != 1 or output.count("CHECKER_PASS run=1 requests=640") != 1 or \
                f"FAULT_MBIST_PASS type={fault_type}" not in output:
            raise RuntimeError(f"{prefix} missing result/checker marker: {output[-500:]}")
        values = tuple(int(x, 16) if i >= 9 else int(x)
                       for i, x in enumerate(matches[0]))
        if values[:3] != (fault_type, addr, bit):
            raise RuntimeError(f"{prefix} configuration mismatch: {values[:3]}")
        if values[3:] != expected_result(fault_type, addr, bit):
            raise RuntimeError(f"{prefix} unexpected physical result: {values[3:]}")
        if output.count("FAULT_ACTIVATE ") != values[4]:
            raise RuntimeError(f"{prefix} activation event count mismatch")
        row.update(activated=values[3], activation_count=values[4],
                   detected=values[5], error_count=values[6],
                   first_phase=values[7], first_addr=values[8],
                   first_expected=f"{values[9]:02x}", first_actual=f"{values[10]:02x}")
    row["status"] = "PASS"
    return row


def main() -> None:
    record_environment(RESULTS)
    WORK.mkdir(parents=True, exist_ok=True)
    (RESULTS / "oracle.hex").write_text(oracle_text(), encoding="ascii")
    rows = []
    for tool in ("icarus", "xsim"):
        for suite in ("unit", "mbist"):
            try:
                directory = build(tool, suite)
                build_error = None
            except Exception as error:
                directory = WORK / tool / suite
                build_error = str(error)
            for case in CASES:
                try:
                    if build_error:
                        raise RuntimeError(build_error)
                    row = run_case(tool, suite, directory, case)
                except Exception as error:
                    row = {field: "" for field in FIELDS}
                    row.update(tool=tool, suite=suite, case=case[0],
                               fault_type=case[1], fault_addr=case[2], fault_bit=case[3],
                               status="FAIL", detail=str(error),
                               run_log=f"{tool}_{suite}_{case[0]}.log")
                rows.append(row)
                print(f"STEP05_{row['status']} {tool} {suite} {case[0]}", flush=True)

    for case in CASES:
        pair = [row for row in rows if row["suite"] == "mbist" and row["case"] == case[0]]
        fields = ("activated", "activation_count", "detected", "error_count",
                  "first_phase", "first_addr", "first_expected", "first_actual")
        if len(pair) == 2 and all(row["status"] == "PASS" for row in pair):
            if any(pair[0][field] != pair[1][field] for field in fields):
                for row in pair:
                    row["status"] = "FAIL"
                    row["detail"] = "XSim/Icarus result disagreement"

    with (RESULTS / "report.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    failures = sum(row["status"] != "PASS" for row in rows)
    if failures:
        raise RuntimeError(f"{failures} of {len(rows)} directed cases failed; see report.csv")
    print(f"STEP05_REGRESSION_PASS cases={len(rows)} unit=14 mbist=14 tool_parity=7")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"STEP05_REGRESSION_FAIL {error}", file=sys.stderr)
        raise SystemExit(1)
