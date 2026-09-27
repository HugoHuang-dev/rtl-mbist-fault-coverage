"""Local build directories and tool discovery for reproducible reruns."""
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = os.environ.get("MBIST_RUN_ID", datetime.now().strftime("%Y%m%d_%H%M%S"))
if not RUN_ID or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in RUN_ID):
    raise ValueError("MBIST_RUN_ID must contain only letters, digits, underscores and hyphens")
RESULT_ROOT = ROOT / "results" / "reruns" / RUN_ID
BUILD_ROOT = ROOT / ".build" / RUN_ID
config_path = ROOT / "toolchain.local.json"
LOCAL = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}

def result_dir(stage):
    return RESULT_ROOT / stage

def build_dir(stage):
    return BUILD_ROOT / stage

def tool(name):
    family = "IVERILOG_BIN" if name in {"iverilog", "vvp"} else "VIVADO_BIN"
    directory = os.environ.get(family) or LOCAL.get(family)
    suffix = ".exe" if family == "IVERILOG_BIN" else ".bat"
    found = str(Path(directory) / (name + suffix)) if directory else shutil.which(name + suffix)
    if not found or not Path(found).is_file():
        raise FileNotFoundError(f"Cannot find {name}; set {family}, toolchain.local.json, or PATH")
    return found

def record_environment(output, engines=("icarus", "xsim")):
    output.mkdir(parents=True, exist_ok=True)
    data = {"run_id": RUN_ID, "project": str(ROOT), "tools": {}}
    names = (["iverilog", "vvp"] if "icarus" in engines else []) + (["xvlog", "xelab", "xsim"] if "xsim" in engines else [])
    for name in names:
        executable = tool(name)
        version = subprocess.run([executable, "-V" if name in {"iverilog", "vvp"} else "-version"],
                                 cwd=output, capture_output=True, text=True, errors="replace", timeout=30)
        data["tools"][name] = {"executable": executable, "version_exit": version.returncode,
                               "version_output": version.stdout + version.stderr}
    (output / "environment.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def audit_dir(stage):
    run = os.environ.get("MBIST_AUDIT_RUN_ID")
    if run and any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in run):
        raise ValueError("Invalid MBIST_AUDIT_RUN_ID")
    return ROOT / "results" / "reruns" / run / stage if run else ROOT / "results" / stage
