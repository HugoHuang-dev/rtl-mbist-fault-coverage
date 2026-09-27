"""Run RAM unit and v3 white-box integration tests with both simulators."""
import argparse
import subprocess
from project_config import ROOT, build_dir, result_dir, tool, record_environment
from check_step03_trace import check

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("step02", "step03", "both"), default="both")
    args = parser.parse_args()
    for stage in (["step02", "step03"] if args.stage == "both" else [args.stage]):
        out = result_dir(stage)
        record_environment(out)
        top = "tb_single_port_sync_ram" if stage == "step02" else "tb_mbist_top"
        rtl = [ROOT / "rtl/single_port_sync_ram.v"]
        if stage == "step03":
            rtl += [ROOT / "rtl" / name for name in ("address_generator.v", "data_generator.v",
                    "memory_interface.v", "response_checker.v", "march_controller.v", "mbist_top.v")]
        sources = [str(p) for p in rtl + [ROOT / "tb" / (top + ".sv")]]
        for engine in ("icarus", "xsim"):
            work = build_dir(stage) / engine
            work.mkdir(parents=True, exist_ok=True)
            commands = ([[tool("iverilog"), "-g2012", "-s", top, "-o", "sim.vvp", *sources],
                         [tool("vvp"), "sim.vvp"]] if engine == "icarus" else
                        [[tool("xvlog"), "-sv", *sources], [tool("xelab"), top, "-s", "snapshot"],
                         [tool("xsim"), "snapshot", "-runall"]])
            for index, command in enumerate(commands):
                process = subprocess.run(command, cwd=work, capture_output=True, text=True, errors="replace", timeout=180)
                text = process.stdout + process.stderr
                log = out / f"{engine}_{index}.log"
                log.write_text(text, encoding="utf-8")
                if process.returncode:
                    raise RuntimeError(f"{stage}/{engine} failed: {log}")
            if stage == "step03":
                outcome = check(log)
            else:
                if "RAM_TB_PASS checks=146 reads=70 writes=68" not in text:
                    raise RuntimeError("RAM test did not finish")
                outcome = "RAM_TB_PASS checks=146 reads=70 writes=68"
            (out / f"{engine}_check.txt").write_text(outcome + "\n", encoding="utf-8")
            print(stage, engine, outcome, flush=True)

if __name__ == "__main__":
    main()
