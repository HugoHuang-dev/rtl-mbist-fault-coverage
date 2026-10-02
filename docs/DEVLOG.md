# Development Log

The entries below record v1–v13 work and acceptance. Board photos and ILA data for v9 were captured on 2026-09-26. Original outputs are under each version's evidence directory.

| Period | Work |
| --- | --- |
| 09.02–09.03 | v1 Memory specification and March C− reference sequence |
| 09.04–09.06 | v2 Single-port synchronous RAM, independent tests, and tool selection |
| 09.07–09.10 | v3 March C− controller RTL |
| 09.11–09.13 | v4 Independent checker and negative regression |
| 09.14–09.17 | v5 Faulty memory and directed validation |
| 09.18–09.21 | v6 Full fault-injection campaign |
| 09.22–09.23 | v7 Independent fault-coverage evaluation |
| 09.24–09.25 | v8 Vivado implementation, bitstreams, and ILA configuration |
| 09.26 | v9 Board capture, audit, and project documentation |
| 09.27 experiment records | v10–v13 ASIC architecture, configuration, gate-level verification, and synthesis evaluation |

## v1 · 09.02–09.03 — Memory specification and March C−

March C− ordering and synchronous-read control follow R1; module organization follows R2. Board constraints are based on the Da Vinci V2.1 schematic and official pin list.

Completed:

1. Fixed the first MUT at 64×8, six-bit address, 50 MHz, single-port synchronous read. The original `DaVinci_FPGA_IO.xdc` has `create_clock -period 20.000` and locates `sys_clk` at R4.
2. Defined the shared request/read-response interface, accepting edge, next-edge response consumption, read-valid flag, absence of write response, and read-before-write order.
3. Specified M0–M5, address directions, expected data, and phase boundaries; generated the full 640-request CSV.
4. Defined first-error latching, error count, continued testing, and DONE/PASS, distinguishing request count from clock cycles.
5. Established the system structure and v1–v9 version index.

Validation: `scripts/generate_march_reference.py` exited 0 and printed `Wrote 640 requests`. An independent shadow RAM verified expected reads; phase lengths were 64/128/128/128/128/64 with 320 reads and 320 writes. PowerShell `Import-Csv` independently checked boundaries: M0 `0/write/0 → 63/write/63`; M1 `0/read/64 → 63/write/191`; M2 `0/read/192 → 63/write/319`; M3 `63/read/320 → 0/write/447`; M4 `63/read/448 → 0/write/575`; M5 `0/read/576 → 63/read/639`.

The RAM timing and request CSV were fixed here. RAM mapping, fault behavior, and board observations were measured in their later versions.

## v2 · 09.04–09.05 — Single-port RAM and stand-alone tests

Basis: the frozen v1 64×8 interface and one-cycle read-response contract, with reference to R1 `march_c-/sim_models/memory_model.v` and AMD UG473/XPM documentation.

Completed `rtl/single_port_sync_ram.v` with synchronous reads/writes, no fault or initial contents, no array reset, and request readiness during normal operation. Writes have no read response. Added `tb/tb_single_port_sync_ram.sv` with an independent shadow RAM. Tests cover addresses 0/63, 64-address sequential access, alternating operations at one address, idle output retention, reset suppression of requests, and data retention. Added a Vivado RAM-only synthesis check.

Initial tests: Icarus `-g2012` and XSim 2018.3 both printed `RAM_TB_PASS checks=146 reads=70 writes=68`. Vivado 2018.3 RAM-only synthesis for `xc7a35tfgg484-2` inferred one RAMB18E1 with `DOA_REG=0` and `WRITE_MODE_A=NO_CHANGE`.

During implementation, the testbench's planned read count was corrected upward by one to 70. XSim required consistent module timescales; `` `timescale 1ns/1ps`` was added to the RAM RTL. Both tools were rerun after the fixes. v3 and v4 reuse this request/response interface.

## v2 · 09.06 — RAM acceptance and simulation environment

