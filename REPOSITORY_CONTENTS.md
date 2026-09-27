# Repository Contents

This repository contains the March C− RTL, independent verification environment, fault campaign, FPGA build scripts, measured reports, and board evidence described in the [project README](README.md).

| Directory | Contents |
| --- | --- |
| [rtl/](rtl/README.md) | RAM, controller, address/data generators, and response checker |
| [tb/](tb/README.md) · [specs/](specs/README.md) | Testbenches, fault models, independent checkers, and frozen request sequence |
| [scripts/](scripts/README.md) · [sim/](sim/README.md) | Simulation runners, campaign automation, and evidence audits |
| [fpga/](fpga/README.md) | Board wrapper, pin/timing constraints, and Vivado project/build Tcl |
| [docs/](docs/README.md) | Version history, design notes, reproduction guide, and board procedure |
| [results/step06/](results/step06/README.md) · [results/step07/](results/step07/README.md) | All 2,048 target faults, both simulators' raw logs, coverage, and detection phases |
| [Final implementation](results/reruns/20260926_review_final/README.md) | Utilization, timing, CDC, and board-wrapper simulation |
| [Final board evidence](results/step08/hardware_final/README.md) | Photos, screenshots, five native ILA captures, and per-transaction audits |
| [releases/](releases/README.md) | Normal and perturbed BIT/LTX files, with and without ILA |
| [evidence/](evidence/README.md) | Source snapshots, historical hashes, and review records |

Vivado projects and working directories are generated locally. Build caches, checkpoints, simulator intermediates, session journals, and the machine-specific toolchain configuration are excluded. Original experiment logs, source snapshots, reports, and native hardware captures are retained. The portable ILA directory also includes its WDB/WCFG files for reopening.

Historical manifests describe their original experiment or archive. The repository-wide [SHA256SUMS.txt](SHA256SUMS.txt) checks the files supplied here. Git attributes disable line-ending conversion so that source and raw-log hashes remain stable after cloning.

Copy [toolchain.example.json](toolchain.example.json) to `toolchain.local.json` and adjust installation paths, or configure the environment variables described in [reproduce.md](docs/reproduce.md). New simulation and build outputs use project-local directories.

Run the archived-data checks without a connected board or simulator:

```powershell
py -3 scripts/audit_step06.py
py -3 scripts/evaluate_fault_coverage.py
py -3 scripts/audit_final_hardware.py --self-test
$env:MBIST_RUN_ID = '20260926_review_final'
py -3 scripts/audit_board_revision.py
```

Fresh simulation and implementation commands are in the [reproduction guide](docs/reproduce.md); programming and measurement steps are in the [board procedure](docs/08_board_bringup_steps.md).
