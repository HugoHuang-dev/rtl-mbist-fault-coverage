# v6 Auditable Campaign Records

v6 · 09.18–09.21. This directory retains the 2,048-instance manifest, dual-tool results, raw logs, and audit. From the project root in PowerShell:

```powershell
$env:MBIST_RUN_ID = 'fault_check_01'
py -3 scripts/run_step06.py --mode all
$env:MBIST_AUDIT_RUN_ID = $env:MBIST_RUN_ID
py -3 scripts/audit_step06.py
py -3 scripts/run_step06.py --mode replay --fault-id F1023 --tool both
```

`--mode all` runs the 32-instance pilot followed by the full 2,048 instances in XSim 2018.3 and Icarus. Use `--mode pilot` or `--mode full` separately if needed; default `--chunk-size` is 64. Each simulator is compiled once; `campaign.hex`, `selection.hex`, and testbench configuration select cases without changing RTL. Replay accepts any ID from `F0000` through `F2047` and compares its fields with the existing full run.

| File or directory | Contents |
| --- | --- |
| `fault_manifest.csv` | 2,048 unique target IDs, types, addresses, and bit positions |
| `pilot_manifest.csv` | 32 pilot cases spanning different addresses and bits |
| `campaign.hex`, `oracle.hex` | Simulation configuration and independent transaction oracle from v1 |
| `pilot/`, `full/` | Per-instance CSV/JSONL and cross-tool `consistency.csv`, `summary.json` |
| `raw/pilot/`, `raw/full/` | Raw simulator logs by tool and batch, referenced by each CSV row's `raw_log` |
| `build/` | Icarus compilation and XSim compilation/elaboration logs |
| `audit.json` | Manifest, structured-result, raw-log, and tool-pair audit |
| `replay/F1023/`, `raw/replay/F1023/` | Example single-case replay results and raw logs |

Each `raw_results.csv` or `raw_results.jsonl` row contains `fault_id`, `fault_type`, `fault_addr`, `fault_bit`, `activated`, `detected`, `first_fail_addr`, `first_fail_stage`, `request_count`, and `simulation_status`. Additional fields record activation/error counts, first-failure expected/actual values, cycles, outcome, reason, attempt count, and raw-log path. Records with `simulation_status=invalid` retain a `reason`. `not_activated` denotes a valid run without fault activation; `activated_escape` denotes a valid run in which the fault activated but was not detected. They are counted separately and remain in the target set. `detected_without_activation` is invalid.

The pilot's 64 tool records and the full campaign's 4,096 records are valid. All 2,048 tool pairs agree field by field; every full record is `activated_detected` with 640 requests. Coverage is calculated separately in v7. Since one batch log covers several instances, several rows may cite the same log. Use `CASE_BEGIN id=` and `CASE_RESULT id=` to locate an instance.

New runs are written to `results/reruns/<run-id>/step06/`; this directory retains the original campaign. See the [reproduction guide](../../docs/reproduce.md) for tool configuration.
