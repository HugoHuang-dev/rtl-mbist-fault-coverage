# v3 Evidence and Reproduction

v3 · 09.07–09.10. This directory holds controller integration logs and request-trace checks. From the project root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\sim\run_step03.ps1
```

The script uses Vivado/XSim 2018.3, Icarus Verilog, and Python via `py -3`. Configure simulator locations at the start of the script. XSim and Icarus compile separately under `sim/.build-step03-xsim` and `sim/.build-step03-iverilog`. Each run log is independently compared with the frozen CSV.

| Files | Contents |
| --- | --- |
| `xsim_compile.log`, `xsim_elaborate.log`, `xsim_run.log` | XSim compile, elaborate, two simulation runs, and per-request trace |
| `icarus_compile.log`, `icarus_run.log` | Icarus compile, two runs, and per-request trace |
| `xsim_trace_check.log`, `icarus_trace_check.log` | Independent transaction comparison against the v1 CSV |
| `source_sha256.txt` | SHA-256 of RTL, testbench, scripts, and reference CSV used for this acceptance |

Both run logs contain `MBIST_TB_PASS normal_and_injected_continue`. The fault-free run performs 640 requests (320 reads, 320 writes) in 961 cycles and returns PASS. A one-time read-response perturbation also completes 640 requests, returns FAIL, records one error, and first fails at M2/address 7. Both trace checks report `TRACE_CHECK_PASS`, comparing 1,280 requests per log across the two runs. The testbench cycle count starts at the start-request edge and includes startup and read-response waits.
