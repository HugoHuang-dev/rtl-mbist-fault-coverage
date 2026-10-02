#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : run_v11.sh
# Module  : run_v11
# -----------------------------------------------------------------------------
# Run from WSL Ubuntu. This mounts the local MBIST project beside the frozen
# ORFS flow and keeps all new output under results/asic/v11/<run-id>/.
set -euo pipefail

run_id="${1:-$(date +%Y%m%d_%H%M%S)}"
if [[ ! "$run_id" =~ ^[A-Za-z0-9_-]+$ ]]; then
  printf 'Invalid run ID: %s\n' "$run_id" >&2
  exit 2
fi

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
orfs_root="${ORFS_ROOT:-$HOME/OpenROAD-flow-scripts}"
work_host="${MBIST_ASIC_WORK_ROOT:-$HOME/mbist-asic-work}/v11/$run_id"
image="${ORFS_IMAGE:?Set ORFS_IMAGE to the installed ORFS toolchain image}"
test -f "$orfs_root/flow/Makefile"
test "$(git -C "$orfs_root" rev-parse HEAD)" = b74a7293ea57fc4154a08471bcf78042ed497e4e
test -f "$project_root/asic/config/config.mk"
out="$project_root/results/asic/v11/$run_id"
mkdir -p "$(dirname "$out")"
mkdir "$out"
test ! -e "$work_host"
mkdir -p "$work_host"

docker run --rm -u "$(id -u):$(id -g)" \
  -v "$orfs_root/flow:/OpenROAD-flow-scripts/flow" \
  -v "$project_root:/work/mbist:ro" \
  -v "$work_host:/work/output" \
  -w /OpenROAD-flow-scripts "$image" bash -lc '
    set -euo pipefail
    source ./env.sh
    cd flow
    config=/work/mbist/asic/config/config.mk
    work=/work/output
    for var in DESIGN_NAME PLATFORM VERILOG_FILES SDC_FILE ABC_CLOCK_PERIOD_IN_PS; do
      make DESIGN_CONFIG="$config" WORK_HOME="$work" "print-$var"
    done
  ' 2>&1 | tee "$out/config_parse.log"

docker run --rm -u "$(id -u):$(id -g)" \
  -v "$orfs_root/flow:/OpenROAD-flow-scripts/flow" \
  -v "$project_root:/work/mbist:ro" \
  -v "$work_host:/work/output" \
  -w /OpenROAD-flow-scripts "$image" bash -lc '
    set -euo pipefail
    source ./env.sh
    cd flow
    make DESIGN_CONFIG=/work/mbist/asic/config/config.mk \
      WORK_HOME=/work/output synth
  ' 2>&1 | tee "$out/synth_validation.log"

docker run --rm -u "$(id -u):$(id -g)" \
  -v "$orfs_root/flow:/OpenROAD-flow-scripts/flow" \
  -v "$project_root:/work/mbist:ro" \
  -v "$work_host:/work/output" \
  -e V11_WORK=/work/output \
  -w /OpenROAD-flow-scripts "$image" bash -lc '
    set -euo pipefail
    source ./env.sh
    openroad -exit /work/mbist/asic/scripts/check_v11.tcl
  ' 2>&1 | tee "$out/constraint_check.log"

mkdir "$out/orfs"
cp -r "$work_host/results" "$work_host/logs" "$work_host/reports" "$out/orfs/"
mkdir "$out/input_snapshot"
cp "$project_root/asic/config/config.mk" "$project_root/asic/config/constraint.sdc" \
   "$project_root/asic/rtl/asic_rtl.f" "$out/input_snapshot/"
cp "$project_root/asic/scripts/run_v11.sh" "$project_root/asic/scripts/check_v11.tcl" \
   "$project_root/asic/scripts/audit_v11.py" "$out/input_snapshot/"
{
  printf 'ORFS_COMMIT %s\n' "$(git -C "$orfs_root" rev-parse HEAD)"
  printf 'ORFS_IMAGE %s\n' "$image"
} > "$out/toolchain.txt"
python3 "$project_root/asic/scripts/audit_v11.py" "$out"
printf 'V11 preliminary synthesis and SDC parse complete: %s\n' "$out"
