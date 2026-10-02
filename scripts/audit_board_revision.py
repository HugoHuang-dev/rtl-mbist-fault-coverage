"""Audit routed builds, board regression, and matching archived hardware captures."""
import json
import re
from project_config import ROOT, result_dir

def timing(path):
    text = path.read_text(encoding="utf-8")
    section = text.split("| Design Timing Summary", 1)[1]
    values = re.search(r"(?m)^\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(\d+)\s+\d+\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(\d+)", section)
    if not values or "WHS(ns)" not in section:
        raise ValueError(f"Setup/hold summary absent: {path}")
    wns, tns, setup_fail, whs, ths, hold_fail = map(float, values.groups())
    if wns < 0 or whs < 0 or tns != 0 or ths != 0 or setup_fail or hold_fail:
        raise ValueError(f"Timing violation: {path}")
    if not re.search(r"sys_clk\s+\{0\.000 10\.000\}\s+20\.000\s+50\.000", text):
        raise ValueError("50 MHz clock not found")
    return {"wns_ns": wns, "whs_ns": whs, "tns_ns": tns, "ths_ns": ths}

def utilization(path):
    text = path.read_text(encoding="utf-8")
    result = {}
    for key, label in (("lut", r"Slice LUTs\*?"), ("registers", "Slice Registers"),
                       ("ramb18", "RAMB18"), ("ramb36", "RAMB36/FIFO\\*?")):
        match = re.search(r"(?m)^\|\s*" + label + r"\s*\|\s*(\d+)\s*\|", text)
        if match: result[key] = int(match[1])
    if not {"lut", "registers", "ramb18"} <= result.keys():
        raise ValueError(f"Utilization rows absent: {path}")
    return result

def main():
    out = result_dir("step08")
    sim = json.loads((out / "simulation/summary.json").read_text())
    for tool in ("icarus", "xsim"):
        for mode in ("normal", "fault"):
            case = sim[tool][mode]
            if case["status"] != "pass" or case["rounds"] != 3 or case["requests_per_round"] != 640:
                raise ValueError("Board regression incomplete")
    builds = {}
    for variant in ("base", "ila", "base_fault", "ila_fault"):
        folder = out / variant
        debug = variant.startswith("ila")
        timing_path = folder / ("timing_summary.rpt" if debug else "implemented_timing_summary.rpt")
        cdc = (folder / "cdc.rpt").read_text()
        problems = [line for line in cdc.splitlines()
                    if re.match(r"\s+\d+\s+CDC-\d+\s+(Warning|Critical)\s", line)]
        if any("Critical" in line or "dbg_hub/" not in line for line in problems):
            raise ValueError(f"Unreviewed CDC issue in {variant}")
        if "key0" not in cdc or "CDC-9" not in cdc:
            raise ValueError("Input synchronization not recognized")
        check = (folder / "synchronizer_checks.txt").read_text()
        if check.count("TIMED_INTERSTAGE") != 3 or check.count("ASYNC_REG=1") != 4:
            raise ValueError("Synchronization checks incomplete")
        checks = (folder / "check_timing.rpt").read_text()
        for required in ("There are 0 register/latch pins with no clock.",
                         "There are 0 pins that are not constrained for maximum delay.",
                         "There are 0 input ports with no input delay specified.",
                         "There are 0 ports with no output delay specified."):
            if required not in checks: raise ValueError(required)
        bit = folder / ("board_with_ila.bit" if debug else "board_top.bit")
        if not bit.is_file() or not bit.stat().st_size: raise ValueError("Bitstream absent")
        if debug and not (folder / "board_with_ila.ltx").is_file(): raise ValueError("LTX absent")
        if not debug:
            bram = (folder / "bram_configuration.txt").read_text()
            if "primitive=RAMB18E1" not in bram or "DOA_REG=0" not in bram:
                raise ValueError("MUT BRAM mapping differs")
        builds[variant] = {**timing(timing_path), **utilization(folder / (
            "utilization.rpt" if debug else "implemented_utilization.rpt")),
            "cdc_debug_ip_warning_paths": len(problems)}
    hardware_status = "not_evaluated_for_this_build"
    hardware = None
    from audit_final_hardware import BUILD, audit
    if out.resolve() == BUILD.resolve():
        hardware = audit()
        hardware_status = hardware["status"]
    report = {"status": "pass", "clock_mhz": 50, "builds": builds,
              "board_simulation": sim, "hardware_status": hardware_status,
              "hardware_audit": hardware}
    (out / "revision_audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"BOARD_REVISION_AUDIT_PASS builds=4 setup=met hold=met hardware={hardware_status}")

if __name__ == "__main__":
    main()
