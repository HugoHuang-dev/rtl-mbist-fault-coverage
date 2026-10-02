# v6: Automated Fault-Injection Campaign

v6 · 09.18–09.21. Both simulators completed the full set of 2,048 single-fault instances. The manifest, results, and raw logs are indexed in the [v6 evidence](../results/step06/README.md).

## Manifest and execution

The fault set contains v5's SA0, SA1, Rising TF, and Falling TF models, across 64 addresses and eight bit positions, with one configured fault per case. `scripts/generate_fault_manifest.py` enumerates type, address, and bit to produce IDs `F0000`–`F2047`: 512 instances of each type. `fault_manifest.csv` defines the full target set. A separate `pilot_manifest.csv` selects eight different address/bit combinations per type, for 32 pilot instances.

`scripts/run_step06.py` builds an Icarus image and an XSim snapshot once per tool, then normally runs 64 instances per simulator process. Before each instance, the testbench asserts `experiment_clear` to return faulty RAM cells, read responses, and reference-model state to their uninitialized state. It then resets the controller and checker and verifies that activation counts, responses, and DONE are clear. An ordinary `rst_n` reset continues to preserve memory contents. The production `rtl/` controller was not modified. The v4 checker verifies the complete March sequence; the v5 reference monitor verifies read values and activation events.

The runner retains every simulator-process log. Each structured record carries `raw_log` to locate it. If a batch fails, times out, or lacks a required marker, the runner bisects it to an individual case and records invalid cases with reasons. `simulation_status` describes record validity; `outcome` distinguishes `activated_detected`, `activated_escape`, `not_activated`, and `invalid`. Detection without activation evidence is invalid. v7 defines the coverage denominator.

## Results

| Measure | Result |
| --- | ---: |
| Unique manifest entries | 2,048; 512 per type |
| Pilot | 32 instances × 2 tools = 64 valid records |
| Full campaign | 2,048 instances × 2 tools = 4,096 valid records |
| Invalid full-run records | 0 |
| Disagreements between paired tool results | 0 / 2,048 |
| Activated and detected tool records | 4,096 |
| Requests per instance | 640 |
| Cycles per instance | 960, using this testbench's DONE observation interval |

For every instance, both tools recorded activation, detection, first-error diagnostics, all 640 requests, and normal termination. `scripts/audit_step06.py` independently checks the manifest, record count, tool pairs, and raw markers. A single-case replay also matched the full-run result.

## Evidence and reproduction

The [v6 evidence index](../results/step06/README.md) contains manifest files, CSV/JSONL results, tool-specific raw logs, build logs, audit results, and commands. Run the full campaign with `py -3 scripts/run_step06.py --mode all`, replay one instance with `py -3 scripts/run_step06.py --mode replay --fault-id F1023 --tool both`, and audit with `py -3 scripts/audit_step06.py`. Vivado 2018.3 XSim and Icarus Verilog must be installed and callable. The [reproduction guide](reproduce.md) explains output directories and `MBIST_AUDIT_RUN_ID`; select the same run ID when auditing new results.

Coverage statistics and the denominator definition are documented in the [v7 report](07_fault_coverage_evaluation.md).
