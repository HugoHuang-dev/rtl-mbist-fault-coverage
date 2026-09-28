"""Freeze V13 inputs and independently reconcile Yosys/Liberty area reports."""

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V12 = ROOT / "results/asic/v12/20260927_v12_frozen"
EXPECTED_IMAGE = "openroad/orfs@sha256:bc05b68ef2f023cb49d4a7f80b021d3895328c0e4ee8491ae9bdf6fc29771b9f"
EXPECTED_COMMIT = "b74a7293ea57fc4154a08471bcf78042ed497e4e"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def frozen_hashes() -> dict[str, str]:
    found = {}
    for line in (V12 / "toolchain.txt").read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})\s+(.+)", line)
        if match:
            found[Path(match[2]).name] = match[1]
    return found


def preflight(run: Path) -> dict:
    snapshot = run / "input_snapshot"
    old_report = json.loads((V12 / "report.json").read_text(encoding="utf-8"))
    old_structure = json.loads((V12 / "structure.json").read_text(encoding="utf-8"))
    require(old_report["status"] == "PASS" and old_report["scenario_count"] == 16,
            "V12 accepted gate-level regression is missing")
    toolchain = (V12 / "toolchain.txt").read_text(encoding="utf-8")
    require(f"ORFS_COMMIT {EXPECTED_COMMIT}" in toolchain and
            f"ORFS_IMAGE {EXPECTED_IMAGE}" in toolchain, "Wrong ORFS toolchain")
    expected = frozen_hashes()
    for name in ("1_2_yosys.v", "constraint.sdc", "NangateOpenCellLibrary_typical.lib"):
        require(name in expected and sha(snapshot / name) == expected[name],
                f"Frozen V12 input mismatch: {name}")
    require(sha(snapshot / "1_2_yosys.v") == old_structure["netlist_sha256"],
            "V12 structure report refers to another netlist")
    require(sha(snapshot / "constraint.sdc") == sha(ROOT / "asic/config/constraint.sdc"),
            "Current V11 SDC differs from accepted V12 input")
    for name in ("synth_stat.txt", "synth_check.txt", "report.json",
                 "structure.json", "toolchain.txt"):
        source = (V12 / "orfs/reports/nangate45/mbist_asic_top/base" / name
                  if name.startswith("synth_") else V12 / name)
        require(sha(snapshot / name) == sha(source), f"V12 evidence copy changed: {name}")
    require("Found and reported 0 problems" in (snapshot / "synth_check.txt").read_text(),
            "V12 Yosys check did not pass")
    files = {path.name: sha(path) for path in snapshot.iterdir() if path.is_file()}
    result = {"status": "PASS", "v12_run": "20260927_v12_frozen",
              "orfs_commit": EXPECTED_COMMIT, "orfs_image": EXPECTED_IMAGE,
              "input_sha256": files}
    (run / "preflight.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def liberty_cells(text: str) -> dict[str, tuple[Decimal, bool]]:
    headers = list(re.finditer(r"(?m)^\s*cell\s*\(\s*([A-Za-z0-9_]+)\s*\)\s*\{", text))
    cells = {}
    for index, match in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        body = text[match.end():end]
        area = re.search(r"(?m)^\s*area\s*:\s*([0-9.]+)\s*;", body)
        if area:
            cells[match[1]] = (Decimal(area[1]), bool(re.search(r"\b(ff|latch)\s*\(", body)))
    return cells


def lef_areas(text: str) -> dict[str, Decimal]:
    headers = list(re.finditer(r"(?m)^MACRO\s+([A-Za-z0-9_]+)\s*$", text))
    areas = {}
    for index, match in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        size = re.search(r"\bSIZE\s+([0-9.]+)\s+BY\s+([0-9.]+)\s*;", text[match.end():end])
        if size:
            areas[match[1]] = Decimal(size[1]) * Decimal(size[2])
    return areas


def area_audit(run: Path) -> dict:
    snapshot = run / "input_snapshot"
    stat = (snapshot / "synth_stat.txt").read_text(encoding="utf-8")
    structure = json.loads((snapshot / "structure.json").read_text(encoding="utf-8"))
    liberty = liberty_cells((snapshot / "NangateOpenCellLibrary_typical.lib").read_text(encoding="utf-8"))
    lef = lef_areas((snapshot / "NangateOpenCellLibrary.macro.mod.lef").read_text(encoding="utf-8"))
    rows = re.findall(r"(?m)^\s*(\d+)\s+([0-9.]+)\s+\d+\s+[0-9.]+\s+([A-Z][A-Z0-9_]+)\s*$", stat)
    cells = {name: (int(count), Decimal(area)) for count, area, name in rows}
    total = re.search(r"(?m)^\s*(\d+)\s+([0-9.]+)\s+\d+\s+[0-9.]+\s+cells\s*$", stat)
    reported_area = re.search(r"Chip area for module '\\mbist_asic_top':\s*([0-9.]+)", stat)
    require(total is not None and reported_area is not None and cells, "Cannot parse Yosys area report")
    require(set(cells) == set(structure["cell_types"]), "Yosys/V12 cell types differ")
    require(all(count == structure["cell_types"][name] for name, (count, _) in cells.items()),
            "Yosys/V12 cell counts differ")
    summary_rows = []
    for name, (count, yosys_area) in sorted(cells.items()):
        require(name in liberty, f"No Liberty area for {name}")
        per_cell, sequential = liberty[name]
        require(name in lef and abs(lef[name] - per_cell) <= Decimal("0.001"),
                f"Liberty/LEF physical area mismatch for {name}")
        recomputed = count * per_cell
        require(abs(recomputed - yosys_area) <= Decimal("0.001"),
                f"Liberty/Yosys area mismatch for {name}")
        summary_rows.append({"cell": name, "category": "sequential" if sequential else "combinational",
                             "count": count, "liberty_area_um2": str(per_cell),
                             "recomputed_area_um2": str(recomputed),
                             "yosys_area_um2": str(yosys_area)})
    count_sum = sum(row["count"] for row in summary_rows)
    area_sum = sum((Decimal(row["recomputed_area_um2"]) for row in summary_rows), Decimal(0))
    sequential_rows = [row for row in summary_rows if row["category"] == "sequential"]
    sequential_count = sum(row["count"] for row in sequential_rows)
    sequential_area = sum((Decimal(row["recomputed_area_um2"]) for row in sequential_rows), Decimal(0))
    require(count_sum == int(total[1]) == structure["total_cells"], "Total cell count differs")
    require(abs(area_sum - Decimal(total[2])) <= Decimal("0.001") and
            abs(area_sum - Decimal(reported_area[1])) <= Decimal("0.001"),
            "Cell areas do not add up to Yosys total")
    require(sequential_count == structure["registers"], "Sequential count differs")
    result = {"status": "PASS", "area_unit": "um^2", "cell_count": count_sum,
              "sequential_count": sequential_count,
              "combinational_count": count_sum - sequential_count,
              "total_area_um2": str(area_sum), "sequential_area_um2": str(sequential_area),
              "combinational_area_um2": str(area_sum - sequential_area),
              "yosys_reported_area_um2": reported_area[1], "per_cell": summary_rows}
    (run / "area_summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with (run / "area_cells.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=summary_rows[0].keys())
        writer.writeheader()
        writer.writerows(summary_rows)
    return result


def prepare(run: Path) -> dict:
    frozen = preflight(run)
    area = area_audit(run)
    required = ("setup_wns.rpt", "setup_top10.rpt", "setup_top10.json",
                "reg_to_reg.rpt", "input_to_reg.rpt", "reg_to_output.rpt",
                "input_to_output.rpt", "unconstrained_paths.rpt",
                "unconstrained_paths.json", "check_setup.rpt")
    missing = [name for name in required if not (run / "sta" / name).is_file()]
    require(not missing, f"Missing STA reports: {missing}")
    sta_log = (run / "sta.log").read_text(encoding="utf-8", errors="replace")
    require("V13_INTERCONNECT wire_load_model=5K_hvratio_1_1 mode=top" in sta_log and
            "V13_CLOCKS 1" in sta_log and "V13_INPUTS 13" in sta_log and
            "V13_OUTPUTS 54" in sta_log and "V13_REPORTS_WRITTEN" in sta_log,
            "STA did not finish with frozen conditions")
    require("[ERROR" not in sta_log and "Error:" not in sta_log,
            "OpenROAD reported an error")
    require(not (run / "sta/check_setup.rpt").read_text().strip(),
            "OpenROAD check_setup emitted diagnostics")
    paths = json.loads((run / "sta/unconstrained_paths.json").read_text(encoding="utf-8"))
    unconstrained = [path for path in paths["checks"]
                     if path.get("path_group", "").lower() == "unconstrained"]
    require(not unconstrained, "STA reported an unconstrained path group")
    report_hashes = {name: sha(run / "sta" / name) for name in required}
    result = {"status": "PREPARED_FOR_MANUAL_READINGS", "frozen_inputs": frozen["status"],
              "area_audit": area["status"], "sta_reports_sha256": report_hashes,
              "interconnect_model": "Nangate45 Liberty 5K_hvratio_1_1, top mode; pre-placement",
              "check_setup_diagnostics": 0, "unconstrained_path_group_count": len(unconstrained)}
    (run / "preparation_audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("preflight", "prepare"))
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    run = args.run_dir.resolve()
    result = preflight(run) if args.stage == "preflight" else prepare(run)
    print("V13_" + args.stage.upper() + "_PASS", result["status"])


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("V13_AUDIT_FAIL", error, file=sys.stderr)
        sys.exit(1)
