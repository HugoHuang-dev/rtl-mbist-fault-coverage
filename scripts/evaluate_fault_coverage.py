# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : evaluate_fault_coverage.py
# Module  : evaluate_fault_coverage
# -----------------------------------------------------------------------------
"""Independently evaluate the frozen Step 6 fault universe and raw evidence.

This script only reads existing simulation evidence. It never invokes a simulator.
Coverage denominator is the 2048 unique fault IDs, not the 4096 tool records.
"""

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from project_config import audit_dir

from frozen_source import verify_step6_source_fingerprints


ROOT = Path(__file__).resolve().parents[1]
STEP6 = audit_dir("step06")
OUT = audit_dir("step07")
TYPES = (("1", "SA0"), ("2", "SA1"), ("3", "Rising_TF"), ("4", "Falling_TF"))
STAGES = tuple(f"M{index}" for index in range(6))
TOOLS = ("icarus", "xsim")
COMPARE = (
    "activated", "activation_count", "detected", "error_count",
    "first_fail_addr", "first_fail_stage", "first_fail_expected",
    "first_fail_actual", "request_count", "cycles", "simulation_status",
    "outcome",
)
BEGIN = re.compile(r"^CASE_BEGIN id=(\d+) type=(\d+) addr=(\d+) bit=(\d+)\s*$", re.M)
RESULT = re.compile(
    r"^CASE_RESULT id=(\d+) type=(\d+) addr=(\d+) bit=(\d+) "
    r"activated=(\d+) activations=(\d+) detected=(\d+) errors=(\d+) "
    r"first_phase=(\d+) first_addr=(\d+) first_expected=([0-9a-fA-F]{2}) "
    r"first_actual=([0-9a-fA-F]{2}) requests=(\d+) cycles=(\d+)\s*$", re.M
)
CHECKER = re.compile(r"^CHECKER_PASS run=1 requests=(\d+) cycles=(\d+) errors=(\d+)\s*$", re.M)
DONE = re.compile(r"^CAMPAIGN_DONE start=(\d+) count=(\d+)\s*$", re.M)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def table(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def project_path(name: str) -> Path:
    path = (ROOT / name).resolve()
    check(path.is_relative_to(ROOT.resolve()), f"path outside project: {name}")
    return path


def read_manifest() -> list[dict[str, str]]:
    rows = table(STEP6 / "fault_manifest.csv")
    expected = [
        (f"F{index:04d}", code, label, str(address), str(bit))
        for code, label in TYPES for address in range(64) for bit in range(8)
        for index in [(int(code) - 1) * 512 + address * 8 + bit]
    ]
    actual = [(r["fault_id"], r["fault_type"], r["fault_name"],
               r["fault_addr"], r["fault_bit"]) for r in rows]
    check(actual == expected, "manifest is not the frozen exhaustive 2048-instance universe")
    return rows


def read_spec() -> dict:
    rows = table(ROOT / "specs" / "march_c_minus_64x8.csv")
    check(len(rows) == 640, "March specification must have 640 requests")
    check([int(r["seq"]) for r in rows] == list(range(640)), "March sequence numbers differ")
    stage_counts = Counter(r["phase"] for r in rows)
    check(stage_counts == {"M0": 64, "M1": 128, "M2": 128,
                           "M3": 128, "M4": 128, "M5": 64}, "stage counts differ")
    operations = Counter(r["operation"] for r in rows)
    check(operations == {"read": 320, "write": 320}, "read/write counts differ")
    return {"requests": len(rows), "reads": operations["read"],
            "writes": operations["write"], "stage_operations": dict(stage_counts)}


def verify_step6_fingerprints() -> int:
    return verify_step6_source_fingerprints(STEP6 / "source_sha256.txt")


def parse_log(path: Path, expected_hash: str) -> dict[int, dict]:
    check(digest(path) == expected_hash, f"raw log SHA-256 differs: {path}")
    content = path.read_text(encoding="utf-8", errors="replace")
    completion = DONE.findall(content)
    check(len(completion) == 1, f"raw log lacks unique completion: {path}")
    check(not re.search(r"\b(?:FATAL|Fatal|CHECKER_FAIL|FAULT_REF_FAIL|RUNNER_TIMEOUT)\b",
                        content), f"raw log contains failure: {path}")
    begins = list(BEGIN.finditer(content))
    check(bool(begins), f"raw log has no cases: {path}")
    check(int(completion[0][1]) == len(begins),
          f"completion/case count differs: {path}")
    parsed = {}
    for position, begin in enumerate(begins):
        stop = begins[position + 1].start() if position + 1 < len(begins) else len(content)
        segment = content[begin.start():stop]
        ident, fault_type, address, bit = (int(v) for v in begin.groups())
        check(ident not in parsed, f"duplicate case in log: {path} id={ident}")
        result = RESULT.findall(segment)
        checker = CHECKER.findall(segment)
        check(len(result) == 1 and len(checker) == 1,
              f"missing/duplicate result or checker in {path} id={ident}")
        values = result[0]
        check(tuple(map(int, values[:4])) == (ident, fault_type, address, bit),
              f"begin/result config differs in {path} id={ident}")
        check(tuple(map(int, checker[0])) ==
              (int(values[12]), int(values[13]), int(values[7])),
              f"checker/result differs in {path} id={ident}")
        check(segment.count("FAULT_ACTIVATE ") == int(values[5]),
              f"activation events differ in {path} id={ident}")
        parsed[ident] = {"config": (fault_type, address, bit), "values": values}
    return parsed


def verify_record(row: dict[str, str], item: dict[str, str], logs: dict) -> None:
    fault_id = item["fault_id"]
    check(row["tool"] in TOOLS, f"unknown simulator: {fault_id}")
    check(all(row[key] == item[key] for key in
              ("fault_id", "fault_type", "fault_name", "fault_addr", "fault_bit")),
          f"result config differs from manifest: {fault_id} {row['tool']}")
    log_path = project_path(row["raw_log"])
    check(log_path.is_file(), f"raw log missing: {log_path}")
    check(re.fullmatch(r"[A-F0-9]{64}", row["raw_log_sha256"]) is not None,
          f"missing log hash: {fault_id} {row['tool']}")
    if log_path not in logs:
        if row["simulation_status"] == "valid":
            logs[log_path] = parse_log(log_path, row["raw_log_sha256"])
        else:
            check(digest(log_path) == row["raw_log_sha256"],
                  f"invalid-case raw log hash differs: {fault_id}")
            logs[log_path] = None
    else:
        check(digest(log_path) == row["raw_log_sha256"], f"log hash differs: {fault_id}")
    if row["simulation_status"] != "valid":
        check(row["simulation_status"] == "invalid" and bool(row["reason"]),
              f"invalid case lacks reason: {fault_id} {row['tool']}")
        return
    check(logs[log_path] is not None, f"valid case in invalid log: {fault_id}")
    ident = int(fault_id[1:])
    check(ident in logs[log_path], f"case missing from raw log: {fault_id} {row['tool']}")
    parsed = logs[log_path][ident]
    check(parsed["config"] == (int(item["fault_type"]), int(item["fault_addr"]),
                                int(item["fault_bit"])), f"raw config differs: {fault_id}")
    values = parsed["values"]
    expected = {
        "activated": values[4], "activation_count": values[5],
        "detected": values[6], "error_count": values[7],
        "first_fail_addr": values[9] if values[6] == "1" else "",
        "first_fail_stage": f"M{values[8]}" if values[6] == "1" else "",
        "first_fail_expected": values[10].upper() if values[6] == "1" else "",
        "first_fail_actual": values[11].upper() if values[6] == "1" else "",
        "request_count": values[12], "cycles": values[13],
    }
    check(all(row[key] == value for key, value in expected.items()),
          f"CSV differs from raw result: {fault_id} {row['tool']}")
    activated = int(row["activated"])
    detected = int(row["detected"])
    check(activated in (0, 1) and detected in (0, 1), f"invalid flags: {fault_id}")
    check(activated == int(int(row["activation_count"]) > 0),
          f"activation flag/count differ: {fault_id}")
    check(detected == int(int(row["error_count"]) > 0),
          f"detection flag/error count differ: {fault_id}")
    check(int(row["request_count"]) == 640 and int(row["cycles"]) > 0,
          f"incomplete sequence or cycle count: {fault_id}")
    check(not detected or row["first_fail_stage"] in STAGES,
          f"invalid first detection stage: {fault_id}")
    expected_outcome = ("not_activated" if not activated else
                        "activated_detected" if detected else "activated_escape")
    check(row["outcome"] == expected_outcome, f"outcome differs: {fault_id}")


def percent(numerator: int, denominator: int) -> str:
    return f"{100 * numerator / denominator:.2f}"


def main() -> None:
    manifest = read_manifest()
    spec = read_spec()
    source_count = verify_step6_fingerprints()
    records = table(STEP6 / "full" / "raw_results.csv")
    check(len(records) == 4096, f"expected 4096 tool records, got {len(records)}")
    by_key = {}
    logs = {}
    items = {item["fault_id"]: item for item in manifest}
    for row in records:
        check(row["fault_id"] in items, f"unknown fault ID: {row['fault_id']}")
        key = (row["fault_id"], row["tool"])
        check(key not in by_key, f"duplicate tool record: {key}")
        verify_record(row, items[row["fault_id"]], logs)
        by_key[key] = row
    check(set(by_key) == {(item["fault_id"], tool) for item in manifest for tool in TOOLS},
          "missing tool records")

    step6_consistency = {r["fault_id"]: r for r in
                         table(STEP6 / "full" / "consistency.csv")}
    check(len(step6_consistency) == 2048, "Step 6 consistency rows differ")
    detail = []
    matrix = {label: Counter() for _, label in TYPES}
    per_type = {label: Counter() for _, label in TYPES}
    request_values, cycle_values = [], []
    for item in manifest:
        fault_id = item["fault_id"]
        left, right = (by_key[(fault_id, tool)] for tool in TOOLS)
        differences = [field for field in COMPARE if left[field] != right[field]]
        prior = step6_consistency[fault_id]
        check(prior["match"] == str(int(not differences)) and
              prior["differences"] == ";".join(differences),
              f"Step 6 consistency table differs: {fault_id}")
        invalid = any(r["simulation_status"] != "valid" for r in (left, right))
        simulation_failed = any(r["simulation_status"] != "valid" and
                                r["reason"] != "detected_without_activation"
                                for r in (left, right))
        unactivated = any(r["simulation_status"] == "valid" and r["activated"] == "0"
                          for r in (left, right))
        undetected = any(r["simulation_status"] == "valid" and
                         r["activated"] == "1" and r["detected"] == "0"
                         for r in (left, right))
        confirmed = not (invalid or unactivated or undetected or differences) and all(
            r["activated"] == "1" and r["detected"] == "1" for r in (left, right))
        flags = {"confirmed_detected": int(confirmed), "not_activated": int(unactivated),
                 "activated_undetected": int(undetected), "simulation_invalid": int(invalid),
                 "simulation_failed": int(simulation_failed),
                 "tool_disagreement": int(bool(differences))}
        per_type[item["fault_name"]].update({key: value for key, value in flags.items() if value})
        if confirmed:
            matrix[item["fault_name"]][left["first_fail_stage"]] += 1
        for record in (left, right):
            if record["simulation_status"] == "valid":
                request_values.append(int(record["request_count"]))
                cycle_values.append(int(record["cycles"]))
        detail.append({**item, **flags,
                       "first_fail_stage": left["first_fail_stage"] if confirmed else "",
                       "first_fail_addr": left["first_fail_addr"] if confirmed else "",
                       "icarus_status": left["simulation_status"],
                       "xsim_status": right["simulation_status"],
                       "icarus_reason": left["reason"], "xsim_reason": right["reason"],
                       "disagree_fields": ";".join(differences),
                       "icarus_log": left["raw_log"], "xsim_log": right["raw_log"]})

    coverage = []
    stage_rows = []
    for _, label in TYPES:
        stats = per_type[label]
        coverage.append({"fault_type": label, "target_instances": 512,
                         **{field: stats[field] for field in (
                             "confirmed_detected", "not_activated", "activated_undetected",
                             "simulation_invalid", "simulation_failed", "tool_disagreement")},
                         "target_coverage_pct": percent(stats["confirmed_detected"], 512)})
        stage_rows.append({"fault_type": label, **{stage: matrix[label][stage] for stage in STAGES},
                           "confirmed_detected": stats["confirmed_detected"]})
    total = {key: sum(int(row[key]) for row in coverage) for key in (
        "target_instances", "confirmed_detected", "not_activated",
        "activated_undetected", "simulation_invalid", "simulation_failed",
        "tool_disagreement")}
    total["fault_type"] = "TOTAL"
    total["target_coverage_pct"] = percent(total["confirmed_detected"], 2048)
    coverage.append(total)
    stage_rows.append({"fault_type": "TOTAL",
                       **{stage: sum(row[stage] for row in stage_rows) for stage in STAGES},
                       "confirmed_detected": total["confirmed_detected"]})

    previous = json.loads((STEP6 / "full" / "summary.json").read_text(encoding="utf-8"))
    audit = json.loads((STEP6 / "audit.json").read_text(encoding="utf-8"))
    check(previous["target_fault_instances"] == len(manifest) and
          previous["records"] == len(records) and
          previous["invalid_records"] == sum(r["simulation_status"] != "valid" for r in records) and
          previous["tool_disagreements"] == total["tool_disagreement"],
          "computed counts differ from Step 6 summary")
    check(audit["manifest_instances"] == len(manifest) and
          audit["full"]["records"] == len(records) and
          audit["full"]["invalid"] == previous["invalid_records"],
          "computed counts differ from Step 6 audit")

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "fault_evaluation.csv", list(detail[0]), detail)
    write_csv(OUT / "coverage_by_type.csv", list(coverage[0]), coverage)
    write_csv(OUT / "detection_stage_matrix.csv", list(stage_rows[0]), stage_rows)
    exceptions = [row for row in detail if not row["confirmed_detected"]]
    write_csv(OUT / "exceptions.csv", list(detail[0]), exceptions)
    efficiency = {
        "theoretical_operations": spec["requests"], "theoretical_reads": spec["reads"],
        "theoretical_writes": spec["writes"], "stage_operations": spec["stage_operations"],
        "valid_tool_records": len(request_values),
        "observed_request_counts": sorted(set(request_values)),
        "observed_cycle_counts": sorted(set(cycle_values)),
        "cycle_definition": "Step 6 testbench: negedge iterations after start is deasserted until DONE is observed",
    }
    if len(request_values) == 4096 and len(set(request_values)) == 1 and \
            len(cycle_values) == 4096 and len(set(cycle_values)) == 1:
        efficiency.update(observed_requests=request_values[0], observed_cycles=cycle_values[0],
                          extra_cycles_vs_operation_count=cycle_values[0] - spec["requests"],
                          cycles_per_request=cycle_values[0] / request_values[0],
                          requests_per_cycle=request_values[0] / cycle_values[0],
                          nominal_duration_us_at_50mhz=cycle_values[0] / 50)
    (OUT / "efficiency.json").write_text(json.dumps(efficiency, indent=2) + "\n", encoding="utf-8")
    summary = {
        "target_unique_faults": len(manifest), "simulator_records": len(records),
        "raw_logs_checked": len(logs), "step06_source_fingerprints_checked": source_count,
        "coverage": coverage, "detection_stage_matrix": stage_rows,
        "exceptions": len(exceptions), "step06_summary_and_audit_match": True,
        "first_fail_address_matches_fault_address": sum(
            row["confirmed_detected"] and row["first_fail_addr"] == row["fault_addr"]
            for row in detail),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    source_files = [ROOT / "scripts" / "evaluate_fault_coverage.py",
                    STEP6 / "fault_manifest.csv", STEP6 / "full" / "raw_results.csv",
                    STEP6 / "full" / "consistency.csv", STEP6 / "full" / "summary.json",
                    STEP6 / "audit.json", STEP6 / "source_sha256.txt",
                    ROOT / "specs" / "march_c_minus_64x8.csv"]
    (OUT / "source_sha256.txt").write_text("".join(
        f"{digest(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in source_files),
        encoding="utf-8")
    print("STEP07_EVALUATION_PASS unique=2048 records=4096 "
          f"confirmed={total['confirmed_detected']} invalid={total['simulation_invalid']} "
          f"unactivated={total['not_activated']} undetected={total['activated_undetected']} "
          f"disagreements={total['tool_disagreement']}")


if __name__ == "__main__":
    main()
