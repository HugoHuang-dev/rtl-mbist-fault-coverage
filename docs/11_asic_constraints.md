# V11 · ASIC Design Configuration & Timing Constraints

Status: configuration and constraint checks passed. Building on the verified [V10 controller boundary](10_asic_architecture.md), this version establishes Nangate45 synthesis configuration and explicit early timing assumptions. Netlist functional verification is covered in V12; formal area and critical-path evaluation is covered in V13.

## ORFS configuration

[`asic/config/config.mk`](../asic/config/config.mk) sets `DESIGN_NAME=mbist_asic_top` and `PLATFORM=nangate45`, reading seven RTL files from V10's frozen [`asic_rtl.f`](../asic/rtl/asic_rtl.f). Absolute paths are calculated from the container mount `/work/mbist`, without Windows drive letters. `VERILOG_FILES` excludes `single_port_sync_ram.v`, faulty RAM, the board top, and FPGA IP. `SDC_FILE` points to this version's [`constraint.sdc`](../asic/config/constraint.sdc).

`ABC_CLOCK_PERIOD_IN_PS=20000` is set explicitly to match the SDC's `20.0 ns`. The current ORFS Makefile extracts a clock-period value from SDC into this variable, whose unit name is ps. The explicit assignment removes ambiguity between `20` and `20000`. The acceptance log confirms Yosys/ABC used `-D 20000`.

The platform uses `NangateOpenCellLibrary_typical.lib` from ORFS commit `b74a7293ea57fc4154a08471bcf78042ed497e4e`. Liberty nominal conditions are 25 °C, 1.10 V, and process 1.00; time and capacitance units are ns and fF. The pinned image from the reproduction guide is `openroad/orfs@sha256:bc05b68ef2f023cb49d4a7f80b021d3895328c0e4ee8491ae9bdf6fc29771b9f`. Library, RTL, and configuration fingerprints are in the [frozen toolchain record](../results/asic/v11/20260927_v11_frozen/toolchain.txt) and [automated audit](../results/asic/v11/20260927_v11_frozen/audit.json).

## External interface timing assumptions

The 50 MHz / 20 ns target follows the FPGA experiment. External SRAM has not been selected. The following delays and loads are early interface budgets to be reviewed against the memory datasheet and interconnect when integrated.

| Constraint | Value | Basis and meaning |
| --- | --- | --- |
| `create_clock` | 20.0 ns | One rising-edge `clk`, targeting 50 MHz |
| Setup / hold uncertainty | 0.2 / 0.1 ns | Initial allowance for clock variation and analysis margin; the clock network is currently ideal |
| `set_input_delay -max/-min` on all non-clock inputs | 2.0 / 0.0 ns | An external source in the same clock domain provides valid signals within 2 ns after the rising edge; covers `start`, `rst_n`, `req_ready`, `rd_valid`, and `rd_data[7:0]` |
| Input transition | 0.1 ns | Initial driving-slew assumption for these 12 input bits |
| `set_output_delay -max/-min` on all outputs | 2.0 / 0.0 ns | Reserves up to 2 ns for external receiver setup and interconnect; covers 54 request, status, and diagnostic output bits |
| Output load | 4.0 fF | Nangate45 Liberty uses fF; the initial load is close to the ORFS platform's default ABC load of 3.898 fF and must be reviewed against actual integration loads |

Under the one-cycle synchronous-read protocol, the request is accepted at `E_k`, external RAM produces `rd_valid/rd_data` after that edge, and the controller samples them at `E_{k+1}`. A 2 ns maximum input delay requires the response to reach the controller interface within 2 ns of the launching edge and remain stable before the next sampling edge. This is a requirement on external memory and interconnect, not measured SRAM performance. `req_ready` is likewise modeled as a synchronous input stable before the sampling edge. Combinational ready logic or another clock domain would require analysis of the actual paths and synchronization scheme.

`rst_n` is an active-low synchronous reset in the controller RTL. It remains in the constrained input set, preserving reset-to-register paths; no `set_false_path` is applied to it. The assumption requires appropriately synchronized external reset release. An asynchronous board button is not used as the timing model for the ASIC reset pin. All outputs, including diagnostics, are constrained so status paths are not omitted by constraining only requests.

## Tool checks and results

