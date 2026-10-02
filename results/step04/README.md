# v4 Regression Evidence

v4 · 09.11–09.13. Baseline and negative-test results for the independent checker are stored here. From the project root:

```powershell
py -3 .\scripts\run_step04.py
```

The script uses XSim/Vivado 2018.3 and Icarus. It generates single-change RTL variants in temporary work storage without modifying production RTL. Generated source, `oracle.hex`, and simulator build files are kept with the case; this directory holds reviewable inputs, logs, and reports.

| File | Contents |
| --- | --- |
| `oracle.hex` | 18-bit expected transaction entries generated from the frozen CSV |
| `report.csv`, `report.json` | 14 cases with simulator, variant, expected rejection category, and regression result |
| `{engine}_{variant}_compile.log` | Independent compile log per case |
| `xsim_{variant}_elaborate.log` | XSim elaboration log |
| `{engine}_{variant}_run.log` | Checker log: two `CHECKER_PASS` markers for baseline, matching `CHECKER_FAIL code` and fatal for a faulty variant |

Acceptance requires 14 report rows: two `baseline` rows with `dut_outcome=accepted`, 12 variant rows with `dut_outcome=rejected`, and `regression_status=PASS` throughout. A mismatch writes `regression_status=FAIL` and returns nonzero. `sim_exit` retains the simulator exit code; case classification comes from logged error codes and pass markers. Each reported category corresponds to the log's `CHECKER_FAIL` number.
