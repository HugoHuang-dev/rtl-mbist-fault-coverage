# Project 3 — RTL MBIST with Automated Fault Coverage Evaluation

Development period: 2026.09.02–09.26 · Board: Da Vinci V2.1 / Artix-7 XC7A35TFGG484-2I  
Tools: Verilog / SystemVerilog, Vivado 2018.3, XSim, Icarus Verilog, Python

## Highlights

- Modular March C− RTL with synchronous RAM access, first-error diagnostics, and continued execution after a mismatch.
- Independent transaction checking, six controller mutation tests, and four validated single-fault models.
- Automated dual-simulator campaign: 2,048 unique faults, 4,096 result records, and reproducible per-case logs.
- FPGA validation at 50 MHz: BRAM inference, routed timing reports, and five normal/controlled-failure ILA captures.

The project progressed from a memory specification and stand-alone RAM tests through the MBIST controller, independent checker, fault models, automated campaign, coverage analysis, and FPGA validation. The controller entry point is [`mbist_top.v`](rtl/mbist_top.v); the board top level is [`board_top.v`](fpga/board_top.v). The [releases](releases/README.md) contain bitstreams, including the ILA build, and probe files.

The final v9 design executes 640 March C− requests (320 reads and 320 writes). XSim and Icarus detected all 2,048 instances of the four defined single-fault behavior models. The four FPGA builds (normal and perturbed, each with and without ILA) meet the 50 MHz timing constraint. Board tests cover reset, repeated start, PASS, and controlled FAIL. Five native ILA captures each show a complete 640-request run. The controlled failure reports M2, address 7, expected FF, actual FE.

[Final board acceptance and original evidence](results/step08/hardware_final/README.md) · [Utilization and timing reports](results/reruns/20260926_review_final/README.md) · [Bitstreams and probe files](releases/20260926_review/README.md)

## System design

March C− visits 64 addresses in six phases: `M0 ↑(w0)`, `M1 ↑(r0,w1)`, `M2 ↑(r1,w0)`, `M3 ↓(r0,w1)`, `M4 ↓(r1,w0)`, and `M5 ↑(r0)`. Here `0` means `8'h00` and `1` means `8'hFF`. At each address, a read and comparison complete before the next write. The six phases require `10 × 64 = 640` requests. The [reference CSV](specs/march_c_minus_64x8.csv) specifies each address, direction, operation, and expected value.

```text
Board: RESET / KEY0 → MBIST controller → single-port synchronous BRAM
                               ↑                         │
                         read response and check ←───────┘
                               ↓
                        DONE / PASS / FAIL → LEDs + ILA

Simulation: fault manifest → XSim / Icarus + faulty RAM
                                      ↓
                      independent checker and fault reference monitor
                                      ↓
                      raw logs → Python audit → coverage and detection phase
```

Simulation and FPGA builds use the same controller RTL. Python runs the simulators and analyzes their logs. LEDs and ILA expose the board behavior. Fault coverage is calculated from the simulated faulty RAM; board measurements are reported separately.

## Version history · 2026.09.02–09.26

