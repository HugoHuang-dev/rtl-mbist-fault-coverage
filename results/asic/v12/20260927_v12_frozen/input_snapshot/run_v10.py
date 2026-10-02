"""Compare the original controller and ASIC boundary with frozen V4/V5 checks."""

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FILELIST = ROOT / "asic/rtl/asic_rtl.f"
TB = ROOT / "tb"
CASES = (
    ("none_a7_b2", 0, 7, 2),
    ("sa0_a7_b2", 1, 7, 2),
    ("sa1_a7_b2", 2, 7, 2),
    ("rising_a7_b2", 3, 7, 2),
    ("falling_a7_b2", 4, 7, 2),
    ("sa0_a63_b7", 1, 63, 7),
    ("falling_a0_b0", 4, 0, 0),
)
CHECKER = re.compile(r"CHECKER_PASS run=(\d+) requests=(\d+) cycles=(\d+) errors=(\d+)")
FAULT = re.compile(r"^FAULT_CASE_RESULT .+$", re.MULTILINE)


def sources() -> list[Path]:
    names = [line.strip() for line in FILELIST.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    expected = [
        "rtl/address_generator.v", "rtl/data_generator.v",
        "rtl/memory_interface.v", "rtl/response_checker.v",
        "rtl/march_controller.v", "rtl/mbist_top.v",
        "asic/rtl/mbist_asic_top.v",
    ]
    if names != expected:
        raise RuntimeError("ASIC RTL file list changed; review its contents before synthesis")
    files = [ROOT / name for name in names]
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(path)
    return files


def oracle() -> str:
    with (ROOT / "specs/march_c_minus_64x8.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 640:
        raise RuntimeError("Frozen March CSV is not 640 requests")
    words = []
    for index, row in enumerate(rows):
        phase = int(row["phase"][1:])
        address = int(row["address"])
        write = row["operation"] == "write"
        data = int(row["write_data"] if write else row["expected_read"], 16)
        if int(row["seq"]) != index or not 0 <= phase <= 5 or not 0 <= address < 64:
            raise RuntimeError(f"Invalid frozen CSV row {index}")
        words.append(f"{(phase << 15) | (address << 9) | (int(write) << 8) | data:05x}")
    return "\n".join(words) + "\n"


def tool_path(executable: str, fallback: str) -> str:
    found = shutil.which(executable)
    if found:
        return found
    if Path(fallback).is_file():
        return fallback
    raise FileNotFoundError(f"Missing {executable}; install it or add it to PATH")


def execute(command: list[str], directory: Path, log: Path) -> str:
    process = subprocess.run(command, cwd=directory, capture_output=True,
                             text=True, errors="replace")
    output = process.stdout + process.stderr
    log.write_text("COMMAND: " + subprocess.list2cmdline(command) + "\n"
                   + f"EXIT_CODE: {process.returncode}\n" + output, encoding="utf-8")
    if process.returncode:
        raise RuntimeError(f"Command failed ({process.returncode}): {log}")
    return output


def testbench(suite: str, variant: str, directory: Path) -> Path:
    name = "tb_step04_independent.sv" if suite == "sequence" else "tb_step05_mbist.sv"
    text = (TB / name).read_text(encoding="utf-8")
    anchor = "mbist_top dut ("
    if text.count(anchor) != 1:
        raise RuntimeError(f"Unexpected DUT anchor in {name}")
    if variant == "asic":
        text = text.replace(anchor, "mbist_asic_top dut (", 1)
    output = directory / name
    output.write_text(text, encoding="utf-8")
    return output


def checked_result(suite: str, output: str, case: tuple | None) -> dict:
    if "CHECKER_FAIL" in output or "FAULT_MBIST_FAIL" in output:
        raise RuntimeError("Independent checker or fault test failed")
    checked = [tuple(map(int, row)) for row in CHECKER.findall(output)]
    if suite == "sequence":
        if len(checked) != 2 or checked[0][0:2] != (1, 640) or checked[0][3] != 0 or \
                checked[1][0:2] != (2, 640) or checked[1][3] != 1:
            raise RuntimeError(f"Unexpected normal/diagnostic sequence: {checked}")
        if "STEP04_PASS independent_checker_normal_and_diagnostic" not in output:
            raise RuntimeError("Missing sequence completion marker")
        return {"checker": checked}
    if case is None or len(checked) != 1 or checked[0][0:2] != (1, 640):
        raise RuntimeError(f"Fault case did not complete 640 requests: {checked}")
    matches = FAULT.findall(output)
    if len(matches) != 1 or f"FAULT_MBIST_PASS type={case[1]}" not in output:
        raise RuntimeError("Missing or duplicate fault result marker")
    fields = dict(re.findall(r"(\w+)=([0-9a-fA-F]+)", matches[0]))
    if (int(fields["type"]), int(fields["addr"]), int(fields["bit"])) != case[1:]:
        raise RuntimeError("Fault result differs from requested configuration")
    if int(fields["detected"]) != (case[1] != 0):
        raise RuntimeError("Unexpected fault detection status")
    if checked[0][3] != int(fields["errors"]):
        raise RuntimeError("Checker and DUT disagree on error count")
    return {"checker": checked, "fault": fields}


def compile_suite(tool: str, variant: str, suite: str, directory: Path,
                  rtl: list[Path], executables: dict[str, str]) -> None:
    bench = testbench(suite, variant, directory)
    files = rtl if variant == "asic" else rtl[:-1]
    files += [TB / "march_transaction_checker.sv"]
    if suite == "sequence":
        files += [ROOT / "rtl/single_port_sync_ram.v"]
    else:
        files += [TB / name for name in ("fault_injector.sv", "faulty_memory.sv",
                                       "fault_reference_monitor.sv")]
    files += [bench]
    top = "tb_step04_independent" if suite == "sequence" else "tb_step05_mbist"
    if tool == "icarus":
        execute([executables["iverilog"], "-g2012", "-s", top, "-o", "suite.vvp",
                 *map(str, files)], directory, directory / "compile.log")
    else:
        execute([executables["xvlog"], "-sv", *map(str, files)],
                directory, directory / "compile.log")
        execute([executables["xelab"], top, "-s", "v10_snapshot"],
                directory, directory / "elaborate.log")


def run_suite(tool: str, suite: str, directory: Path, case: tuple | None,
              executables: dict[str, str]) -> dict:
    suffix = "sequence" if case is None else case[0]
    args = [] if case is None else [f"+FAULT_TYPE={case[1]}",
                                   f"+FAULT_ADDR={case[2]}", f"+FAULT_BIT={case[3]}"]
    if tool == "icarus":
        command = [executables["vvp"], "suite.vvp", *args]
    else:
        # Vivado 2018.3's Windows batch wrapper requires the inner quotes.
        plusargs = [item for arg in args for item in ("-testplusarg", f'"{arg[1:]}"')]
        command = [executables["xsim"], "v10_snapshot", "-runall", *plusargs]
    output = execute(command, directory, directory / f"{suffix}.log")
    return checked_result(suite, output, case)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", choices=("icarus", "xsim", "both"), default="both")
    parser.add_argument("--run-id", default=datetime.now().strftime("%Y%m%d_%H%M%S"))
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
        parser.error("run-id must contain only letters, digits, underscore or hyphen")
    rtl = sources()
    run_dir = ROOT / "results/asic/v10" / args.run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    oracle_text = oracle()
    (run_dir / "oracle.hex").write_text(oracle_text, encoding="ascii")
    selected = ("icarus", "xsim") if args.tool == "both" else (args.tool,)
    executables = {}
    if "icarus" in selected:
        executables["iverilog"] = tool_path("iverilog", r"C:\iverilog\bin\iverilog.exe")
        executables["vvp"] = tool_path("vvp", r"C:\iverilog\bin\vvp.exe")
    if "xsim" in selected:
        base = r"C:\Xilinx\Vivado\2018.3\bin"
        executables["xvlog"] = tool_path("xvlog", base + r"\xvlog.bat")
        executables["xelab"] = tool_path("xelab", base + r"\xelab.bat")
        executables["xsim"] = tool_path("xsim", base + r"\xsim.bat")
    results = {}
    try:
        for tool in selected:
            for variant in ("baseline", "asic"):
                for suite in ("sequence", "fault"):
                    directory = run_dir / tool / variant / suite
                    directory.mkdir(parents=True)
                    (directory / "oracle.hex").write_text(oracle_text, encoding="ascii")
                    compile_suite(tool, variant, suite, directory, rtl.copy(), executables)
                    cases = (None,) if suite == "sequence" else CASES
                    for case in cases:
                        key = f"{tool}/{variant}/{suite}/" + ("sequence" if case is None else case[0])
                        results[key] = run_suite(tool, suite, directory, case, executables)
                        print("PASS", key, flush=True)
            for suite in ("sequence", "fault"):
                for case in ((None,) if suite == "sequence" else CASES):
                    suffix = "sequence" if case is None else case[0]
                    base = results[f"{tool}/baseline/{suite}/{suffix}"]
                    asic = results[f"{tool}/asic/{suite}/{suffix}"]
                    if base != asic:
                        raise RuntimeError(f"Baseline/ASIC external result differs: {tool}/{suite}/{suffix}")
        if args.tool == "both":
            for suite in ("sequence", "fault"):
                for case in ((None,) if suite == "sequence" else CASES):
                    suffix = "sequence" if case is None else case[0]
                    if results[f"icarus/asic/{suite}/{suffix}"] != results[f"xsim/asic/{suite}/{suffix}"]:
                        raise RuntimeError(f"Icarus/XSim disagreement: {suite}/{suffix}")
        summary = {"status": "PASS", "run_id": args.run_id, "tools": list(selected),
                   "scenario_count": len(results), "results": results}
    except Exception as error:
        summary = {"status": "FAIL", "run_id": args.run_id, "tools": list(selected),
                   "error": str(error), "results": results}
        raise
    finally:
        (run_dir / "report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("REPORT", run_dir / "report.json", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"V10_REGRESSION_FAIL {error}", file=sys.stderr)
        sys.exit(1)
