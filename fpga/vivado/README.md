# Vivado Board Project

Vivado 2018.3 generates the board projects from the maintained RTL, XDC, and build Tcl. From the repository root in PowerShell, after configuring the tools:

```powershell
$env:MBIST_RUN_ID = 'board_check_01'
py -3 scripts/run_board_build.py --ila
py -3 scripts/run_board_build.py --fault --ila
```

Open the normal project under `.build/board_check_01/vivado/` or the perturbed project under `.build/board_check_01/vivado_fault/`. New reports and bitstreams are saved under `results/reruns/board_check_01/step08/`. Generated project state, caches, and checkpoints are excluded from Git.

The [tested bitstreams and probes](../../releases/20260926_review/README.md) can be used without rebuilding. The [implementation report](../../docs/08_fpga_implementation.md) and [board evidence](../../results/step08/hardware_final/README.md) describe their results. The original v8 implementation records remain under [results/step08](../../results/step08/README.md).

The separate [ASIC RTL-view project](../../asic/vivado/mbist_asic_v10/mbist_asic_v10.xpr) is included for inspecting the controller hierarchy. Full tool setup and run commands are in the [reproduction guide](../../docs/reproduce.md).
