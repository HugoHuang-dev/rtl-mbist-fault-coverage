# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : run_step04.py
# Module  : run_step04
# -----------------------------------------------------------------------------
"""Calibrate the independent checker with real, temporary RTL mutations."""

import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from project_config import build_dir, result_dir, tool as tool_path, record_environment


PROJECT = Path(__file__).resolve().parents[1]
WORK = build_dir("step04")
RESULTS = result_dir("step04")
RTL = [
    "single_port_sync_ram.v", "address_generator.v", "data_generator.v",
    "memory_interface.v", "response_checker.v", "march_controller.v",
    "mbist_top.v",
]
TB = [PROJECT / "tb" / "march_transaction_checker.sv",
      PROJECT / "tb" / "tb_step04_independent.sv"]

# Each replacement is checked for one exact occurrence. The production RTL is
# never edited; each variant gets one modified copy in the work directory.
MUTATIONS = {
    "address_order": (
        "address_generator.v",
        "addr <= down ? addr - 1'b1 : addr + 1'b1;",
        "addr <= down ? addr + 1'b1 : addr - 1'b1;", 1),
    "operation_order": (
        "march_controller.v",
        "(state == ISSUE && phase == 3'd0));",
        "(state == ISSUE && (phase == 3'd0 || phase == 3'd1)));", 2),
    "write_data": (
        "data_generator.v",
        "(phase == 3'd1 || phase == 3'd3)",
        "(phase == 3'd3)", 3),
    "compare_before_valid": (
        "mbist_top.v",
        ".compare_enable(compare_enable), .phase(phase), .address(address),",
        ".compare_enable(issue_valid && !issue_write), .phase(phase), .address(address),", 4),
    "early_done": (
        "march_controller.v",
        "if (phase == 3'd5)\n                    state <= DONE;",
        "if (phase == 3'd4)\n                    state <= DONE;", 5),
    "wrong_first_diagnostic": (
        "response_checker.v",
        "first_fail_addr <= address;",
        "first_fail_addr <= address + 1'b1;", 6),
}


def oracle_text() -> str:
    with (PROJECT / "specs" / "march_c_minus_64x8.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 640:
        raise RuntimeError(f"Frozen CSV has {len(rows)} rows, expected 640")
    words = []
    for index, row in enumerate(rows):
        phase = int(row["phase"][1:])
        address = int(row["address"])
        write = row["operation"] == "write"
        data = int(row["write_data"] if write else row["expected_read"], 16)
        if int(row["seq"]) != index or not 0 <= phase <= 5 or not 0 <= address < 64:
            raise RuntimeError(f"Invalid oracle row {index}")
        words.append(f"{(phase << 15) | (address << 9) | (int(write) << 8) | data:05x}")
    return "\n".join(words) + "\n"


def run(command: list[str], cwd: Path, log: Path) -> tuple[int, str]:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, errors="replace")
    output = completed.stdout + completed.stderr
    log.write_text(output, encoding="utf-8")
    return completed.returncode, output


def sources_for(name: str, directory: Path) -> list[str]:
    sources = [PROJECT / "rtl" / source for source in RTL]
    if name in MUTATIONS:
        file_name, old, new, _ = MUTATIONS[name]
        original = PROJECT / "rtl" / file_name
        source = original.read_text(encoding="utf-8")
        if source.count(old) != 1:
            raise RuntimeError(f"Mutation anchor changed: {name}")
        alternate = directory / file_name
        alternate.write_text(source.replace(old, new, 1), encoding="utf-8")
        sources[RTL.index(file_name)] = alternate
    return [str(path) for path in [*sources, *TB]]


def simulate(engine: str, variant: str, oracle: str) -> dict:
    directory = WORK / engine / variant
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "oracle.hex").write_text(oracle, encoding="ascii")
    sources = sources_for(variant, directory)
    prefix = f"{engine}_{variant}"
    if engine == "icarus":
        compile_code, compile_output = run(
            [tool_path("iverilog"), "-g2012", "-s", "tb_step04_independent",
             "-o", "step04.vvp", *sources], directory, RESULTS / f"{prefix}_compile.log")
        if compile_code:
            raise RuntimeError(f"{prefix} compile failed: {compile_output[-1000:]}")
        code, output = run([tool_path("vvp"), "step04.vvp"],
                           directory, RESULTS / f"{prefix}_run.log")
    else:
        compile_code, compile_output = run(
            [tool_path("xvlog"), "-sv", *sources],
            directory, RESULTS / f"{prefix}_compile.log")
        if compile_code:
            raise RuntimeError(f"{prefix} compile failed: {compile_output[-1000:]}")
        elaborate_code, elaborate_output = run(
            [tool_path("xelab"), "tb_step04_independent", "-s", "step04_snapshot"],
            directory, RESULTS / f"{prefix}_elaborate.log")
        if elaborate_code:
            raise RuntimeError(f"{prefix} elaborate failed: {elaborate_output[-1000:]}")
        code, output = run([tool_path("xsim"), "step04_snapshot", "-runall"],
                           directory, RESULTS / f"{prefix}_run.log")

    if variant == "baseline":
        good = (code == 0 and output.count("CHECKER_PASS run=") == 2
                and "STEP04_PASS independent_checker_normal_and_diagnostic" in output
                and "CHECKER_FAIL" not in output)
        detected_code = None
    else:
        detected_code = MUTATIONS[variant][3]
        good = (f"CHECKER_FAIL code={detected_code} " in output
                and re.search(r"\bfatal\b", output, re.IGNORECASE) is not None
                and "STEP04_PASS" not in output)
    if not good:
        raise RuntimeError(f"{prefix} unexpected result exit={code}: {output[-1200:]}")
    return {"engine": engine, "variant": variant,
            "dut_outcome": "accepted" if variant == "baseline" else "rejected",
            "regression_status": "PASS", "sim_exit": code,
            "detected_code": detected_code, "run_log": f"{prefix}_run.log", "detail": ""}


def main() -> None:
    record_environment(RESULTS)
    WORK.mkdir(parents=True, exist_ok=True)
    oracle = oracle_text()
    (RESULTS / "oracle.hex").write_text(oracle, encoding="ascii")
    rows = []
    for engine in ("icarus", "xsim"):
        for variant in ("baseline", *MUTATIONS):
            try:
                row = simulate(engine, variant, oracle)
            except Exception as error:
                row = {"engine": engine, "variant": variant, "dut_outcome": "unknown",
                       "regression_status": "FAIL", "sim_exit": "",
                       "detected_code": "", "run_log": f"{engine}_{variant}_run.log",
                       "detail": str(error)}
            rows.append(row)
            print(f"REGRESSION_{row['regression_status']} {engine} {variant} "
                  f"detected_code={row['detected_code']}", flush=True)
    with (RESULTS / "report.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (RESULTS / "report.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    failures = sum(row["regression_status"] != "PASS" for row in rows)
    if failures:
        raise RuntimeError(f"{failures} of {len(rows)} regression cases failed; see report.csv")
    print(f"STEP04_REGRESSION_PASS cases={len(rows)} baseline=2 detected_mutants=12")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"STEP04_REGRESSION_FAIL {error}", file=sys.stderr)
        raise SystemExit(1)
