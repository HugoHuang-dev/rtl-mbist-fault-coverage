# V12 Standard-Cell Synthesis and Netlist Verification Records

Acceptance run: [`20260927_v12_frozen/`](20260927_v12_frozen/report.json). The [regression report](20260927_v12_frozen/report.json) is PASS: eight scenarios each in Icarus and XSim, totaling 16. Each run of the two-run sequence completes 640 requests, as does each of the seven fault scenarios. External results match the frozen V10 records.

| Evidence | Contents |
| --- | --- |
| [`1_2_yosys.v`](20260927_v12_frozen/orfs/results/nangate45/mbist_asic_top/base/1_2_yosys.v) | Formal Nangate45 standard-cell netlist |
| [`synthesis.log`](20260927_v12_frozen/synthesis.log), [`orfs/logs/`](20260927_v12_frozen/orfs/logs/nangate45/mbist_asic_top/base/1_2_yosys.log) | Synthesis commands and original tool logs |
| [`synth_check.txt`](20260927_v12_frozen/orfs/reports/nangate45/mbist_asic_top/base/synth_check.txt), [`synth_stat.txt`](20260927_v12_frozen/orfs/reports/nangate45/mbist_asic_top/base/synth_stat.txt), [`structure.json`](20260927_v12_frozen/structure.json) | 0 structural problems, cell statistics, and model coverage |
| [`cell_model.v`](20260927_v12_frozen/cell_model.v), [`cell_model_generation.log`](20260927_v12_frozen/cell_model_generation.log) | Zero-delay functional model generated from the same Liberty, with command log |
| [`icarus/`](20260927_v12_frozen/icarus/sequence/sequence.log), [`xsim/`](20260927_v12_frozen/xsim/sequence/sequence.log) | Compilation, elaboration, and per-scenario raw checker logs, including simulation copies |
| [`report.json`](20260927_v12_frozen/report.json), [`oracle.hex`](20260927_v12_frozen/oracle.hex) | Machine-readable results and transaction oracle from the frozen CSV |
| [`toolchain.txt`](20260927_v12_frozen/toolchain.txt), [`input_snapshot/`](20260927_v12_frozen/input_snapshot/config.mk) | Versions and snapshots for tools, Liberty, RTL, configuration, netlist, models, and test inputs |
| [`simulator_versions.txt`](20260927_v12_frozen/simulator_versions.txt) | Simulator versions |

Reproduction commands, the timescale compatibility issue, structure-review criteria, and functional-verification scope are in [`docs/12_asic_synthesis.md`](../../../docs/12_asic_synthesis.md).