XSim became the primary simulator and Icarus the independent cross-check. The original RAM implementation was retained. An assertion at the next rising edge, before NBA updates, was added to check the previous read response. Existing checks one nanosecond after the accepting edge and after a falling-edge address change cover the other two observation points. Together they establish acceptance at `E_k`, output after that edge, and synchronous consumption at `E_{k+1}`.

XSim 2018.3 and Icarus Verilog 11.0 recompiled the same source in separate build directories. Both exited 0 with `RAM_TB_PASS checks=146 reads=70 writes=68`. Logs show `CASE_PASS` for boundary/sparse access, sequential 64-address writes/reads, alternating access and idle retention, and reset write suppression with data retention. Original compile/run logs and commands are in `results/step02/`.

The board is marked `XC7A35TFGG484-2I`. Vivado selected `xc7a35tfgg484-2` for device/package/speed and `set_operating_conditions -grade Industrial` for temperature grade; the report says `Device Grade = industrial`. RAM-only synthesis found `RAMB18E1 × 1`, `DOA_REG=0`, `WRITE_MODE_A=NO_CHANGE`, and 0 errors, critical warnings, or warnings. This agrees with post-edge read output and held output on writes. [v2 acceptance](02_ram_verification.md) records the details.

## v2 · 09.06 — Tool version

Vivado 2018.3 was fixed as the project version, with XSim 2018.3 primary and Icarus for cross-checks. RAM synthesis and the stand-alone testbench had already passed on this toolchain; subsequent complete-system builds use it.

## v3 · 09.07–09.10 — March C− controller RTL

Inputs: v1's interface and 640-request M0–M5 sequence, continued execution after failure, and v2's one-cycle RAM. R1's FSM, address/data generators, comparator, and top-level modules informed the split. Its early-exit error path was not used.

Added `march_controller.v`, `address_generator.v`, `data_generator.v`, `memory_interface.v`, `response_checker.v`, and `mbist_top.v`. The controller waits for `req_ready`, compares reads only at `rd_valid`, completes read-then-write at one address, latches the first error, counts mismatches, and continues through the final M5 comparison. Results hold after DONE and a new run can start.

`tb/tb_mbist_top.sv` checked phase, address, operation, and write data against the v2 RAM. `scripts/check_step03_trace.py` compared every one of the 640 requests from each XSim/Icarus trace with the v1 CSV. `sim/run_step03.ps1` ran both tools in separate build directories; logs contain `MBIST_TB_PASS` and `TRACE_CHECK_PASS`. The fault-free run made 640 requests (320 reads, 320 writes) in 961 cycles, returned PASS, and recorded zero errors. Flipping one M2/address 7 read bit produced FAIL, expected FF/actual FE, one error, and still 640 requests. Start while busy was ignored; DONE held results and allowed a later restart. See `results/step03/README.md`.

Windows PowerShell 5.1 redirected one log as UTF-16LE. The trace-check script was changed to detect its BOM so saved logs can be audited directly. The response perturbation checks diagnostics; it is not part of fault-coverage statistics.

## v4 · 09.11–09.13 — Independent checker and negative regression

Added `tb/march_transaction_checker.sv`, which reads `oracle.hex` generated from the frozen v1 CSV and observes only external requests, responses, and result ports. It does not inspect controller FSM or address registers. Checks include read-response consumption, first-error diagnostics, DONE timing, and transaction order/data. A start while busy leaves checker state intact; a post-DONE start begins a new run.

`scripts/run_step04.py` made six separate single-change RTL variants in temporary storage: reversed address direction, M1 read changed to write, M1 write-one changed to zero, premature read comparison, DONE after M4, and shifted first-error address. Production RTL was untouched. Both XSim and Icarus detected each variant in checker categories 1–6; normal baselines completed a fault-free and a one-time perturbed-response run.

Fourteen cases ran: two baselines accepted and 12 variants rejected as intended. `results/step04/report.csv`, JSON, source, `oracle.hex`, and compile/elaborate/run logs preserve the evidence. Negative simulations sometimes exited 0 despite `$fatal`, so the runner checks `CHECKER_FAIL code`, fatal output, and absence of a full-run pass marker together. With a six-bit address, an invalid progression appears as a wrong direction, early wrap, repeat, or extra request. An internal early comparison is observable only if it changes an output; the tested variant changed diagnostics early and was detected.

