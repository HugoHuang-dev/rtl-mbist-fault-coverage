#!/usr/bin/env bash
# Reuse the V12 accepted netlist, the V11 SDC and the pinned Nangate45 library.
set -euo pipefail

run_id="${1:-$(date +%Y%m%d_%H%M%S)}"
[[ "$run_id" =~ ^[A-Za-z0-9_-]+$ ]] || { echo 'Invalid run ID' >&2; exit 2; }
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
orfs_root="${ORFS_ROOT:-$HOME/OpenROAD-flow-scripts}"
v12="$project_root/results/asic/v12/20260927_v12_frozen"
out="$project_root/results/asic/v13/$run_id"
image="${ORFS_IMAGE:?Set ORFS_IMAGE to the installed ORFS toolchain image}"
liberty="$orfs_root/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib"

test "$(git -C "$orfs_root" rev-parse HEAD)" = b74a7293ea57fc4154a08471bcf78042ed497e4e
test ! -e "$out"
test -f "$liberty"
test -f "$v12/report.json"
mkdir -p "$out/input_snapshot" "$out/sta"
cp "$v12/orfs/results/nangate45/mbist_asic_top/base/1_2_yosys.v" "$out/input_snapshot/"
cp "$v12/orfs/reports/nangate45/mbist_asic_top/base/synth_stat.txt" "$out/input_snapshot/"
cp "$v12/orfs/reports/nangate45/mbist_asic_top/base/synth_check.txt" "$out/input_snapshot/"
cp "$project_root/asic/config/constraint.sdc" "$out/input_snapshot/"
cp "$liberty" "$out/input_snapshot/"
cp "$orfs_root/flow/platforms/nangate45/lef/NangateOpenCellLibrary.macro.mod.lef" "$out/input_snapshot/"
cp "$v12/report.json" "$v12/structure.json" "$v12/toolchain.txt" "$out/input_snapshot/"
cp "$project_root/asic/scripts/report_v13.tcl" "$project_root/asic/scripts/run_v13.sh" \
   "$project_root/asic/scripts/audit_v13.py" "$out/input_snapshot/"


docker run --rm -u "$(id -u):$(id -g)" \
  -v "$orfs_root/flow:/OpenROAD-flow-scripts/flow:ro" \
  -v "$out/input_snapshot:/work/input:ro" \
  -v "$out/sta:/work/output" \
  -v "$project_root/asic/scripts/report_v13.tcl:/work/report_v13.tcl:ro" \
  -e V13_INPUT=/work/input -e V13_OUTPUT=/work/output \
  -w /OpenROAD-flow-scripts "$image" bash -lc '
    set -euo pipefail
    source ./env.sh
    openroad -version
    openroad -exit /work/report_v13.tcl
  ' 2>&1 | tee "$out/sta.log"

python3 "$project_root/asic/scripts/audit_v13.py" prepare "$out"
printf 'V13 reports prepared for user readings: %s\n' "$out"
