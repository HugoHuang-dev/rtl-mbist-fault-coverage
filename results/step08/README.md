# v8–v9 FPGA Implementation and Board Evidence

Four normal/perturbed builds, with and without ILA, completed 50 MHz implementation and board testing. Five native ILA captures each contain a complete 640-request run: three normal PASS and two controlled FAIL.

| Entry | Contents |
| --- | --- |
| [Final build reports](../reruns/20260926_review_final/README.md) | Utilization, timing, CDC, synchronizer checks, and simulation for four builds |
| [Board measurements](hardware_final/README.md) | Device identification, reset, restart, LEDs, five ILA files, and audits |
| [Bitstreams and probes](../../releases/20260926_review/README.md) | Six release files and SHA-256 hashes |
| [Implementation guide](../../docs/08_fpga_implementation.md) | BRAM mapping, read timing, resources, timing, and board results |
| [Board procedure](../../docs/08_board_bringup_steps.md) | Programming and capture steps |
| [Reproduction guide](../../docs/reproduce.md) | Simulation, implementation, and audit commands |
| [Controller-only utilization](controller/utilization.rpt) | 48 LUTs, 40 FFs, no BRAM |

## Initial build archive

`base/`, `ila/`, and `simulation/` contain the first normal build and simulation. `summary.json` and `source_sha256.txt` retain its audit and fingerprints. The [initial board capture](hardware/README.md) contains original normal-run photos, phase screenshots, ILA data, and transaction audit. Use the table above for current releases and acceptance.
