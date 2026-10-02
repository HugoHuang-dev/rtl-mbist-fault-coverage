# Project Reproduction

Open PowerShell at the project root. Python 3.10 or later, Vivado 2018.3, and Icarus Verilog are required. Scripts locate tools and save version output before running; a missing tool produces an error.

## Tool configuration

Set `VIVADO_BIN` and `IVERILOG_BIN` to the respective bin directories in PowerShell, or add them to PATH. The same keys can be set in an unversioned `toolchain.local.json`. Precedence is environment variables → local JSON → PATH.

```powershell
$env:VIVADO_BIN = 'D:\Xilinx\Vivado\2018.3\bin'  # Example; use the actual installation path
$env:IVERILOG_BIN = 'D:\iverilog\bin'               # Example; use the actual installation path
```

## Simulation and full fault campaign

Choose a new run ID for each experiment. Rerunning with the same ID updates that run's results; do not reuse archived IDs.

```powershell
$env:MBIST_RUN_ID = 'local_check_01'
py -3 scripts/run_basic_sim.py
py -3 scripts/run_step04.py
py -3 scripts/run_step05.py
py -3 scripts/run_step06.py --mode all
$env:MBIST_AUDIT_RUN_ID = $env:MBIST_RUN_ID
py -3 scripts/audit_step06.py
py -3 scripts/evaluate_fault_coverage.py
py -3 scripts/run_step06.py --mode replay --fault-id F0123
```

Outputs are written under `results/reruns/local_check_01/step02` through `step07`, with builds under `.build/local_check_01/`. `--mode all` runs the pilot and full campaign after one compilation per simulator. Each single-case replay compiles independently and compares against the full campaign with the same ID.

Without `MBIST_AUDIT_RUN_ID`, v6/v7 audits still read the original `results/step06`. Current RTL/testbench bodies are checked against the original snapshot for consistency. New experiments record their own source snapshots.

## Board simulation and builds

```powershell
$env:MBIST_RUN_ID = 'board_check_01'
py -3 scripts/run_step08_board.py
py -3 scripts/run_board_build.py --ila
py -3 scripts/run_board_build.py --fault --ila
py -3 scripts/audit_board_revision.py
```

The run produces `base`, `ila`, `base_fault`, and `ila_fault` directories containing utilization, timing, CDC, timing-exception, and synchronizer-check reports. Keep normal and perturbed `.bit/.ltx` pairs separate. Generated Vivado projects are under `.build/board_check_01/vivado/` and `vivado_fault/`.

`audit_step08.py` checks archived initial reports; current builds use `audit_board_revision.py`. The board perturbation does not change controller source.

## Completed checks

- Software and full fault campaign: `20260926_engineering_review`.
- Final board-wrapper simulation and four implementations: `20260926_review_final`.
- Board photos and ILA for normal/perturbed, reset, and repeated-start tests: `results/step08/hardware_final/`.
- Initial normal capture archive: `results/step08/hardware/`.

Results are summarized in the [engineering review](09_engineering_review.md).

## Board evidence audit

These commands read saved reports and captures without rerunning simulation or programming the board:

```powershell
py -3 scripts/audit_final_hardware.py
$env:MBIST_RUN_ID = '20260926_review_final'
py -3 scripts/audit_board_revision.py
```

The hardware audit checks five ILA captures, 640 requests per run, read responses, diagnostics, completion, repeated starts, and agreement between captured probes and release files. The combined audit also checks 50 MHz setup/hold timing for all four implementations and dual-simulator board tests. See the [results](../results/step08/hardware_final/README.md). Build audits for other IDs inspect their corresponding offline records; existing captures do not automatically validate newly generated bitstreams.

## ASIC tool environment and entry points

v10–v13 use Python 3.10+, Vivado/XSim 2018.3, and Icarus 11.0 (devel). Synthesis and STA run through Docker in WSL2 / Ubuntu 24.04. ORFS is pinned to commit `b74a7293ea57fc4154a08471bcf78042ed497e4e`, and the Docker image must be selected through `ORFS_IMAGE`. Yosys reports `0.68+post`; OpenROAD's version string is `unknown`. Liberty is Nangate45 typical / 25 °C / 1.10 V.

In WSL, `ORFS_ROOT` defaults to `~/OpenROAD-flow-scripts` and must select a checkout of that commit. The environment uses the prebuilt image for Yosys/OpenROAD. `MBIST_ASIC_WORK_ROOT` defaults to `~/mbist-asic-work`, providing an ext4 build directory for v11/v12 to avoid timestamp permissions on Windows mounts. Run all commands below from the project root with new run IDs.

Windows PowerShell:

```powershell
# Current shared RTL and ASIC wrapper: normal/failure cases in both simulators
py -3 asic/scripts/run_v10.py --tool both --run-id rtl_check_01

# Reuse frozen v12 synthesis inputs/outputs for gate-level regression in a new directory
py -3 asic/scripts/run_v12.py --synthesis-run 20260927_v12_frozen --run-id gate_check_01 --tool both
```

Simulator caches are under `.build/asic/v10` or `v12`; reports and raw logs are under `results/asic/v10/rtl_check_01` and `results/asic/v12/gate_check_01`. `--synthesis-run` copies archived synthesis outputs and records their source without resynthesizing.

Ubuntu WSL:

```bash
export ORFS_ROOT="$HOME/OpenROAD-flow-scripts"
export ORFS_IMAGE="<local ORFS image name or ID>"
bash asic/scripts/run_v11.sh constraints_check_01
bash asic/scripts/run_v12.sh synthesis_check_01
bash asic/scripts/run_v13.sh sta_check_01
```

v11 performs configuration parsing, preliminary synthesis, and constraint checks. v12 generates a formal netlist and functional model from the current seven-file RTL set; then run `py -3 asic/scripts/run_v12.py --run-id synthesis_check_01 --tool both` from the Windows project root to complete gate-level verification. v13's default target remains the verified netlist from `20260927_v12_frozen`; reruns neither select another netlist automatically nor copy historical screenshots.

## ASIC RTL inspection

Open the [RTL project](../asic/vivado/mbist_asic_v10/mbist_asic_v10.xpr) in Vivado 2018.3 and select RTL Analysis → Open Elaborated Design. All seven sources use relative paths. Functional verification uses the independent checker; standard-cell synthesis uses ORFS.

## Current source and historical experiments

Shared RTL and testbenches retain the v9 implementation; the ASIC top and scripts are under `asic/`. Shared source from the original ASIC experiment differs from current files only in project headers and line endings. `tb_board_top.sv` retains the v9 board revision and is not used in ASIC regression. Source checks are explained in the [experiment input notes](../evidence/README.md).

Archived ProjectIII runs completed [32 dual-simulator RTL scenarios](../results/asic/v10/projectiii_integration/report.json), [16 dual-simulator frozen-netlist scenarios](../results/asic/v12/projectiii_integration/report.json), and [8 Icarus scenarios](../results/asic/v12/projectiii_synthesis/report.json) after resynthesizing current source. [SDC checks](../results/asic/v11/projectiii_integration/audit.json) and [STA rechecks](../results/asic/v13/projectiii_integration/final_audit.json) agree with the frozen conditions.

The Vivado project [elaborated successfully](../results/asic/v10/projectiii_relocation/elaboration_with_ip_directory.log) in a new directory containing spaces. Active Bash scripts use LF line endings so WSL does not interpret CRLF carriage returns as part of an option. ASIC simulation and synthesis do not produce new board captures.
