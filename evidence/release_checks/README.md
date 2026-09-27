# Project Review Records

This directory stores regression results and logs from project packaging. The associated source snapshot is in the [evidence index](../README.md).

| Check | Result | Log |
| --- | --- | --- |
| Icarus controller integration | Two 640-request runs: normal PASS, perturbed response FAIL; `MBIST_TB_PASS` | [`icarus_run.log`](icarus_run.log) |
| XSim controller integration | Same | [compile](xsim_compile.log), [elaborate](xsim_elaborate.log), [run](xsim_run.log) |
| Vivado 2018.3 project open | Part `xc7a35tfgg484-2`, top `board_top`, eight design sources | [`vivado_open_project.log`](vivado_open_project.log) |
| v6 raw-evidence audit | 2,048 fault instances, 4,096 tool records; PASS | [`step06_audit.log`](step06_audit.log) |
| v7 coverage evaluation | 2,048/2,048 confirmed detected; PASS | [`step07_evaluation.log`](step07_evaluation.log) |
| v8 utilization/timing audit | Baseline WNS +14.628 ns, ILA WNS +14.169 ns; PASS | [`step08_offline_audit.log`](step08_offline_audit.log) |
| v9 ILA audit | 1,024 samples, 640 requests, DONE/PASS; PASS | [`step08_ila_audit.log`](step08_ila_audit.log) |