| Period | Version | Work completed | Evidence |
| --- | --- | --- | --- |
| 09.02–09.03 | v1 Specification and reference sequence | Defined 64×8 memory, 50 MHz clock, one-cycle synchronous read, and the 640-request March sequence | [Specification](docs/01_memory_march_spec.md) · [Transaction CSV](specs/march_c_minus_64x8.csv) |
| 09.04–09.06 | v2 Fault-free RAM | Implemented single-port synchronous RAM and stand-alone read/write tests | [RAM verification](docs/02_ram_verification.md) · [Logs](results/step02/README.md) |
| 09.07–09.10 | v3 MBIST controller | Integrated FSM, address/data generators, response comparison, and PASS/FAIL diagnostics | [Controller verification](docs/03_mbist_rtl_verification.md) · [Trace evidence](results/step03/README.md) |
| 09.11–09.13 | v4 Independent checker | Checked external transactions and ran six categories of single-change negative tests | [Verification design](docs/04_independent_verification.md) · [Regression report](results/step04/README.md) |
| 09.14–09.17 | v5 Faulty RAM | Added SA0, SA1, rising/falling transition faults, and an independent fault reference model | [Model definition](docs/05_faulty_memory_model.md) · [28 directed runs](results/step05/README.md) |
| 09.18–09.21 | v6 Automated campaign | Generated 2,048 fault instances, completed a pilot and both full simulator runs, and verified single-case replay | [Campaign method](docs/06_automated_fault_campaign.md) · [Raw results](results/step06/README.md) |
| 09.22–09.23 | v7 Coverage evaluation | Audited unique instances, reconciled exceptions, and generated the first-detection phase matrix | [Evaluation](docs/07_fault_coverage_evaluation.md) · [Statistics](results/step07/README.md) |
| 09.24–09.25 | v8 FPGA implementation | Confirmed BRAM inference, implemented the 50 MHz design, and built bitstreams and ILA probes | [Implementation](docs/08_fpga_implementation.md) · [Build evidence](results/step08/README.md) |
| 09.26 | v9 Board validation | Checked normal and perturbed runs, reset, repeated start, LEDs, and five ILA captures | [Board evidence](results/step08/hardware_final/README.md) · [ILA audit](results/step08/hardware_final/audit.json) |

### v1–v2: Memory specification and RAM verification

v1 defines the `req_valid/req_ready` request handshake, the `rd_valid/rd_data` read response, and the M0–M5 operation order. v2 adds [`single_port_sync_ram.v`](rtl/single_port_sync_ram.v) and a stand-alone [RAM testbench](tb/tb_single_port_sync_ram.sv).

The testbench samples around the request edge and at the following rising edge, avoiding false results from nonblocking-assignment event scheduling. XSim and Icarus each passed 146 checks covering addresses 0 and 63, consecutive and alternating reads/writes, idle behavior, and memory retention across reset. RAM-only synthesis inferred one RAMB18E1 with `DOA_REG=0`. Commands and logs are in the [v2 evidence](results/step02/README.md).

### v3: March C− controller

[`march_controller.v`](rtl/march_controller.v) sequences the phases and read-before-write operations. Separate modules generate addresses and data, handle the memory request interface, and check responses in [`response_checker.v`](rtl/response_checker.v). Read data is compared only when `rd_valid` is asserted. The controller continues after an error and asserts DONE after the final M5 read is checked.

Fault-free XSim and Icarus runs each recorded 640 requests and PASS. A one-time read-response perturbation at M2/address 7 made the controller record the first error, finish all 640 requests, and return FAIL. The external request trace matched the v1 CSV transaction by transaction (`TRACE_CHECK_PASS`; see [v3 evidence](results/step03/README.md)). This diagnostic test is separate from the fault-coverage campaign.

### v4: Independent checker and negative tests

[`march_transaction_checker.sv`](tb/march_transaction_checker.sv) observes RAM requests, read responses, and result ports outside the controller. It takes expected transactions from the v1 CSV and does not inspect the controller FSM. The regression script generates single-change RTL variants in a temporary directory.

The variants change address direction, read/write order, write data, comparison timing, DONE timing, or first-error address. Across both simulators, two baselines passed and the checker rejected all 12 variants in the expected error category. Regression checks the reported category, fatal messages, and pass markers, since a negative simulation may still exit with code 0. See the [regression report](results/step04/report.csv).

### v5: Directed fault-model verification

[`faulty_memory.sv`](tb/faulty_memory.sv) configures one fault by type, address, and bit. SA0/SA1 force the selected bit; a transition fault activates only when the old bit value and write direction match its definition. [`fault_reference_monitor.sv`](tb/fault_reference_monitor.sv) maintains an independent expected state from external transactions.

