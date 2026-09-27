"""Build normal or response-perturbed board images with Vivado 2018.3."""
import argparse
import json
import subprocess
from project_config import ROOT, RUN_ID, build_dir, result_dir, tool
import os

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fault", action="store_true")
    parser.add_argument("--ila", action="store_true", help="Build base first, then add ILA")
    args = parser.parse_args()
    variant = "fault" if args.fault else "normal"
    work = build_dir("vivado_driver_" + variant)
    out = result_dir("step08") / ("build_logs_" + variant)
    work.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, MBIST_RUN_ID=RUN_ID, MBIST_INJECT_FAULT=str(int(args.fault)))
    executable = tool("vivado")
    version = subprocess.run([executable, "-version"], cwd=work, capture_output=True, text=True, errors="replace", timeout=60)
    (out / "vivado_version.txt").write_text(version.stdout + version.stderr, encoding="utf-8")
    if version.returncode or "2018.3" not in version.stdout:
        raise RuntimeError("This board flow requires the validated Vivado 2018.3 toolchain")
    commands = []
    scripts = ["create_board_project.tcl"] + (["build_ila.tcl"] if args.ila else [])
    for name in scripts:
        stem = name.removesuffix(".tcl")
        command = [executable, "-mode", "batch", "-source", str(ROOT / "fpga" / name),
                   "-log", str(out / (stem + ".log")), "-journal", str(out / (stem + ".jou"))]
        commands.append(command)
        (out / "commands.json").write_text(json.dumps(commands, indent=2) + "\n", encoding="utf-8")
        print(f"BUILD_START {variant} {name}", flush=True)
        with (out / (stem + "_console.log")).open("w", encoding="utf-8") as stream:
            process = subprocess.run(command, cwd=work, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=1800)
        if process.returncode:
            raise RuntimeError(f"{name} failed: inspect {out}")
        print(f"BUILD_PASS {variant} {name}", flush=True)

if __name__ == "__main__":
    main()
