# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : run_step08_board.py
# Module  : run_step08_board
# -----------------------------------------------------------------------------
"""Run the board wrapper's short functional regression on XSim and Icarus."""

import json
import subprocess
from pathlib import Path
from project_config import build_dir, result_dir, tool as tool_path, record_environment

from run_step04 import oracle_text


ROOT = Path(__file__).resolve().parents[1]
WORK = build_dir("step08")
OUT = result_dir("step08") / "simulation"
RTL = [ROOT / "rtl" / name for name in (
    "address_generator.v", "data_generator.v", "memory_interface.v",
    "response_checker.v", "march_controller.v", "mbist_top.v",
    "single_port_sync_ram.v",
)]
SOURCES = RTL + [ROOT / "fpga" / "board_top.v",
                 ROOT / "tb" / "march_transaction_checker.sv",
                 ROOT / "tb" / "tb_board_top.sv"]


def run(args: list[str], cwd: Path, log: Path) -> str:
    process = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                             errors="replace", timeout=180)
    output = process.stdout + process.stderr
    log.write_text(output, encoding="utf-8")
    if process.returncode:
        raise RuntimeError(f"{log.name} failed with {process.returncode}: {output[-1000:]}")
    return output


def main() -> None:
    record_environment(OUT)
    results = {}
    for tool in ("icarus", "xsim"):
        results[tool] = {}
        for variant, top in (("normal", "tb_board_top"), ("fault", "tb_board_fault")):
            directory = WORK / tool / variant
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "oracle.hex").write_text(oracle_text(), encoding="ascii")
            prefix = f"{tool}_{variant}"
            if tool == "icarus":
                run([tool_path("iverilog"), "-g2012", "-s", top, "-o", "board.vvp",
                     *(str(path) for path in SOURCES)], directory, OUT / f"{prefix}_compile.log")
                output = run([tool_path("vvp"), "board.vvp"], directory, OUT / f"{prefix}_run.log")
            else:
                run([tool_path("xvlog"), "-sv", *(str(path) for path in SOURCES)],
                    directory, OUT / f"{prefix}_compile.log")
                run([tool_path("xelab"), top, "-s", "board_snapshot"],
                    directory, OUT / f"{prefix}_elaborate.log")
                output = run([tool_path("xsim"), "board_snapshot", "-runall"],
                             directory, OUT / f"{prefix}_run.log")
            if ("BOARD_TB_PASS rounds=3" not in output or
                    output.count("BOARD_CASE_PASS ") != 3 or
                    output.count("CHECKER_PASS run=1 requests=640") != 3 or
                    "CHECKER_FAIL" in output):
                raise RuntimeError(f"{prefix} did not complete the board regression")
            results[tool][variant] = {"rounds": 3, "requests_per_round": 640,
                "led_at_done": "0101" if variant == "fault" else "0011",
                "error_count": int(variant == "fault"), "status": "pass",
                "busy_start": "ignored", "active_reset": "pass"}
    (OUT / "summary.json").write_text(json.dumps(results, indent=2) + "\n",
                                       encoding="utf-8")
    print("STEP08_BOARD_SIM_PASS tools=2 rounds_per_tool=6 requests_per_round=640")


if __name__ == "__main__":
    main()