Stand-alone RAM tests check bit readback, state transitions, and activation counts before the model is integrated with the controller and v4 checker. All 28 directed XSim/Icarus runs passed. Fault-free operation returned PASS; all four fault types activated and were detected as expected, with correct first-error phase and address. The controller completed 640 requests in every run. See [v5 evidence](results/step05/README.md).

### v6–v7: Full campaign and coverage evaluation

The v6 [fault manifest](results/step06/fault_manifest.csv) enumerates four types × 64 addresses × 8 bits, giving 2,048 unique instances. A 32-instance pilot preceded one full run in each simulator. The runner reuses compiled simulation artifacts, executes cases independently, and saves per-case results, raw logs, hashes, and a `fault_id` replay entry point. MBIST RTL was unchanged.

The records distinguish activation, detection, and simulation validity. The full campaign produced 4,096 valid simulator records, with zero disagreements across 2,048 paired instances and zero invalid records. Audit and `F1023` replay passed. See the [campaign index](results/step06/README.md) for methods and raw data.

v7's [`evaluate_fault_coverage.py`](scripts/evaluate_fault_coverage.py) reads the manifest, results from both simulators, and raw logs. Its denominator is the 2,048 unique fault instances. An instance counts as confirmed detected when both runs are valid, activated, detected, and consistent on key fields. The script checks log hashes and first-error fields; changing a detection phase in a result CSV causes the audit to fail. Outputs include the [coverage table](results/step07/coverage_by_type.csv) and [exception list](results/step07/exceptions.csv).

### v8–v9: FPGA implementation and board validation

v8 adds [`board_top.v`](fpga/board_top.v). KEY0 starts the test after synchronization and debouncing; LED0–3 indicate DONE, PASS, FAIL, and BUSY. [Pin constraints](fpga/board_pins.xdc) connect the 50 MHz clock, keys, and LEDs. Vivado 2018.3 produced the [project](fpga/vivado/README.md), a build without ILA, and a build with 18 ILA probe groups.

CDC checks cover synchronous reset release and the KEY0 synchronizer. The synchronized reset output removes the BRAM asynchronous-control warning. Synthesis confirms one RAMB18E1 for the MUT with `DOA_REG=0`. All four normal/perturbed implementations meet the 20 ns clock constraint. In v9, reset cleared the result LEDs; a normal KEY0 start ended with DONE/PASS, and the perturbed build ended with DONE/FAIL. Three normal and two perturbed [ILA captures](results/step08/hardware_final/README.md) passed the 640-transaction reference-sequence audit. The second start cleared the previous count and diagnostics. Both perturbed runs reported M2, address 7, FF→FE, error count 1, and continued through DONE.

## Final measurements

### Simulated single-fault coverage

| Fault type | Target instances | Confirmed by both tools | First detected |
| --- | ---: | ---: | --- |
| SA0 | 512 | 512 | M2 |
| SA1 | 512 | 512 | M1 |
| Rising transition fault | 512 | 512 | M2 |
| Falling transition fault | 512 | 512 | M3 |
| Total | 2,048 | 2,048 (100.00%) | [Full phase matrix](results/step07/detection_stage_matrix.csv) |

There were zero unactivated faults, activated but undetected faults, invalid simulations, or cross-tool disagreements. Each entry in the [evaluation CSV](results/step07/fault_evaluation.csv) links back to the [raw results](results/step06/full/raw_results.csv) and logs. The [coverage evaluation](docs/07_fault_coverage_evaluation.md) defines the model scope and calculation.

### FPGA utilization, timing, and measurements

| Build | LUTs | Registers | RAMB18 / RAMB36 | WNS / ns | WHS / ns |
| --- | ---: | ---: | ---: | ---: | ---: |
| Controller-only synthesis | 48 | 40 | 0 / 0 | Not implemented | Not implemented |
| Normal, no ILA | 98 | 63 | 1 / 0 | +14.474 | +0.121 |
| Normal, with ILA | 1,930 | 2,934 | 2 / 2 | +13.458 | +0.036 |
| Perturbed, no ILA | 112 | 73 | 1 / 0 | +15.085 | +0.130 |
| Perturbed, with ILA | 1,941 | 2,944 | 2 / 2 | +13.031 | +0.062 |

