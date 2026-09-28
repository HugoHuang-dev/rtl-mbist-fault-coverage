# Repository Contents

This repository contains the shared March C− controller, verification environment, FPGA implementation and board records, and the Nangate45 synthesis experiments described in the [project README](README.md).

| Directory or entry | Contents |
| --- | --- |
| [rtl/](rtl/) | Shared controller, address/data generators, response checker, and synchronous RAM |
| [tb/](tb/) · [specs/](specs/) | Testbenches, independent checkers, fault models, and the frozen 640-request reference sequence |
| [scripts/](scripts/) · [sim/](sim/) | Simulation runners, fault campaign, coverage evaluation, and hardware-data checks |
| [fpga/](fpga/) | Board wrapper, pin/timing constraints, and Vivado creation/build scripts |
| [asic/](asic/) | Controller-only top level, seven-file RTL list, ORFS configuration, SDC, gate-level simulation, and STA scripts |
| [docs/](docs/) | v1–v13 reports, [development log](docs/DEVLOG.md), and [reproduction guide](docs/reproduce.md) |
| [v6 campaign](results/step06/README.md) · [v7 coverage](results/step07/README.md) | The 2,048 target faults, both simulators' raw results, coverage, and detection phases |
| [FPGA implementation](results/reruns/20260926_review_final/README.md) | Utilization, timing, CDC, and board-wrapper simulation |
| [Board evidence](results/step08/hardware_final/README.md) | Photos, screenshots, five native ILA captures, and transaction checks |
| [v10 architecture](results/asic/v10/README.md) · [v11 constraints](results/asic/v11/README.md) | RTL regression, Vivado structure views, synthesis configuration, and constraint checks |
| [v12 netlist](results/asic/v12/README.md) · [v13 evaluation](results/asic/v13/README.md) | Verified standard-cell netlist, functional models, synthesis logs, Liberty/LEF inputs, area, and timing reports |
| [releases/](releases/README.md) | Normal and perturbed BIT/LTX files, with and without ILA |
| [evidence/](evidence/README.md) | Current source checksums and the two source archives required by historical experiment checks |

The shared controller entry is `rtl/mbist_top.v`. The default board build uses `fpga/board_top.v` with `INJECT_READ_FAULT=0`. The ASIC entry is `asic/rtl/mbist_asic_top.v`; `asic/rtl/asic_rtl.f` defines its synthesis boundary. SRAM is external to that boundary.

Board Vivado projects are generated locally under `.build/<run-id>/`. The maintained [ASIC RTL-view project](asic/vivado/mbist_asic_v10/mbist_asic_v10.xpr) is included with relative source paths. It opens the controller hierarchy in Vivado; Nangate45 synthesis uses ORFS.

Build caches, checkpoints, simulator executables, session journals, and `toolchain.local.json` are excluded. Original experiment logs, reports, netlists, source snapshots, and native hardware captures are retained. The portable ILA directory includes its WDB/WCFG pair. Git preserves their bytes on checkout; maintained ASIC shell scripts use LF endings.

Git records project revisions. The [current source manifest](evidence/current_source_sha256.txt) covers maintained RTL, constraints, and scripts; experiment-specific manifests identify their original inputs and evidence.

Copy [toolchain.example.json](toolchain.example.json) to `toolchain.local.json` and adjust installation paths, or set environment variables. The [reproduction guide](docs/reproduce.md) gives commands for simulation, synthesis, and STA with new run IDs. Programming and capture instructions are in the [board procedure](docs/08_board_bringup_steps.md).
