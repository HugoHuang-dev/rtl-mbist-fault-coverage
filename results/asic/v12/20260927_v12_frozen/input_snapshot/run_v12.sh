#!/usr/bin/env bash
# Formal V12 synthesis. Run in Ubuntu WSL from any directory.
set -euo pipefail

run_id="${1:-$(date +%Y%m%d_%H%M%S)}"
[[ "$run_id" =~ ^[A-Za-z0-9_-]+$ ]] || { echo 'Invalid run ID' >&2; exit 2; }
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
orfs_root="${ORFS_ROOT:-$HOME/OpenROAD-flow-scripts}"
work_host="$HOME/mbist-asic-work/v12/$run_id"
out="$project_root/results/asic/v12/$run_id"
image='openroad/orfs@sha256:bc05b68ef2f023cb49d4a7f80b021d3895328c0e4ee8491ae9bdf6fc29771b9f'
liberty="$orfs_root/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib"
test -f "$orfs_root/flow/Makefile"
test -f "$liberty"
test "$(git -C "$orfs_root" rev-parse HEAD)" = b74a7293ea57fc4154a08471bcf78042ed497e4e
test ! -e "$out"
test ! -e "$work_host"
mkdir -p "$out" "$work_host"

docker run --rm -u "$(id -u):$(id -g)" \
  -v "$orfs_root/flow:/OpenROAD-flow-scripts/flow" \
  -v "$project_root:/work/mbist:ro" \
  -v "$work_host:/work/output" \
  -w /OpenROAD-flow-scripts "$image" bash -lc '
    set -euo pipefail
    source ./env.sh
    yosys -V
    openroad -version
    cd flow
    make DESIGN_CONFIG=/work/mbist/asic/config/config.mk WORK_HOME=/work/output synth
  ' 2>&1 | tee "$out/synthesis.log"

# Use the exact Liberty used by ORFS to produce zero-delay functional modules
# for the mapped standard cells. This is functional simulation, not SDF STA.
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$orfs_root/flow:/OpenROAD-flow-scripts/flow" \
  -v "$work_host:/work/output" \
  -w /OpenROAD-flow-scripts "$image" bash -lc '
    set -euo pipefail
    source ./env.sh
    yosys -Q -T -p "read_liberty -ignore_miss_func /OpenROAD-flow-scripts/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib; write_verilog -noattr /work/output/nangate45_functional.v"
  ' 2>&1 | tee "$out/cell_model_generation.log"

mkdir "$out/orfs" "$out/input_snapshot"
cp -r "$work_host/results" "$work_host/logs" "$work_host/reports" "$out/orfs/"
cp "$work_host/nangate45_functional.v" "$out/cell_model.v"
cp "$project_root/asic/config/config.mk" "$project_root/asic/config/constraint.sdc" \
   "$project_root/asic/rtl/asic_rtl.f" "$out/input_snapshot/"
cp "$project_root/asic/scripts/run_v12.sh" "$project_root/asic/scripts/run_v12.py" \
   "$project_root/asic/scripts/run_v10.py" "$out/input_snapshot/"
{
  printf 'ORFS_COMMIT %s\n' "$(git -C "$orfs_root" rev-parse HEAD)"
  printf 'ORFS_IMAGE %s\n' "$image"
  printf 'SYNTH_COMMAND make DESIGN_CONFIG=/work/mbist/asic/config/config.mk WORK_HOME=/work/output synth\n'
  printf 'MODEL_COMMAND yosys -Q -T -p "read_liberty -ignore_miss_func /OpenROAD-flow-scripts/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib; write_verilog -noattr /work/output/nangate45_functional.v"\n'
  sha256sum "$liberty" "$project_root/asic/config/config.mk" "$project_root/asic/config/constraint.sdc"
  while IFS= read -r relative; do
    [[ -z "$relative" || "$relative" == \#* ]] && continue
    sha256sum "$project_root/$relative"
  done < "$project_root/asic/rtl/asic_rtl.f"
  sha256sum "$out/orfs/results/nangate45/mbist_asic_top/base/1_2_yosys.v" "$out/cell_model.v"
} > "$out/toolchain.txt"
printf 'V12 synthesis archived: %s\n' "$out"
printf 'Next: py -3 asic/scripts/run_v12.py --run-id %s\n' "$run_id"
