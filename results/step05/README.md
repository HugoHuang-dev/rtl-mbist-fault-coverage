# v5 Directed-Simulation Evidence

v5 · 09.14–09.17. This directory contains stand-alone faulty-RAM and MBIST integration tests. From the project root:

```powershell
py -3 .\scripts\run_step05.py
```

The script uses Vivado XSim 2018.3 and Icarus. Each configuration runs in a separate simulator process; intermediate build files are stored in temporary work storage. On Windows, the XSim 2018.3 batch wrapper needs inner quotes around `NAME=VALUE` arguments passed through `-testplusarg`; the script supplies them.

| File | Contents |
| --- | --- |
| `report.csv` | 28 rows: tool, unit/integration suite, configuration, activation, detection, first-error diagnostics, and PASS/FAIL |
| `oracle.hex` | Transaction oracle generated from the v1 CSV for the v4 checker |
| `{tool}_{suite}_compile.log` | Icarus or XSim compile log for each suite |
| `xsim_{suite}_elaborate.log` | XSim elaboration log |
| `{tool}_{suite}_{case}.log` | Raw log per configuration, including activation, checker, and final diagnosis |
| `source_sha256.txt` | Hashes of fault model, reference monitor, scripts, original MBIST RTL, and frozen specification |

All 28 report rows must have `status=PASS`. The seven integrated cases must agree across XSim/Icarus on activation, detection, and first-error fields. Fault-free mode requires `detected=0`; every directed faulty case requires `activated=1` and `detected=1`. Compile, runtime, checker, reference-model, or cross-tool disagreement writes FAIL and returns nonzero.
