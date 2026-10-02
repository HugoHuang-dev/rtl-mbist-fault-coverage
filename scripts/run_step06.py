# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : run_step06.py
# Module  : run_step06
# -----------------------------------------------------------------------------
"""Run the 2048-instance MBIST fault campaign without computing coverage."""

import argparse
import csv
import json
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from project_config import build_dir, result_dir, tool as tool_path, record_environment

from generate_fault_manifest import generate, write_manifest
from run_step04 import oracle_text


PROJECT = Path(__file__).resolve().parents[1]
WORK = build_dir("step06")
RESULTS = result_dir("step06")
SOURCES = [PROJECT / "rtl" / name for name in (
    "address_generator.v", "data_generator.v", "memory_interface.v",
    "response_checker.v", "march_controller.v", "mbist_top.v",
)] + [PROJECT / "tb" / name for name in (
    "fault_injector.sv", "faulty_memory.sv", "fault_reference_monitor.sv",
    "march_transaction_checker.sv", "tb_step06_campaign.sv",
)]
RESULT_LINE = re.compile(
    r"CASE_RESULT id=(\d+) type=(\d+) addr=(\d+) bit=(\d+) "
    r"activated=(\d+) activations=(\d+) detected=(\d+) errors=(\d+) "
    r"first_phase=(\d+) first_addr=(\d+) first_expected=([0-9a-fA-F]{2}) "
    r"first_actual=([0-9a-fA-F]{2}) requests=(\d+) cycles=(\d+)"
)
BEGIN_LINE = re.compile(r"CASE_BEGIN id=(\d+) type=(\d+) addr=(\d+) bit=(\d+)")
FIELDS = (
    "fault_id", "fault_type", "fault_name", "fault_addr", "fault_bit", "tool",
    "activated", "activation_count", "detected", "error_count", "first_fail_addr",
    "first_fail_stage", "first_fail_expected", "first_fail_actual", "request_count",
    "cycles", "simulation_status", "outcome", "reason", "attempts", "raw_log",
)
COMPARE_FIELDS = (
    "activated", "activation_count", "detected", "error_count", "first_fail_addr",
    "first_fail_stage", "first_fail_expected", "first_fail_actual", "request_count",
    "cycles", "simulation_status", "outcome",
)


def relative(path: Path) -> str:
    return path.relative_to(PROJECT).as_posix()


def save_snapshot() -> None:
    files = [PROJECT / "specs" / "march_c_minus_64x8.csv",
             RESULTS / "fault_manifest.csv", RESULTS / "campaign.hex",
             RESULTS / "pilot_manifest.csv", RESULTS / "oracle.hex",
             PROJECT / "scripts" / "generate_fault_manifest.py",
             PROJECT / "scripts" / "run_step04.py",
             PROJECT / "scripts" / "run_step06.py",
             PROJECT / "scripts" / "project_config.py",
             PROJECT / "scripts" / "audit_step06.py", *SOURCES]
    from zipfile import ZipFile, ZIP_DEFLATED
    with ZipFile(RESULTS / "source_snapshot.zip", "w", ZIP_DEFLATED) as snapshot:
        for path in files:
            snapshot.write(path, relative(path))


def run_command(args: list[str], cwd: Path, log: Path, timeout: float) -> tuple[int, str]:
    try:
        process = subprocess.run(args, cwd=cwd, capture_output=True,
                                 text=True, errors="replace", timeout=timeout)
        output = process.stdout + process.stderr
        code = process.returncode
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or b""
        stderr = error.stderr or b""
        output = (stdout.decode("utf-8", "replace") if isinstance(stdout, bytes) else stdout)
        output += (stderr.decode("utf-8", "replace") if isinstance(stderr, bytes) else stderr)
        output += "\nRUNNER_TIMEOUT\n"
        code = -1
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(output, encoding="utf-8")
    return code, output


