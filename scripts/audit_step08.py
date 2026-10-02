# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : audit_step08.py
# Module  : audit_step08
# -----------------------------------------------------------------------------
"""Audit offline Step 8 build artifacts without claiming hardware validation."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "step08"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def text(path: Path) -> str:
    require(path.is_file(), f"missing file: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def number(report: str, label: str) -> int:
    match = re.search(rf"(?m)^\|\s*{re.escape(label)}\s*\|\s*(\d+)\s*\|", report)
    require(match is not None, f"missing utilization row: {label}")
    return int(match.group(1))


def wns(report: str) -> float:
    segment = report.split("| Design Timing Summary", 1)[1]
    match = re.search(r"(?m)^\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+\d+\s+\d+", segment)
    require(match is not None, "missing WNS/TNS")
    require("All user specified timing constraints are met." in segment,
            "timing constraints not met")
    require(float(match.group(1)) >= 0 and float(match.group(2)) == 0,
            "timing slack is negative")
    return float(match.group(1))


def main() -> None:
    controller = text(OUT / "controller" / "utilization.rpt")
    base = text(OUT / "base" / "implemented_utilization.rpt")
    ila = text(OUT / "ila" / "utilization.rpt")
    bram = text(OUT / "base" / "bram_configuration.txt")
    require("primitive=RAMB18E1" in bram and "DOA_REG=0" in bram and
            "WRITE_MODE_A=NO_CHANGE" in bram, "BRAM interface mapping differs")
    require("Device Grade = industrial" in text(
        OUT / "base" / "implemented_operating_conditions.rpt"),
        "board operating grade differs")
    require("Device Grade = industrial" in text(
        OUT / "ila" / "operating_conditions.rpt"),
        "ILA operating grade differs")
    base_wns = wns(text(OUT / "base" / "implemented_timing_summary.rpt"))
    ila_wns = wns(text(OUT / "ila" / "timing_summary.rpt"))
    ltx = text(OUT / "ila" / "board_with_ila.ltx")
    for signal in ("start_pulse", "u_mbist/phase", "req_addr", "req_valid",
                   "req_write", "rd_valid", "rd_data", "accepted_count", "done",
                   "pass", "fail", "error_count", "first_fail_phase",
                   "first_fail_addr", "first_fail_expected", "first_fail_actual"):
        require(f'"name": "{signal}"' in ltx, f"ILA probe absent: {signal}")
    simulation = json.loads(text(OUT / "simulation" / "summary.json"))
    require(all(simulation[tool]["status"] == "pass" and
                simulation[tool]["requests_per_round"] == 640 and
                simulation[tool]["rounds"] == 2 for tool in ("xsim", "icarus")),
            "board wrapper regression differs")
    artifacts = [
        ROOT / "fpga" / "vivado" / "mbist_board.xpr",
        OUT / "base" / "board_top.bit",
        OUT / "ila" / "board_with_ila.bit",
        OUT / "ila" / "board_with_ila.ltx",
    ]
    require(all(path.is_file() and path.stat().st_size > 0 for path in artifacts),
            "project/bitstream/probe artifact missing")
    summary = {
        "device_part": "xc7a35tfgg484-2", "operating_grade": "Industrial",
        "clock_mhz": 50, "board_memory": "64x8",
        "controller_only": {"lut": number(controller, "Slice LUTs*"),
                            "registers": number(controller, "Slice Registers"),
                            "ramb18": number(controller, "RAMB18")},
        "base_complete_system": {"lut": number(base, "Slice LUTs"),
                                 "registers": number(base, "Slice Registers"),
                                 "ramb18": number(base, "RAMB18"), "wns_ns": base_wns},
        "ila_instrumented_system": {"lut": number(ila, "Slice LUTs"),
                                    "registers": number(ila, "Slice Registers"),
                                    "ramb18": number(ila, "RAMB18"),
                                    "wns_ns": ila_wns},
        "mut_bram_primitive": "RAMB18E1", "mut_bram_doa_reg": 0,
        "ila_depth": 1024, "ila_probes": 18,
        "board_wrapper_simulation": simulation,
        "hardware_pass": None, "hardware_capture": "not_evaluated_by_offline_audit",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                       encoding="utf-8")
    print(f"STEP08_OFFLINE_AUDIT_PASS controller_lut={summary['controller_only']['lut']} "
          f"base_lut={summary['base_complete_system']['lut']} "
          f"base_wns={base_wns:.3f} ila_wns={ila_wns:.3f} hardware=not_evaluated")


if __name__ == "__main__":
    main()