## v5 · 09.14–09.17 — Faulty memory model

One instance is configured by `fault_type` (0 fault-free; 1 SA0; 2 SA1; 3 Rising TF; 4 Falling TF), `fault_addr[5:0]`, and `fault_bit[2:0]`. SA faults force a selected bit to 0/1; writing the opposite value activates them. Transition faults require a known old bit and a real attempted 0→1 or 1→0 transition. `fault_activated` latches whether any activation occurred; `activation_count` counts events. Detection is an MBIST read-comparison result. The fault model acts on RAM cells, not controller result ports.

Added `tb/fault_injector.sv` and `faulty_memory.sv` while retaining v1 RAM timing. Synchronous reset clears response validity and activation records but retains cells. Controller `rtl/` was unchanged. Unknown fault types are rejected. SA0/SA1 target bits read as stuck before the first write; other uninitialized bits remain unknown.

The stand-alone `tb_faulty_memory_unit.sv` tests target and other cells, reverse-direction and repeated writes, readback, and reset retention. `fault_reference_monitor.sv` maintains a separate physical reference state from external requests, checking reads and activation each cycle. The v4 checker still checks 640 requests and diagnostics. The integration testbench independently specifies first-error phase/address, expected/actual data, and comparison-error count.

`run_step05.py` ran seven stand-alone and seven MBIST cases in each simulator, for 28 PASS results. Fault-free mode returned PASS without activation. All four types activated and were detected as prescribed; every integrated case completed 640 requests. Boundary cases included SA0 at address 63/bit 7 and Falling TF at address 0/bit 0. See `results/step05/README.md` and [v5 definitions](05_faulty_memory_model.md).

## v6 · 09.18–09.21 — Automated fault campaign

`generate_fault_manifest.py` enumerated four types × 64 addresses × eight bits, assigning unique IDs `F0000`–`F2047`. A pilot selected eight address/bit combinations per type, or 32 instances.

Added `tb_step06_campaign.sv` and `run_step06.py`, reusing the v4 checker and v5 reference monitor. An experiment-only `experiment_clear` returns faulty RAM and monitor state to unknown between instances within one compiled snapshot; the controller and checker are also reset and starting state checked. Ordinary memory-reset semantics are unchanged, as is production MBIST RTL. Each simulator compiles once; the runner processes batches and bisects a failed batch down to one instance while preserving reasons and logs.

The pilot produced 64 valid tool records. The full campaign produced 4,096 valid records for all 2,048 configurations, with zero field disagreements across tools. All records show activation, detection, first-error diagnostics, and 640 requests; none is invalid. `audit_step06.py` checked manifest uniqueness, counts, and pairs. `F1023` replay matched the full results. The existing 28 directed cases were rerun to confirm that `experiment_clear` preserved v5 behavior; both simulators passed. CSV, JSONL, logs, and audit are indexed in `results/step06/README.md`.

## v7 · 09.22–09.23 — Fault coverage evaluation

Added `evaluate_fault_coverage.py` to read the v6 frozen manifest, case results, 64 raw logs, tool comparisons, and v1 reference sequence without running simulation or changing RTL. The denominator is 2,048 unique IDs. A detection requires both runs to be valid, activated, detected, and consistent. The script cross-checks activation events, checker result, and first-error diagnostics against v6 audit outputs. Altering one CSV detection phase makes the script reject the record.

Each type has 512/512 confirmed detections, giving 2,048/2,048 overall, or 100.00% for each type and the total. Unactivated, activated but undetected, invalid/failed, and tool-disagreement counts are zero. First-detection phases: SA1→M1, SA0/Rising TF→M2, Falling TF→M3, constant across addresses and bits; first-error address always equals the injected address. The reference has 640 operations (320 reads, 320 writes); all 4,096 valid records have 640 requests and 960 cycles by the v6 count. v3's 961-cycle count includes the start-sampling edge. Per-type CSV, phase matrix, case evaluation, exceptions and efficiency JSON are in `results/step07/README.md` and [v7 evaluation](07_fault_coverage_evaluation.md).