def build(tool: str) -> Path:
    directory = WORK / tool
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "campaign.hex").write_bytes((RESULTS / "campaign.hex").read_bytes())
    (directory / "oracle.hex").write_bytes((RESULTS / "oracle.hex").read_bytes())
    src = [str(path) for path in SOURCES]
    if tool == "icarus":
        code, output = run_command(
            [tool_path("iverilog"), "-g2012", "-s", "tb_step06_campaign",
             "-o", "campaign.vvp", *src], directory,
            RESULTS / "build" / "icarus_compile.log", 120)
        if code:
            raise RuntimeError(f"Icarus compile failed: {output[-1000:]}")
    else:
        code, output = run_command([tool_path("xvlog"), "-sv", *src],
                                   directory, RESULTS / "build" / "xsim_compile.log", 120)
        if code:
            raise RuntimeError(f"XSim compile failed: {output[-1000:]}")
        code, output = run_command(
            [tool_path("xelab"), "tb_step06_campaign", "-s", "step06_snapshot"],
            directory, RESULTS / "build" / "xsim_elaborate.log", 120)
        if code:
            raise RuntimeError(f"XSim elaborate failed: {output[-1000:]}")
    return directory


def selection_file(directory: Path, selected: list[int]) -> None:
    if len(selected) > 2048 or len(set(selected)) != len(selected):
        raise ValueError("Invalid selection")
    padded = selected + [0] * (2048 - len(selected))
    (directory / "selection.hex").write_text(
        "".join(f"{index:03x}\n" for index in padded), encoding="ascii")


def simulator_args(tool: str, start: int, count: int) -> list[str]:
    if tool == "icarus":
        return [tool_path("vvp"), "campaign.vvp",
                f"+START_INDEX={start}", f"+CASE_COUNT={count}"]
    # Literal inner quotes are required by Vivado 2018.3's Windows batch wrapper.
    return [tool_path("xsim"), "step06_snapshot", "-runall",
            "-testplusarg", f'"START_INDEX={start}"',
            "-testplusarg", f'"CASE_COUNT={count}"']


def blank_record(manifest: dict, tool: str, attempts: int, log: Path) -> dict:
    row = {key: "" for key in FIELDS}
    row.update({key: manifest[key] for key in (
        "fault_id", "fault_type", "fault_name", "fault_addr", "fault_bit")})
    row.update(tool=tool, attempts=attempts, raw_log=relative(log))
    return row


