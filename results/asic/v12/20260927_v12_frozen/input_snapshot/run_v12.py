"""Verify an archived Nangate45 netlist with the frozen independent checker."""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

from run_v10 import (CASES, ROOT, TB, checked_result, digest, execute, oracle,
                     testbench, tool_path)


def structure(run_dir: Path, netlist: Path, model: Path) -> dict:
    text = netlist.read_text(encoding="utf-8")
    model_text = model.read_text(encoding="utf-8")
    cells = Counter(re.findall(r"^  ([A-Z][A-Z0-9_]+) \S+\s+\($", text, re.MULTILINE))
    modules = set(re.findall(r"^module ([A-Z][A-Z0-9_]+)\(", model_text, re.MULTILINE))
    missing = sorted(set(cells) - modules)
    check = run_dir / "orfs/reports/nangate45/mbist_asic_top/base/synth_check.txt"
    stat = run_dir / "orfs/reports/nangate45/mbist_asic_top/base/synth_stat.txt"
    check_text, stat_text = check.read_text(), stat.read_text()
    if not cells or missing or "Found and reported 0 problems" not in check_text:
        raise RuntimeError(f"Incomplete standard-cell mapping: cells={sum(cells.values())}, missing={missing}")
    if any(name.startswith(("$", "LATCH", "DLH", "DLL")) for name in cells):
        raise RuntimeError("Unexpected unmapped or latch cell")
    if "-        -        -        - memories" not in stat_text or "-        -        -        - processes" not in stat_text:
        raise RuntimeError("Unexpected memory or process in final netlist")
    if "Chip area for module" not in stat_text or cells.get("DFF_X1", 0) == 0:
        raise RuntimeError("Missing mapped registers or synthesis summary")
    if sum(cells.values()) != 264 or cells["DFF_X1"] != 42:
        raise RuntimeError(f"Cell inventory changed from V11 baseline: {cells}")
    result = {"total_cells": sum(cells.values()), "registers": cells["DFF_X1"],
              "cell_types": dict(sorted(cells.items())), "missing_models": missing,
              "synth_check": "0 problems", "netlist_sha256": digest(netlist),
              "model_sha256": digest(model)}
    (run_dir / "structure.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def compare_v11_inputs(run_dir: Path) -> dict:
    base = ROOT / "results/asic/v11/20260927_v11_frozen/toolchain.txt"
    def hashes(path: Path) -> dict[str, str]:
        found = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.fullmatch(r"([0-9a-f]{64})\s+(.+)", line)
            if match:
                name = match[2].replace("\\", "/")
                key = name.split("mbist-fault-coverage/", 1)[-1]
                if key == name:
                    key = Path(name).name
                found[key] = match[1]
        return found
    prior, current = hashes(base), hashes(run_dir / "toolchain.txt")
    names = ["NangateOpenCellLibrary_typical.lib", "asic/config/config.mk",
             "asic/config/constraint.sdc", *("rtl/" + name for name in
             ("address_generator.v", "data_generator.v", "memory_interface.v",
              "response_checker.v", "march_controller.v", "mbist_top.v")),
             "asic/rtl/mbist_asic_top.v"]
    different = [name for name in names if not prior.get(name) or prior[name] != current.get(name)]
    result = {"v11_toolchain": str(base.relative_to(ROOT)).replace("\\", "/"),
              "matched_inputs": names, "different": different, "status": "PASS" if not different else "FAIL"}
    (run_dir / "input_comparison.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if different:
        raise RuntimeError(f"V11/V12 frozen input mismatch: {different}")
    return result


def compile_suite(tool: str, suite: str, work: Path, netlist: Path, model: Path,
                  executables: dict[str, str]) -> None:
    bench = testbench(suite, "asic", work)
    if tool == "xsim":
        # XSim 2018.3 rejects a design that mixes modules with and without a
        # timescale. Prefix only simulation copies; leave archived netlist
        # and cell functions byte-for-byte unchanged.
        for source, name in ((netlist, "netlist_timescale.v"),
                             (model, "cell_model_timescale.v")):
            (work / name).write_text("`timescale 1ns/1ps\n" + source.read_text(encoding="utf-8"),
                                     encoding="utf-8")
        netlist = work / "netlist_timescale.v"
        model = work / "cell_model_timescale.v"
    files = [model, netlist, TB / "march_transaction_checker.sv"]
    if suite == "sequence":
        files.append(ROOT / "rtl/single_port_sync_ram.v")
    else:
        files.extend(TB / name for name in ("fault_injector.sv", "faulty_memory.sv",
                                            "fault_reference_monitor.sv"))
    files.append(bench)
    top = "tb_step04_independent" if suite == "sequence" else "tb_step05_mbist"
    if tool == "icarus":
        execute([executables["iverilog"], "-g2012", "-s", top, "-o", "suite.vvp",
                 *map(str, files)], work, work / "compile.log")
    else:
        execute([executables["xvlog"], "-sv", *map(str, files)], work, work / "compile.log")
        execute([executables["xelab"], top, "-s", "v12_snapshot"], work,
                work / "elaborate.log")


def run_suite(tool: str, suite: str, work: Path, case: tuple | None,
              executables: dict[str, str]) -> dict:
    suffix = "sequence" if case is None else case[0]
    args = [] if case is None else [f"+FAULT_TYPE={case[1]}",
                                   f"+FAULT_ADDR={case[2]}", f"+FAULT_BIT={case[3]}"]
    if tool == "icarus":
        command = [executables["vvp"], "suite.vvp", *args]
    else:
        plusargs = [part for arg in args for part in ("-testplusarg", f'"{arg[1:]}"')]
        command = [executables["xsim"], "v12_snapshot", "-runall", *plusargs]
    return checked_result(suite, execute(command, work, work / f"{suffix}.log"), case)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--tool", choices=("icarus", "xsim", "both"), default="both")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
        parser.error("Invalid run ID")
    run_dir = ROOT / "results/asic/v12" / args.run_id
    netlist = run_dir / "orfs/results/nangate45/mbist_asic_top/base/1_2_yosys.v"
    model = run_dir / "cell_model.v"
    if not netlist.is_file() or not model.is_file():
        parser.error("Run asic/scripts/run_v12.sh in WSL first")
    inventory = structure(run_dir, netlist, model)
    comparison = compare_v11_inputs(run_dir)
    frozen = {}
    for tool, run in (("icarus", "20260927_icarus_v10"),
                      ("xsim", "20260927_xsim_v10")):
        report = json.loads((ROOT / "results/asic/v10" / run / "report.json").read_text())
        if report["status"] != "PASS":
            raise RuntimeError(f"V10 frozen reference failed: {tool}")
        frozen[tool] = report["results"]
    oracle_text = oracle()
    (run_dir / "oracle.hex").write_text(oracle_text, encoding="ascii")
    used = [ROOT / "asic/rtl/asic_rtl.f", ROOT / "asic/config/config.mk",
            ROOT / "asic/config/constraint.sdc", ROOT / "specs/march_c_minus_64x8.csv",
            TB / "tb_step04_independent.sv", TB / "tb_step05_mbist.sv",
            TB / "march_transaction_checker.sv", ROOT / "rtl/single_port_sync_ram.v",
            *(TB / name for name in ("fault_injector.sv", "faulty_memory.sv",
                                       "fault_reference_monitor.sv")),
            ROOT / "asic/scripts/run_v12.py", ROOT / "asic/scripts/run_v12.sh",
            ROOT / "asic/scripts/run_v10.py", netlist, model]
    used.extend(ROOT / line.strip() for line in (ROOT / "asic/rtl/asic_rtl.f").read_text().splitlines()
                if line.strip() and not line.lstrip().startswith("#"))
    manifest = {str(path.relative_to(ROOT)).replace("\\", "/"): digest(path) for path in used}
    (run_dir / "sources_sha256.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    selected = ("icarus", "xsim") if args.tool == "both" else (args.tool,)
    executables = {}
    if "icarus" in selected:
        executables["iverilog"] = tool_path("iverilog", r"C:\iverilog\bin\iverilog.exe")
        executables["vvp"] = tool_path("vvp", r"C:\iverilog\bin\vvp.exe")
    if "xsim" in selected:
        base = r"C:\Xilinx\Vivado\2018.3\bin"
        for name in ("xvlog", "xelab", "xsim"):
            executables[name] = tool_path(name, base + "\\" + name + ".bat")
    results = {}
    summary = {"status": "FAIL", "run_id": args.run_id, "structure": inventory,
               "v11_input_comparison": comparison,
               "tools": list(selected), "results": results}
    try:
        for tool in selected:
            for suite in ("sequence", "fault"):
                work = run_dir / tool / suite
                work.mkdir(parents=True, exist_ok=True)
                (work / "oracle.hex").write_text(oracle_text, encoding="ascii")
                compile_suite(tool, suite, work, netlist, model, executables)
                for case in ((None,) if suite == "sequence" else CASES):
                    suffix = "sequence" if case is None else case[0]
                    key = f"{tool}/netlist/{suite}/{suffix}"
                    result = run_suite(tool, suite, work, case, executables)
                    reference = frozen[tool][f"{tool}/asic/{suite}/{suffix}"]
                    if json.loads(json.dumps(result)) != reference:
                        raise RuntimeError(f"Netlist/V10 external result differs: {key}: {result} vs {reference}")
                    results[key] = result
                    print("PASS", key, flush=True)
        if args.tool == "both":
            for suite in ("sequence", "fault"):
                for case in ((None,) if suite == "sequence" else CASES):
                    suffix = "sequence" if case is None else case[0]
                    if results[f"icarus/netlist/{suite}/{suffix}"] != results[f"xsim/netlist/{suite}/{suffix}"]:
                        raise RuntimeError(f"Icarus/XSim disagreement: {suite}/{suffix}")
        summary["status"] = "PASS"
        summary["scenario_count"] = len(results)
    except Exception as error:
        summary["error"] = str(error)
        raise
    finally:
        (run_dir / "report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("REPORT", run_dir / "report.json", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"V12_REGRESSION_FAIL {error}", file=sys.stderr)
        sys.exit(1)
