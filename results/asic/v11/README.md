# V11 Configuration and Constraint-Check Records

Acceptance run: [`20260927_v11_frozen/`](20260927_v11_frozen/audit.json). The [automated audit](20260927_v11_frozen/audit.json) is PASS: one clock, 12 constrained non-clock input bits, 54 constrained output bits, and no timing exceptions. Nine representative categories of constrained paths can be reported.

| File | Contents |
| --- | --- |
| [`config_parse.log`](20260927_v11_frozen/config_parse.log) | Top, platform, RTL, SDC, and ABC period resolved by ORFS |
| [`synth_validation.log`](20260927_v11_frozen/synth_validation.log) | Complete preliminary synthesis and `read_sdc` log |
| [`constraint_check.log`](20260927_v11_frozen/constraint_check.log) | OpenROAD `check_setup`, port counts, and nine path groups |
| [`1_synth.sdc`](20260927_v11_frozen/orfs/results/nangate45/mbist_asic_top/base/1_synth.sdc) | Constraints expanded by the tool for individual ports |
| [`synth_check.txt`](20260927_v11_frozen/orfs/reports/nangate45/mbist_asic_top/base/synth_check.txt) | Yosys structural check: 0 problems |
| [`toolchain.txt`](20260927_v11_frozen/toolchain.txt) | ORFS commit, image digest, and Liberty/RTL/configuration SHA-256 |
| [`input_snapshot/`](20260927_v11_frozen/input_snapshot/config.mk) | Run-specific configuration, SDC, file list, and three check-script snapshots |

Original failure logs retain the [Windows-mount timestamp error](20260927_v11_prelim/synth_validation.log) and [unsupported collection command](20260927_v11_ext4/synth_validation.log). `20260927_v11_frozen` is the historical acceptance record. The [ProjectIII configuration and constraint run](projectiii_integration/audit.json) validates the relocated seven-file list, synthesis, and SDC entry points.

Commands and constraint rationale are in [`docs/11_asic_constraints.md`](../../../docs/11_asic_constraints.md). These netlists and paths belong to V11 configuration checks; V12 netlist functionality and V13 area/timing evaluation are recorded in their respective reports.