def parse_chunk(output: str, code: int, ids: list[int], start: int,
                manifest: list[dict], tool: str, attempts: Counter,
                log: Path) -> dict[int, dict]:
    if code != 0 or re.search(r"\b(?:Fatal|FATAL|CHECKER_FAIL|FAULT_REF_FAIL|RUNNER_TIMEOUT)\b",
                              output):
        raise ValueError(f"simulator failure exit={code}")
    if f"CAMPAIGN_DONE start={start} count={len(ids)}" not in output:
        raise ValueError("missing CAMPAIGN_DONE")
    begins = list(BEGIN_LINE.finditer(output))
    if len(begins) != len(ids):
        raise ValueError(f"CASE_BEGIN count {len(begins)} != {len(ids)}")
    records = {}
    for position, begin in enumerate(begins):
        segment_end = begins[position + 1].start() if position + 1 < len(begins) else len(output)
        segment = output[begin.start():segment_end]
        expected_id = ids[position]
        item = manifest[expected_id]
        config = tuple(map(int, begin.groups()))
        expected_config = (expected_id, int(item["fault_type"]),
                           int(item["fault_addr"]), int(item["fault_bit"]))
        if config != expected_config:
            raise ValueError(f"CASE_BEGIN config mismatch {config} != {expected_config}")
        matches = RESULT_LINE.findall(segment)
        if len(matches) != 1 or segment.count("CHECKER_PASS run=1 requests=640") != 1:
            raise ValueError(f"missing result/checker pass for {item['fault_id']}")
        groups = matches[0]
        values = [int(value, 16) if index in (10, 11) else int(value)
                  for index, value in enumerate(groups)]
        if tuple(values[:4]) != expected_config:
            raise ValueError(f"CASE_RESULT config mismatch for {item['fault_id']}")
        activated, activations, detected, errors = values[4:8]
        first_phase, first_addr, first_expected, first_actual = values[8:12]
        requests, cycles = values[12:14]
        if requests != 640 or not 0 <= activations <= 320 or \
                activated not in (0, 1) or detected not in (0, 1):
            raise ValueError(f"invalid result fields for {item['fault_id']}")
        if activated != int(activations > 0):
            raise ValueError(f"activation flag/count disagree for {item['fault_id']}")
        if segment.count("FAULT_ACTIVATE ") != activations:
            raise ValueError(f"activation event mismatch for {item['fault_id']}")
        row = blank_record(item, tool, attempts[expected_id], log)
        row.update(activated=activated, activation_count=activations,
                   detected=detected, error_count=errors,
                   first_fail_addr=first_addr if detected else "",
                   first_fail_stage=f"M{first_phase}" if detected else "",
                   first_fail_expected=f"{first_expected:02X}" if detected else "",
                   first_fail_actual=f"{first_actual:02X}" if detected else "",
                   request_count=requests, cycles=cycles)
        if detected and not activated:
            row.update(simulation_status="invalid", outcome="invalid",
                       reason="detected_without_activation")
        else:
            row.update(simulation_status="valid", reason="")
            row["outcome"] = ("not_activated" if not activated else
                              "activated_detected" if detected else "activated_escape")
        records[expected_id] = row
    return records


def execute_selected(tool: str, mode: str, selected: list[int],
                     manifest: list[dict], chunk_size: int, directory: Path) -> list[dict]:
    selection_file(directory, selected)
    attempts: Counter = Counter()
    serial = 0

    def attempt(start: int, count: int) -> dict[int, dict]:
        nonlocal serial
        ids = selected[start:start + count]
        for index in ids:
            attempts[index] += 1
        serial += 1
        log = RESULTS / "raw" / mode / tool / f"run_{serial:04d}_offset_{start:04d}_count_{count:04d}.log"
        timeout = max(45, 30 + count * 2)
        code, output = run_command(simulator_args(tool, start, count), directory, log, timeout)
        try:
            return parse_chunk(output, code, ids, start, manifest, tool, attempts, log)
        except Exception as error:
            print(f"CHUNK_RETRY tool={tool} mode={mode} offset={start} count={count} reason={error}",
                  flush=True)
            if count == 1:
                row = blank_record(manifest[ids[0]], tool, attempts[ids[0]], log)
                row.update(simulation_status="invalid", outcome="invalid", reason=str(error))
                return {ids[0]: row}
            left = count // 2
            return {**attempt(start, left), **attempt(start + left, count - left)}

    by_id = {}
    for start in range(0, len(selected), chunk_size):
        count = min(chunk_size, len(selected) - start)
        by_id.update(attempt(start, count))
        print(f"CAMPAIGN_PROGRESS tool={tool} mode={mode} processed={len(by_id)}/{len(selected)}",
              flush=True)
    if set(by_id) != set(selected):
        raise RuntimeError(f"{tool} {mode}: missing or duplicate fault records")
    return [by_id[index] for index in selected]