All four implemented builds meet 50 MHz setup and hold timing; TNS and THS are zero. Full-system figures include ILA logic and memory. The [report index](results/reruns/20260926_review_final/README.md) links utilization, timing, CDC, and synchronizer checks for each build. Controller-only data is in the [synthesis report](results/step08/controller/utilization.rpt).

[Board acceptance](results/step08/hardware_final/README.md) contains 17 original evidence files. Three normal runs ended in PASS; two controlled-perturbation runs ended in FAIL at M2/address 7/FF→FE. Each executed 640 requests. The perturbation changes one read response in board-level wrapper logic to exercise the diagnostic path.

![Normal completion: 640 requests, DONE/PASS](results/step08/hardware_final/screenshots/07_normal_ila_round1_done.png)

![Controlled failure: 640 requests, DONE/FAIL, one error](results/step08/hardware_final/screenshots/14_fault_ila_done_640.png)

## Reproduction and project index

See the [repository contents](REPOSITORY_CONTENTS.md) for the source and evidence layout, and the [reproduction guide](docs/reproduce.md) for tool setup, simulation, and build commands. Copy [toolchain.example.json](toolchain.example.json) to `toolchain.local.json` and adjust tool paths, or use environment variables. A new run uses a separate identifier and writes outputs under `.build/` and `results/reruns/`.

```powershell
$env:MBIST_RUN_ID = 'local_check_01'
py -3 scripts/run_step04.py
py -3 scripts/run_step05.py
py -3 scripts/run_step06.py --mode all
$env:MBIST_AUDIT_RUN_ID = $env:MBIST_RUN_ID
py -3 scripts/audit_step06.py
py -3 scripts/evaluate_fault_coverage.py
py -3 scripts/run_step06.py --mode replay --fault-id F0123
```

[Software review](results/reruns/20260926_engineering_review/README.md) · [Final FPGA build](results/reruns/20260926_review_final/README.md) · [Normal and perturbed bitstreams](releases/20260926_review/README.md) · [Board photos, ILA data, and audits](results/step08/hardware_final/README.md)

| Directory | Contents |
| --- | --- |
| [`specs/`](specs/README.md) | Frozen transaction-by-transaction March C− reference sequence |
| [`rtl/`](rtl/README.md) | Fault-free RAM, MBIST controller, and response checker |
| [`tb/`](tb/README.md) | RAM testbench, independent transaction checker, fault model, and reference monitor |
| [`scripts/`](scripts/README.md) | Fault manifest, regression, coverage, and ILA audit tools |
| [`fpga/`](fpga/README.md) | Board top level, XDC, [Vivado project](fpga/vivado/README.md), and build scripts |
| [`releases/`](releases/README.md) | ILA and non-ILA bitstreams with probe files |
| [v2 RAM](results/step02/README.md), [v3 controller](results/step03/README.md), [v4 checker](results/step04/README.md), [v5 faults](results/step05/README.md) | Simulation and directed-test records |
| [v6 campaign](results/step06/README.md), [v7 coverage](results/step07/README.md) | Full fault results and independent evaluation |
| [v8–v9 FPGA](results/step08/README.md) | Reports, bitstreams, photos, native ILA captures, and audits |
| [Design documents](docs/README.md) | Version documentation and [development log](docs/DEVLOG.md) |
| [`evidence/`](evidence/README.md) | Source snapshots, SHA-256 records, and source mapping |

Reference projects: [MBIST March Algorithms](https://github.com/Happy251005/mbist-march-algorithms), [Politecnico di Torino Memory BIST](https://github.com/cad-polito-it/memory-bist), and [SRAM Controller UVM Verification](https://github.com/abdo-ehab-euv/sram-controller-uvm-verification). Coupling faults, March X, and ASIC implementation were not part of this project.
