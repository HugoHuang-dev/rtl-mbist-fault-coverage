# v3: March C− Controller RTL and Integration Test

v3 · 09.07–09.10. With the fault-free RAM attached, the controller completed the March C− sequence with PASS and 640 accepted requests. Commands, traces, and logs are in the [v3 evidence](../results/step03/README.md).

## Module structure

| Module | Responsibility |
| --- | --- |
| `march_controller.v` | IDLE, request, read-response wait, read-before-write, and DONE states; M0–M5 transitions and address boundaries |
| `address_generator.v` | Load each phase's first address and increment or decrement |
| `data_generator.v` | Generate write data and expected read data (00/FF) |
| `memory_interface.v` | Connect FSM requests to the frozen RAM request/response interface; accept on `req_ready` |
| `response_checker.v` | Compare only in the wait state when `rd_valid` is asserted; retain first-error fields and error count |
| `mbist_top.v` | Connect the modules and expose RAM, BUSY/DONE/PASS/FAIL, and diagnostics |

R1 informed the module split, while the handshake and timing follow this project's interface. A mismatch does not terminate the test. The controller permits at most one outstanding read: a request is accepted at `E_k`, RAM outputs update after that edge, and the controller compares at `E_{k+1}`. DONE follows comparison of the M5/address 63 read. `pass = done && !fail`, so an error on the last read cannot produce PASS.

The v4 transaction checker infers phases from external requests and the frozen CSV without inspecting the controller FSM.

## Acceptance results

XSim 2018.3 and Icarus Verilog 11.0 independently compiled and ran the same RTL/testbench, both exiting with code 0. Each simulator ran:

| Scenario | Requests | Read / write | Cycles | Result |
| --- | ---: | ---: | ---: | --- |
| Fault-free RAM | 640 | 320 / 320 | 961 | DONE=1, PASS=1, FAIL=0, errors=0 |
| One perturbed read response | 640 | 320 / 320 | 961 | DONE=1, PASS=0, FAIL=1, errors=1; first error M2/address 7, expected FF, actual FE |

This version's integration testbench is white-box: it reads `dut.u_controller.phase` and checks phase, address, operation, and write data. Python also compares both simulator traces against all 640 rows of the v1 [reference CSV](../specs/march_c_minus_64x8.csv); both comparisons passed. A start pulse while busy did not restart the test, the DONE result remained stable, and a new start from DONE was accepted. The one-time perturbation exercises comparison and continued execution. Faulty RAM and coverage results are documented in v5–v7.

[Exact commands and original logs](../results/step03/README.md)