def write_table(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_mode(mode: str, selected: list[int], manifest: list[dict],
               rows: list[dict], tools: list[str]) -> tuple[int, int]:
    folder = RESULTS / mode
    folder.mkdir(parents=True, exist_ok=True)
    write_table(folder / "raw_results.csv", FIELDS, rows)
    (folder / "raw_results.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    consistency = []
    if len(tools) == 2:
        by_tool = {tool: {row["fault_id"]: row for row in rows if row["tool"] == tool}
                   for tool in tools}
        for index in selected:
            fault_id = manifest[index]["fault_id"]
            left, right = (by_tool[tools[0]][fault_id], by_tool[tools[1]][fault_id])
            differences = [field for field in COMPARE_FIELDS if left[field] != right[field]]
            consistency.append({"fault_id": fault_id,
                                "match": int(not differences),
                                "differences": ";".join(differences)})
        write_table(folder / "consistency.csv", ("fault_id", "match", "differences"), consistency)
    invalid = sum(row["simulation_status"] != "valid" for row in rows)
    mismatches = sum(not row["match"] for row in consistency)
    summary = {
        "mode": mode, "target_fault_instances": len(selected), "tools": tools,
        "records": len(rows), "invalid_records": invalid,
        "tool_disagreements": mismatches,
        "status_counts": dict(Counter(row["simulation_status"] for row in rows)),
        "outcome_counts": dict(Counter(row["outcome"] for row in rows)),
    }
    (folder / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return invalid, mismatches


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("all", "pilot", "full", "replay"), default="all")
    parser.add_argument("--tool", choices=("both", "xsim", "icarus"), default="both")
    parser.add_argument("--fault-id", help="Required for --mode replay, e.g. F0123")
    parser.add_argument("--chunk-size", type=int, default=64)
    args = parser.parse_args()
    if not 1 <= args.chunk_size <= 2048:
        parser.error("--chunk-size must be 1..2048")
    if (args.mode == "replay") != bool(args.fault_id):
        parser.error("--fault-id is required only for --mode replay")

    manifest = generate()
    write_manifest(manifest, RESULTS)
    record_environment(RESULTS)
    (RESULTS / "oracle.hex").write_text(oracle_text(), encoding="ascii")
    tools = ["icarus", "xsim"] if args.tool == "both" else [args.tool]
    built = {tool: build(tool) for tool in tools}

    pilot = [int(row["fault_id"][1:]) for row in csv.DictReader(
        (RESULTS / "pilot_manifest.csv").open(newline="", encoding="utf-8"))]
    modes = ["pilot", "full"] if args.mode == "all" else [args.mode]
    for mode in modes:
        if mode == "pilot":
            selected = pilot
        elif mode == "full":
            selected = list(range(2048))
        else:
            if not re.fullmatch(r"F\d{4}", args.fault_id or ""):
                parser.error("Fault ID must have form F0000..F2047")
            index = int(args.fault_id[1:])
            if not 0 <= index < 2048:
                parser.error("Fault ID out of range")
            selected = [index]
            mode = f"replay/{args.fault_id}"
        rows = []
        for tool in tools:
            rows.extend(execute_selected(tool, mode, selected, manifest,
                                         args.chunk_size, built[tool]))
        invalid, mismatches = write_mode(mode, selected, manifest, rows, tools)
        print(f"MODE_RESULT mode={mode} instances={len(selected)} records={len(rows)} "
              f"invalid={invalid} disagreements={mismatches}", flush=True)
        if invalid or mismatches:
            raise RuntimeError(f"{mode}: inspect recorded invalid cases or tool disagreements")
        if mode.startswith("replay/"):
            full_path = RESULTS / "full" / "raw_results.csv"
            if full_path.exists():
                with full_path.open(newline="", encoding="utf-8") as stream:
                    originals = {(row["fault_id"], row["tool"]): row
                                 for row in csv.DictReader(stream)}
                for row in rows:
                    original = originals.get((row["fault_id"], row["tool"]))
                    if original is None or any(str(row[field]) != original[field]
                                               for field in COMPARE_FIELDS):
                        raise RuntimeError(f"Replay disagrees with full run: "
                                           f"{row['fault_id']} {row['tool']}")
                print(f"REPLAY_MATCH_FULL fault_id={rows[0]['fault_id']} tools={len(tools)}",
                      flush=True)
    save_snapshot()
    print("STEP06_CAMPAIGN_PASS", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"STEP06_CAMPAIGN_FAIL {error}", file=sys.stderr)
        raise SystemExit(1)
