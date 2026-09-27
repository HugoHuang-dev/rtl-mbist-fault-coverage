# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : audit_step06.py
# Module  : audit_step06
# -----------------------------------------------------------------------------
"""Audit Step 6 artifacts without rerunning simulations or computing coverage."""

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from project_config import audit_dir

from frozen_source import verify_step6_source_fingerprints


PROJECT = Path(__file__).resolve().parents[1]
RESULTS = audit_dir("step06")


def rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def check_mode(mode: str, expected: int, manifest: dict[str, dict]) -> dict:
    folder = RESULTS / mode
    records = rows(folder / "raw_results.csv")
    consistency = rows(folder / "consistency.csv")
    assert len(records) == 2 * expected, (mode, len(records))
    assert len(consistency) == expected
    assert len({row["fault_id"] for row in consistency}) == expected
    assert all(row["match"] == "1" for row in consistency)
    assert len({(row["fault_id"], row["tool"]) for row in records}) == 2 * expected
    assert {row["tool"] for row in records} == {"xsim", "icarus"}
    logs = {}
    for row in records:
        item = manifest[row["fault_id"]]
        assert all(row[key] == item[key] for key in
                   ("fault_type", "fault_name", "fault_addr", "fault_bit"))
        if row["simulation_status"] == "invalid":
            assert row["reason"] and row["outcome"] == "invalid"
        else:
            assert row["simulation_status"] == "valid" and row["request_count"] == "640"
            assert row["outcome"] in {"activated_detected", "activated_escape", "not_activated"}
        log_path = PROJECT / row["raw_log"]
        if log_path not in logs:
            raw = log_path.read_bytes()
            logs[log_path] = {
                "hash": hashlib.sha256(raw).hexdigest().upper(),
                "content": raw.decode("utf-8", "replace"),
            }
        log = logs[log_path]
        assert row["raw_log_sha256"] == log["hash"]
        numeric_id = int(row["fault_id"][1:])
        assert re.search(rf"^CASE_BEGIN id={numeric_id}\b", log["content"], re.MULTILINE)
        if row["simulation_status"] == "valid":
            assert re.search(rf"^CASE_RESULT id={numeric_id}\b", log["content"], re.MULTILINE)
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    assert summary["records"] == len(records)
    assert summary["invalid_records"] == sum(
        row["simulation_status"] != "valid" for row in records)
    assert summary["tool_disagreements"] == 0
    return {"instances": expected, "records": len(records),
            "raw_logs": len(logs), "invalid": summary["invalid_records"],
            "outcomes": dict(Counter(row["outcome"] for row in records))}


def main() -> None:
    source_count = verify_step6_source_fingerprints(RESULTS / "source_sha256.txt")
    items = rows(RESULTS / "fault_manifest.csv")
    assert len(items) == 2048
    manifest = {row["fault_id"]: row for row in items}
    assert len(manifest) == 2048
    assert Counter(row["fault_type"] for row in items) == {
        "1": 512, "2": 512, "3": 512, "4": 512}
    assert len({(row["fault_type"], row["fault_addr"], row["fault_bit"])
                for row in items}) == 2048
    expected_configurations = {
        (str(fault_type), str(address), str(bit))
        for fault_type in range(1, 5) for address in range(64) for bit in range(8)
    }
    assert {(row["fault_type"], row["fault_addr"], row["fault_bit"])
            for row in items} == expected_configurations
    assert [row["fault_id"] for row in items] == [f"F{index:04d}" for index in range(2048)]
    pilot = rows(RESULTS / "pilot_manifest.csv")
    assert len(pilot) == 32 and len({row["fault_id"] for row in pilot}) == 32
    report = {
        "source_fingerprints_checked": source_count,
        "manifest_instances": len(items),
        "pilot": check_mode("pilot", 32, manifest),
        "full": check_mode("full", 2048, manifest),
    }
    (RESULTS / "audit.json").write_text(json.dumps(report, indent=2) + "\n",
                                         encoding="utf-8")
    print("STEP06_AUDIT_PASS manifest=2048 pilot_records=64 "
          "full_records=4096 tool_pairs=2048")


if __name__ == "__main__":
    main()
