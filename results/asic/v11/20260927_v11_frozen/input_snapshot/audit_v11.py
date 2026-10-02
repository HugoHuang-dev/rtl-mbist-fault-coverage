"""Audit V11 ORFS source selection and effective post-synthesis SDC."""

import json
import re
import sys
from pathlib import Path


EXPECTED_RTL = (
    "rtl/address_generator.v", "rtl/data_generator.v", "rtl/memory_interface.v",
    "rtl/response_checker.v", "rtl/march_controller.v", "rtl/mbist_top.v",
    "asic/rtl/mbist_asic_top.v",
)
PATH_SECTIONS = (
    "MAX_PATH", "RESET_INPUT_PATH", "MEMORY_RESPONSE_PATH", "READY_INPUT_PATH",
    "VALID_INPUT_PATH", "START_INPUT_PATH", "REGISTER_PATH",
    "REQUEST_OUTPUT_PATH", "STATUS_OUTPUT_PATH",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def section(text: str, label: str) -> str:
    begin = f"V11_{label}_BEGIN"
    end = f"V11_{label}_END"
    require(text.count(begin) == 1 and text.count(end) == 1, f"Missing {label} audit section")
    return text.split(begin, 1)[1].split(end, 1)[0]


def delay_ports(sdc: str, command: str, qualifier: str) -> list[str]:
    names = []
    expected = 0.0 if qualifier == "min" else 2.0
    for line in sdc.splitlines():
        if line.startswith(command + " ") and f"-{qualifier}" in line:
            value = re.match(rf"^{command} ([0-9.]+)", line)
            require(value is not None and float(value.group(1)) == expected,
                    f"Wrong {command} -{qualifier} delay")
            match = re.search(r"\[get_ports \{([^}]+)\}\]", line)
            require(match is not None, f"Cannot parse {command} port in effective SDC")
            names.append(match.group(1))
    return names


def main() -> None:
    run = Path(sys.argv[1]).resolve()
    project = Path(__file__).resolve().parents[2]
    config = (run / "config_parse.log").read_text(encoding="utf-8", errors="replace")
    synth = (run / "synth_validation.log").read_text(encoding="utf-8", errors="replace")
    check = (run / "constraint_check.log").read_text(encoding="utf-8", errors="replace")
    stage = run / "orfs/results/nangate45/mbist_asic_top/base"
    reports = run / "orfs/reports/nangate45/mbist_asic_top/base"
    effective = (stage / "1_synth.sdc").read_text(encoding="utf-8")
    netlist = (stage / "1_2_yosys.v").read_text(encoding="utf-8")
    synth_check = (reports / "synth_check.txt").read_text(encoding="utf-8")

    require("DESIGN_NAME: mbist_asic_top" in config, "Wrong ORFS top")
    require("PLATFORM: nangate45" in config, "Wrong ORFS platform")
    require("ABC_CLOCK_PERIOD_IN_PS: 20000" in config, "Wrong ABC clock")
    config_rtl = re.search(r"^VERILOG_FILES: (.+)$", config, re.MULTILINE)
    require(config_rtl is not None, "Missing ORFS RTL list")
    actual_rtl = tuple(path.split("/work/mbist/", 1)[-1] for path in config_rtl.group(1).split())
    require(actual_rtl == EXPECTED_RTL, f"Unexpected ORFS RTL list: {actual_rtl}")
    require("SDC_FILE: /work/mbist/asic/config/constraint.sdc" in config, "Wrong SDC path")
    require("link_design mbist_asic_top" in synth and "read_sdc " in synth,
            "ORFS did not link top and load SDC")
    require("write_db " in synth and (stage / "1_synth.odb").stat().st_size > 0,
            "Missing preliminary synthesized design")
    require("Found and reported 0 problems" in synth_check, "Yosys check reported problems")
    require("module mbist_asic_top(" in netlist, "Wrong synthesized top")
    require(not re.search(r"single_port_sync_ram|faulty_memory|board_top|RAMB18|ILA", netlist),
            "Memory or FPGA module leaked into synthesis")
    require("Error:" not in synth and "Error:" not in check, "Tool reported an error")

    require("create_clock -name core_clock -period 20.0000" in effective,
            "20 ns clock missing from effective SDC")
    require("set_clock_uncertainty -setup 0.2000" in effective and
            "set_clock_uncertainty -hold 0.1000" in effective,
            "Clock uncertainty missing")
    expected_inputs = {"rst_n", "start", "req_ready", "rd_valid"}
    expected_inputs |= {f"rd_data[{bit}]" for bit in range(8)}
    input_min = delay_ports(effective, "set_input_delay", "min")
    input_max = delay_ports(effective, "set_input_delay", "max")
    require(len(input_min) == len(input_max) == 12 and
            set(input_min) == set(input_max) == expected_inputs,
            "Input min/max delays do not cover all 12 non-clock input bits")
    output_min = delay_ports(effective, "set_output_delay", "min")
    output_max = delay_ports(effective, "set_output_delay", "max")
    require(len(output_min) == len(output_max) == 54 and
            set(output_min) == set(output_max),
            "Output min/max delays do not cover all 54 output bits")
    loads = re.findall(r"^set_load -pin_load 4\.0000 \[get_ports \{([^}]+)\}\]$",
                       effective, re.MULTILINE)
    require(len(loads) == 54 and set(loads) == set(output_max),
            "4 fF load does not cover all outputs")
    transitions = re.findall(r"^set_input_transition 0\.1000 \[get_ports \{([^}]+)\}\]$",
                             effective, re.MULTILINE)
    require(len(transitions) == 12 and set(transitions) == expected_inputs,
            "0.1 ns input transition does not cover all data inputs")
    require(not re.search(r"^set_(false_path|multicycle_path|disable_timing)\b",
                          effective, re.MULTILINE), "Unexpected timing exception")

    require("V11_AUDIT_CLOCKS 1" in check and "V11_AUDIT_INPUTS 13" in check and
            "V11_AUDIT_OUTPUTS 54" in check, "Unexpected OpenROAD clock or port count")
    require(not section(check, "CHECK_SETUP").strip(), "OpenROAD check_setup emitted diagnostics")
    for name in PATH_SECTIONS:
        content = section(check, name)
        require("Startpoint:" in content and "Endpoint:" in content and "slack (MET)" in content,
                f"No constrained path in {name}")

    result = {"status": "PASS", "top": "mbist_asic_top", "platform": "nangate45",
              "clock_ns": 20.0, "input_bits_constrained": 12,
              "output_bits_constrained": 54, "timing_exceptions": 0,
              "audited_path_groups": list(PATH_SECTIONS)}
    (run / "audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("V11_AUDIT_PASS 12 input bits, 54 output bits, 9 path sections")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"V11_AUDIT_FAIL {error}", file=sys.stderr)
        sys.exit(1)