[`run_v11.sh`](../asic/scripts/run_v11.sh) mounts the project into Docker from WSL and runs `make ... synth` with this configuration to exercise configuration and SDC parsing. ORFS builds in WSL ext4; logs, reports, the preliminary netlist, and constraint copies are then archived in the [V11 results](../results/asic/v11/README.md). GCD was not rerun, and MBIST place and route was not started.

`config_parse.log` resolves the expected seven RTL files, Nangate45, top `mbist_asic_top`, the SDC, and ABC period `20000`. Yosys completes hierarchy processing and mapping, with 0 structural problems in `synth_check.txt`. OpenROAD successfully runs `link_design` and `read_sdc`, producing `1_synth.odb` and the expanded `1_synth.sdc`. This preliminary netlist validates configuration and had not yet undergone V12 gate-level regression.

[`check_v11.tcl`](../asic/scripts/check_v11.tcl) runs `check_setup -verbose` and targeted path queries on the preliminary netlist. The log reports one clock, 13 input bits including `clk`, and 54 output bits. `check_setup` reports no missing-constraint diagnostics. Independently, [`audit_v11.py`](../asic/scripts/audit_v11.py) checks the expanded SDC: all 12 non-clock input bits have 0/2 ns min/max delays and 0.1 ns transition; all 54 output bits have 0/2 ns min/max delays and 4 fF load. There are no false-path, multicycle-path, or disable-timing exceptions. The result is `V11_AUDIT_PASS`.

OpenROAD reports constrained setup paths for `rst_n →` diagnostic registers, `req_ready →` FSM/phase registers, `rd_valid →` address registers, `rd_data →` first-failure registers, and `start →` address registers, as well as register-to-register, register-to-request-output, and register-to-status-output paths. These preliminary reports all show `slack (MET)`. Their purpose here is to confirm that paths enter the analysis; the margins are not the V13 evaluation results. See the [constraint-check log](../results/asic/v11/20260927_v11_frozen/constraint_check.log).

## Implementation issues and fixes

1. The first run used a Windows-mounted directory as `WORK_HOME`. Yosys read all seven controller files, but ORFS failed on SDC `touch -r` because of timestamp permissions on that mount. ORFS was moved to WSL ext4, with results copied back afterward. The original error is retained in `20260927_v11_prelim/synth_validation.log`.
2. The first SDC used `sizeof_collection`, unsupported by this OpenROAD/OpenSTA command set, producing `invalid command name`. It was replaced with `llength`, retaining the 12/54-bit assertions. The error is in `20260927_v11_ext4/synth_validation.log`.
3. `report_checks -unconstrained` alone was found insufficient for per-port omission checks. Acceptance instead combines expanded-SDC checks of each port's min/max delay and load, `check_setup`, and nine groups of constrained paths. The final run, `20260927_v11_frozen`, passed.

The early Yosys canonicalize stage emitted three messages about parameterized modules with processes being ignored before `proc`. Subsequent `proc`, mapping, and final structural checks completed, with 0 problems in `synth_check.txt`. A small WSL/container timestamp difference also caused one non-blocking warning that `clock_period.txt` was slightly in the future. No unresolved modules, missing ports, or errors blocking configuration validation remained. V12 records the netlist structure and functional results.

## Reproduction and acceptance

From the project root in Ubuntu WSL:

```bash
bash asic/scripts/run_v11.sh NEW_RUN_ID
```

The script defaults to ORFS at `~/OpenROAD-flow-scripts`; `ORFS_ROOT` can select another checkout of the same commit. The image digest is pinned in the script. Use a new run ID. It calls `make DESIGN_CONFIG=/work/mbist/asic/config/config.mk WORK_HOME=/work/output synth`, then runs the dedicated constraint check and automated audit. `results/asic/v11/NEW_RUN_ID/` contains toolchain fingerprints, input snapshots, ORFS logs/reports/preliminary netlist, constraint checks, and audit JSON.

Acceptance: ORFS identifies the controller and Nangate45 correctly; the 20 ns clock and interface constraints are read; synchronous reset remains timed; structure checks pass; principal path categories can be reported; and no ports are unintentionally unconstrained. V11 is complete. The numerical budgets require review once actual SRAM/SoC integration conditions are known. V12 verifies the synthesized netlist's function.
