# Reproducing the Project

Open PowerShell at the project root. Requirements: Python 3.10 or later, Vivado 2018.3, and Icarus Verilog. Scripts locate tools and save their version output; missing tools cause an explicit error.

## Tool configuration

Set `VIVADO_BIN` and `IVERILOG_BIN` to their respective bin directories, or add those directories to PATH. A local `toolchain.local.json` may specify the two directories for this machine. Lookup order is environment variables → local JSON → PATH.

```powershell
$env:VIVADO_BIN = 'D:\Xilinx\Vivado\2018.3\bin'  # Example: use your installed path
$env:IVERILOG_BIN = 'D:\iverilog\bin'               # Example: use your installed path
```

## Simulation and full campaign

Choose a new run ID. Reusing an ID updates that run's results; do not reuse an archived ID.

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

Outputs go to `results/reruns/local_check_01/step02` through `step07`; builds go to `.build/local_check_01/`. With `--mode all`, the pilot and full campaign each reuse one compilation per tool. Single-case replay recompiles independently and compares its result with the full campaign for that run.

Without `MBIST_AUDIT_RUN_ID`, v6/v7 audit reads the archived `results/step06`. Archived source fingerprints refer to the original snapshot; current RTL/testbench text is checked separately. A new run records its own source snapshot and byte-exact hashes.

## Board-wrapper simulation and FPGA builds

```powershell
$env:MBIST_RUN_ID = 'board_check_01'
py -3 scripts/run_step08_board.py
py -3 scripts/run_board_build.py --ila
py -3 scripts/run_board_build.py --fault --ila
py -3 scripts/audit_board_revision.py
```

This produces `base`, `ila`, `base_fault`, and `ila_fault` directories with utilization, timing, CDC, timing-exception, and synchronizer reports. Normal and perturbed `.bit/.ltx` files must stay paired. Vivado projects are under `.build/board_check_01/vivado/` and `vivado_fault/`.

`audit_step08.py` checks the archived initial reports; `audit_board_revision.py` checks the current build. Board perturbation does not change controller RTL.

## Archived review runs

- Software and full fault campaign: `20260926_engineering_review`.
- Final board-wrapper simulation and four implementations: `20260926_review_final`.
- Board photos and ILA for normal/perturbed runs, reset, and restart: `results/step08/hardware_final/`.
- Initial normal capture: `results/step08/hardware/`.

See the [engineering review](09_engineering_review.md) for results.

## Audit the final hardware evidence

These commands read saved reports and captures. They do not rerun simulation or reprogram the board:

```powershell
py -3 scripts/audit_final_hardware.py
$env:MBIST_RUN_ID = '20260926_review_final'
py -3 scripts/audit_board_revision.py
```

The hardware audit checks five ILA runs, 640 requests, read responses, diagnostics, completion, restart clearing, probes, and release-file consistency. The combined audit also checks 50 MHz setup/hold timing across four implementations and dual-tool board-wrapper simulation. See the [results](../results/step08/hardware_final/README.md). Auditing a different run ID checks that run's offline data; existing captures are not automatically associated with newly generated bitstreams.