## v8 · 09.24–09.25 — Board project and offline implementation

Kept 64×8, 640 requests, and original `mbist_top`; added board top, KEY0 synchronizer/debounce, RESET conditioning, LED0–3, and ILA request counter. The XDC was checked against the Da Vinci V2.1 schematic and pin list. Vivado 2018.3 targeted `xc7a35tfgg484-2` with Industrial operating conditions. March C− and the v6 fault campaign were unchanged.

The first implementation met timing but reported BRAM enable warning `REQP-1840` for asynchronous control. The board reset path was revised to an asynchronous-clear first stage and synchronous output stage; the warning disappeared after rebuild. The schematic also prompted `CFGBVS=VCCO`, `CONFIG_VOLTAGE=3.3`, and constraints for only the used KEY0 input.

Initial offline measurements: controller-only synthesis used 48 LUTs, 40 registers, no BRAM. Full normal build used 99 LUTs, 62 registers, one RAMB18E1 with `DOA_REG=0` and `WRITE_MODE_A=NO_CHANGE`, WNS +14.628 ns. The initial ILA build had 18 probe groups and depth 1,024, WNS +14.169 ns. Both met 20 ns timing and generated bitstreams/`.ltx`. Two normal board-wrapper starts passed the independent 640-request checker in XSim and Icarus. `audit_step08.py` checked reports, BRAM parameters, probe names and releases. See [implementation](08_fpga_implementation.md) and `results/step08/README.md`. Board captures are recorded in v9.

## v9 · 2026-09-26 — Board captures and evidence archive

Saved photos of the Da Vinci device marking and connections, and LED states after KEY0 in the baseline and ILA builds. Both result photos show DONE/PASS on, FAIL/BUSY off. Native `ILADATA.ila` was archived as `results/step08/hardware/ila_capture/2026-09-26_march_c_minus_64x8_full_run.ila`. Seven phase screenshots were named in M0–M5 transition order without altering image content. See the [initial board index](../results/step08/hardware/README.md).

`audit_step08_ila.py` extracted 1,024-point CSV/VCD from the native file. It compared all 640 external requests against v1, including phase, address, operation, write data, read value, and one-cycle response. Counts were 320 reads and 320 writes, with phase lengths 64/128/128/128/128/64. Final M5/address 63 request was at sample 959, response at 960, first DONE/PASS at 961; PASS held through 1023 with FAIL=0, errors=0, BUSY=0. Machine-readable result: `results/step08/hardware/ila_audit.json`. Additional reset, restart, device-ID, and controlled-FAIL tests appear in the final acceptance below.

## 2026-09-26 — Engineering revision

- Moved builds under project-local `.build/<run-id>` and new results under `results/reruns/<run-id>`; tools are discovered through environment, local configuration, or PATH.
- Completed synchronous reset release, KEY0 `ASYNC_REG` settings, and external-endpoint timing exceptions. A CDC-7 finding on the previous reset structure disappeared with a two-stage release chain plus synchronous core output.
- Fixed request-count clearing on a busy KEY0 pulse. Added a normally disabled one-time read-response perturbation. The checker caught an initial port-direction error; the corrected wiring passed.
- Reran RAM, integration, 14 checker cases, 28 directed faults, 2,048-instance campaign, and replay in both tools. Three normal and three perturbed board-wrapper simulations per tool also passed.
- All four board builds met 50 MHz setup and hold timing. Normal WNS/WHS: +14.474/+0.121 ns; normal ILA: +13.458/+0.036 ns; perturbed: +15.085/+0.130 ns; perturbed ILA: +13.031/+0.062 ns.
- Kept the original ILA and created a copy with a portable relative WDB reference. Source headers retained author/module details while unverified dates and editor fields were removed.

See the [engineering review](09_engineering_review.md) and [board acceptance](../results/step08/hardware_final/README.md).

## 2026-09-27 — Board Evidence Archiving and Acceptance

