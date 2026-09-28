# V13 Area and Synthesis-Stage Timing Evaluation Records

Status: PASS. The formal run is [`20260927_v13_readout/`](20260927_v13_readout/final_audit.json): 264 standard cells including 42 DFFs, 483.322 µm² total area, and Setup WNS +17.3953 ns at a 20 ns clock. Analysis is in [`docs/13_synthesis_evaluation.md`](../../../docs/13_synthesis_evaluation.md).

| File | Purpose |
| --- | --- |
| [`input_snapshot/`](20260927_v13_readout/input_snapshot/synth_stat.txt) | V12 netlist, V11 SDC, Liberty/LEF, original Yosys reports, and execution-script snapshots |
| [`preflight.json`](20260927_v13_readout/preflight.json) | SHA-256 comparison against verified V12 inputs |
| [`area_summary.json`](20260927_v13_readout/area_summary.json), [`area_cells.csv`](20260927_v13_readout/area_cells.csv) | Per-cell and categorized Liberty/LEF/Yosys area reconciliation |
| [`sta/setup_wns.rpt`](20260927_v13_readout/sta/setup_wns.rpt), [`sta/setup_top10.rpt`](20260927_v13_readout/sta/setup_top10.rpt) | Setup WNS and worst paths |
| [`sta/`](20260927_v13_readout/sta/reg_to_reg.rpt) | Original path-category, `check_setup`, and unconstrained-path reports |
| [`sta.log`](20260927_v13_readout/sta.log), [`preparation_audit.json`](20260927_v13_readout/preparation_audit.json) | Tool conditions and report completeness |
| [`screenshots/`](#screenshots) | Eight original screenshots and their meanings |
| [`final_audit.json`](20260927_v13_readout/final_audit.json) | Cross-checks of metrics, paths, inputs, and report/image fingerprints |

To reproduce, run `bash asic/scripts/run_v13.sh NEW_RUN_ID` from the Ubuntu WSL project root. A new run archives generated reports without copying historical screenshots. The [STA recheck](projectiii_integration/final_audit.json) under the ProjectIII path matches the frozen results.

## Screenshots

| Image | Contents and corresponding report |
| --- | --- |
| [`01_yosys_synthesis_statistics.png`](20260927_v13_readout/screenshots/01_yosys_synthesis_statistics.png) | Yosys: 264 cells, 42 DFFs, 483.322 µm² total area; `input_snapshot/synth_stat.txt` |
| [`02_area_liberty_reconciliation.png`](20260927_v13_readout/screenshots/02_area_liberty_reconciliation.png) | Area audit PASS, combinational/sequential counts and areas; `area_summary.json` |
| [`03_critical_setup_path_detailed.png`](20260927_v13_readout/screenshots/03_critical_setup_path_detailed.png) | Overall worst setup path, including cell chain, fanout, arrival/required times, and +17.3953 ns slack; `sta/setup_top10.rpt` |
| [`04_sta_audit_snapshot.png`](20260927_v13_readout/screenshots/04_sta_audit_snapshot.png) | Report-generation audit interface, hashes, interconnect model, and constraint checks. Final status is recorded in `preparation_audit.json` and `final_audit.json` |
| [`05_openroad_analysis_conditions.png`](20260927_v13_readout/screenshots/05_openroad_analysis_conditions.png) | OpenROAD environment, wire-load model, one clock, 13 inputs, 54 outputs, 42 registers; `sta.log` |
| [`06_register_to_register_path.png`](20260927_v13_readout/screenshots/06_register_to_register_path.png) | March phase to address-register path; `sta/reg_to_reg.rpt` |
| [`07_critical_setup_path_compact.png`](20260927_v13_readout/screenshots/07_critical_setup_path_compact.png) | Compact timing breakdown of the worst setup path; `sta/setup_top10.rpt` |
| [`08_register_to_output_path.png`](20260927_v13_readout/screenshots/08_register_to_output_path.png) | March phase to `req_wdata[1]` path; `sta/reg_to_output.rpt` |

## Report reconciliation

On 2026-09-28, the current `audit_v13.py` checked frozen inputs and original reports from `20260927_v13_readout` offline. [Area and path checks](20260928_offline_check/preparation_audit.json) passed; the [execution record](20260928_offline_check/check.log) identifies the report source. Area 483.322 µm² and WNS +17.3953 ns match the original reports. A fresh STA attempt stopped because Docker was unavailable in WSL; its [error output](20260928_offline_check/sta_attempt.log) is retained. This check reconciles the existing reports.
