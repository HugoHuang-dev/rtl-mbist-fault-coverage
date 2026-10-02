# V12 · Standard-Cell Synthesis & Netlist Verification

Status: passed. The Nangate45 configuration and 20 ns SDC from V11 are unchanged. This version synthesizes the seven controller RTL files in a separate work directory, freezes the standard-cell netlist, and runs gate-level functional regression with the existing independent checker. SRAM remains part of the simulation environment outside the ASIC top and is excluded from synthesis. V12 verifies behavior using zero-delay standard-cell functional models; synthesis-stage area and STA are covered in v13.

## Frozen inputs and outputs

[`asic/scripts/run_v12.sh`](../asic/scripts/run_v12.sh) uses ORFS commit `b74a7293ea57fc4154a08471bcf78042ed497e4e` and the Docker image selected by required `ORFS_IMAGE`, running `make DESIGN_CONFIG=/work/mbist/asic/config/config.mk WORK_HOME=/work/output synth`. The synthesis top is the controller-only `mbist_asic_top`. The typical Liberty file is `NangateOpenCellLibrary_typical.lib`, at 25 °C / 1.10 V / process 1.00. Commands are in the [toolchain record](../results/asic/v12/20260927_v12_frozen/toolchain.txt).

The formal netlist is [`1_2_yosys.v`](../results/asic/v12/20260927_v12_frozen/orfs/results/nangate45/mbist_asic_top/base/1_2_yosys.v). The archive also retains original ORFS logs, reports, synthesis ODB, and configuration/script snapshots. Writable `WORK_HOME` is on WSL ext4 to avoid the Windows-mount timestamp problem identified in V11. Tools are Yosys `0.68+post`, OpenROAD reporting `unknown`, and Windows simulators Icarus Verilog `11.0 (devel)` and Vivado XSim `2018.3`.

## Netlist structure and warnings

The final Yosys [`synth_check.txt`](../results/asic/v12/20260927_v12_frozen/orfs/reports/nangate45/mbist_asic_top/base/synth_check.txt) reports 0 problems. The mapped top contains 264 standard cells, including 42 `DFF_X1` instances. Final statistics contain no memory or process objects; the netlist contains no latches, Yosys internal `$` cells, or unmapped modules. All 36 mapped cell types have definitions in the functional model generated from the same library. See [`structure.json`](../results/asic/v12/20260927_v12_frozen/structure.json). Transaction and first-failure regressions below check whether synthesis preserved the FSM, address/data generation, response checks, and diagnostics; cell counts alone do not establish equivalence.

[`synthesis.log`](../results/asic/v12/20260927_v12_frozen/synthesis.log) contains three canonicalize-stage messages about parameterized modules that `contains processes (run 'proc' command first)`, as in V11. Subsequent `proc`, register mapping, ABC standard-cell mapping, and final `check` complete; these messages do not indicate unresolved modules in the final netlist. No other synthesis errors or latch warnings remained unresolved. Cell-model generation with `read_liberty -ignore_miss_func` emitted no warnings. Structural review confirms a model for every instantiated cell, and compilation/regression confirms that the instances elaborate.

## Gate-level functional model and verification method

The fixed input supplied by the ORFS platform is Nangate45 Liberty rather than a separate simulation Verilog library. To keep model provenance consistent, V12 uses the same image and synthesis Liberty to run `yosys -Q -T -p "read_liberty -ignore_miss_func .../NangateOpenCellLibrary_typical.lib; write_verilog -noattr /work/output/nangate45_functional.v"`, archived as [`cell_model.v`](../results/asic/v12/20260927_v12_frozen/cell_model.v). This provides combinational and flip-flop behavior without SDF propagation delays. The results are zero-delay gate-level functional verification, not timing simulation, formal equivalence, or physical sign-off.

[`run_v12.py`](../asic/scripts/run_v12.py) compiles only the formal standard-cell netlist and functional model as the DUT. The test environment reuses the unchanged `march_transaction_checker.sv`, frozen 640-entry March C− CSV, synchronous RAM, faulty RAM, and independent reference monitor. The checker observes transactions, responses, DONE/PASS/FAIL, error count, and first-failure diagnostics through external ASIC ports without reading DUT state. The sequence testbench first runs 640 fault-free requests, then applies one controlled bit flip to the read response for request index 206 in the second run (zero-based, M2/address 7). It requires another complete 640-request run ending in FAIL with one error. The fault testbench covers fault-free mode, representative SA0, SA1, Rising TF, and Falling TF cases, plus address 63/bit 7 and address 0/bit 0 boundaries. The RAM reference monitor checks activation and data; the checker validates completion and diagnostics. Each gate-level result is also compared field by field with V10's frozen ASIC RTL result from the same simulator, including request/cycle/error counts and first-failure phase/address/expected/actual values.

Active-low `rst_n` retains synchronous-reset semantics. The testbench starts with reset low and releases it after three falling clock edges. Netlist flip-flops enter known states after effective reset edges; the checker's core rules are unchanged. The first XSim 2018.3 elaboration failed because the netlist lacked a `timescale` declaration while the testbench and other modules had one. The runner adds only `` `timescale 1ns/1ps `` to simulation copies of the netlist and cell model in XSim's separate build directory. The formal netlist and cell logic remain unchanged; Icarus uses the originals directly. Both tools passed after this compatibility fix, which changes neither Boolean/register behavior nor propagation delays.

## Regression results and acceptance

The final [`report.json`](../results/asic/v12/20260927_v12_frozen/report.json) is PASS for 16/16 scenarios: one two-run sequence scenario and seven fault scenarios in each simulator. Both sequence runs complete 640 requests and 960 checker-counted cycles, with 0 and 1 errors respectively. The first returns DONE/PASS; the second returns DONE/FAIL and retains diagnostics. All seven fault scenarios also complete 640 requests. Fault-free mode has zero errors; the four directed faults and two boundary cases are detected. First-failure phase, address, expected/actual bytes, activation, and error count match V10. For example, SA0 at address 7/bit 2 first fails in M2 at address 7, `FF`→`FB`, with two total errors; Falling TF at address 0/bit 0 first fails in M3, `00`→`01`, also with two errors. Results agree across both tools.

Compile, XSim elaboration, and per-scenario raw logs are in the [V12 evidence directory](../results/asic/v12/README.md). The independent checker accepts the netlist, confirming all 640 frozen transactions, continued execution after failure, and first-failure diagnostics. V12 does not repeat the 2,048-instance campaign, optimize area, run SDF timing simulation, or prove RTL/netlist equivalence over all possible inputs.

## Reproduction

Synthesize in Ubuntu WSL using a new, unused run ID:

```bash
bash asic/scripts/run_v12.sh NEW_RUN_ID
```

ORFS defaults to `~/OpenROAD-flow-scripts`. Then, from the project root in Windows PowerShell:

```powershell
py -3 asic/scripts/run_v12.py --run-id NEW_RUN_ID --tool both
```

`--tool icarus` or `--tool xsim` can run separately under different new run IDs; acceptance uses `both`. Review `synthesis.log`, `cell_model_generation.log`, `orfs/reports/.../synth_check.txt`, `structure.json`, per-scenario logs, `report.json` under `results/asic/v12/NEW_RUN_ID/`. Conclusions apply to the frozen inputs, Nangate45 typical library, and functional models described here. External SRAM timing remains subject to V11 interface assumptions and must be reviewed during integration.
