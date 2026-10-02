# v7 Coverage-Evaluation Outputs

v7 · 09.22–09.23. This directory contains coverage totals, the first-detection phase matrix, and per-instance decisions. From the project root:

```powershell
py -3 scripts/evaluate_fault_coverage.py
```

The script reads the frozen v6 manifest, full per-instance CSV, 64 batch logs, audit records, and v1 reference sequence. It neither starts a simulator nor changes RTL.

| File | Contents |
| --- | --- |
| `fault_evaluation.csv` | One row per unique `fault_id`, including confirmed detection or exception, first phase, and both raw-log paths |
| `coverage_by_type.csv` | Targets, confirmed detections, unactivated, activated/missed, invalid/failed, disagreements, and coverage by type and total |
| `detection_stage_matrix.csv` | Fault type × M0–M5 first-detection counts |
| `exceptions.csv` | Instances without agreement on detection; header only in this run |
| `efficiency.json` | Theoretical operations, measured requests/cycles, and count definition |
| `summary.json` | Machine-readable audit and statistics |
| `evaluation.log` | Final independent evaluation pass marker and totals |

The [method and scope](../../docs/07_fault_coverage_evaluation.md) explain the result: 2,048 unique faults, 4,096 tool records, 2,048 confirmed detections, and zero unactivated, missed, invalid, or disagreement cases. Coverage is counted by unique `fault_id`.