- Indexed 17 originals captured on 09.26: seven board photos, five interface screenshots, and five native ILA files. File content and names were preserved.
- Photos show normal DONE/PASS, controlled DONE/FAIL, RESET clearing results, and normal restart. Hardware Manager shows XC7A35T Programmed.
- Added `audit_final_hardware.py` to compare native ILA CSVs against all 640 v1 requests, one-cycle responses, count, DONE, error count, and first-error fields.
- Three normal runs returned PASS; two perturbed runs returned FAIL with one error at M2/address 7/FF→FE. The second capture retains the previous result at sample 0 and clears count/diagnostics on the new start. All five runs finish at sample 961.
- ILA UUID and 18 probe mappings match release LTX files. Six released files match implementation outputs. The combined four-build timing and hardware audit passed.
- Updated the README, implementation report, board procedure, and result indexes. v9 board acceptance is complete.

[Final board evidence and audit](../results/step08/hardware_final/README.md)

## v10 — ASIC controller architecture

Added `mbist_asic_top.v` as a pass-through wrapper around the shared controller interface. The synthesis list contains only this wrapper and six shared RTL files. The existing v4/v5 checker, reference CSV, RAM, and fault models are reused. Icarus/XSim ran 32 scenarios across the original and ASIC tops; normal operation, response perturbation, four fault types, and boundary diagnostics agreed. The Vivado RTL project records the seven-file hierarchy and three original screenshots. Vivado 2018.3 does not support `open_elaborated_design` as the batch Tcl command used initially; `synth_design -rtl` succeeded. [Architecture and results](10_asic_architecture.md).

## v11 — Nangate45 configuration and constraints

The v10 synchronous read-response and reset protocol determines the 20 ns clock, 0/2 ns input/output delays, 0.1 ns input transition, and 4 fF load. All 12 non-clock input bits and 54 output bits are constrained; synchronous `rst_n` is not assigned a false path. Moving ORFS work to WSL ext4 resolved Windows-mount `touch -r` permissions. Collection checks use supported `llength` instead of `sizeof_collection`. Preliminary synthesis reports 0 structural problems; nine path groups and per-port constraints passed checks. [Constraint rationale and logs](11_asic_constraints.md).

## v12 — Standard-cell synthesis and netlist verification

Independent synthesis using the frozen v11 configuration produced a 264-cell netlist with 42 DFFs. Final Yosys structural checks report 0 problems. Three canonicalize messages about parameterized modules containing processes are resolved by subsequent `proc` and mapping. Zero-delay cell models come from the same Liberty; XSim's required `timescale` is added only to build copies. All 16 dual-simulator scenarios passed, with 640 requests and 960 checker-counted cycles per run. First-failure diagnostics and continued execution after errors match v10. [Synthesis and gate-level results](12_asic_synthesis.md).

## v13 — Area and synthesis-stage STA

Per-cell Yosys and Liberty areas agree with LEF dimensions. The 264 cells total 483.322 µm²: 189.924 µm² sequential and 293.398 µm² combinational. OpenROAD uses the `5K_hvratio_1_1` wire-load model and ideal clock; Setup WNS is +17.3953 ns under 20 ns constraints. The worst path runs from `rd_data[7]` to the first-failure actual-data register; its 2.3656 ns arrival includes 2.0000 ns of external input delay. Because `report_checks -unconstrained` text also lists constrained groups, checks combine JSON path groups with `check_setup`. Both diagnostics and unconstrained-group counts are 0. Seven original screenshots and numerical checks are archived for this version. [Evaluation report](13_synthesis_evaluation.md).

## 2026-09-28 — Project Organization and Regression Checks

Updated the ASIC file index and run instructions, then checked script paths, documentation links, and archived results. Simulation caches are under `.build/asic/`; results are stored by run ID. Commands are in the [reproduction guide](reproduce.md).

XSim/Icarus reran the RTL regression, with all [32 scenarios passing](../results/asic/v10/20260928_source_check/report.json). [Area and timing-data checks](../results/asic/v13/20260928_offline_check/preparation_audit.json) on the original v13 reports matched their results. A fresh STA attempt stopped because Docker was unavailable in WSL; the [run log](../results/asic/v13/20260928_offline_check/sta_attempt.log) is retained. The timing recheck uses existing reports.
