# 2026-09-26 Software Review

This directory contains independent rerun data; the original `results/step02`–`step08` records remain available.

| Check | Result entry |
| --- | --- |
| RAM unit test | [Icarus](step02/icarus_check.txt), [XSim](step02/xsim_check.txt) |
| Controller integration trace | [Icarus](step03/icarus_check.txt), [XSim](step03/xsim_check.txt) |
| 14-case independent checker regression | [Report](step04/report.json) |
| 28 directed fault tests | [Report](step05/report.csv) |
| Full 2,048-instance campaign | [Raw results](step06/full/raw_results.csv), [audit](step06/audit.json) |
| Independent coverage evaluation | [Summary](step07/summary.json), [phase matrix](step07/detection_stage_matrix.csv) |
| F0123 replay | [Record](step06/replay/F0123/raw_results.csv) |
| Portable ILA copy | [Notes](portable_ila/README.md) |

`step08/` retains the initial build and diagnostic logs from this revision. The final board implementation is under [`20260926_review_final`](../20260926_review_final/README.md). The [engineering review](../../../docs/09_engineering_review.md) records final results.
