# v4: Independent Verification and Negative Tests

v4 · 09.11–09.13. The independent checker accepted baseline runs and caught six categories of controller faults. See the [v4 evidence](../results/step04/README.md).

## Independent transaction checker

[`march_transaction_checker.sv`](../tb/march_transaction_checker.sv) observes only the MBIST top-level RAM request, read-response, start, DONE/PASS/FAIL, and diagnostic ports. It does not read internal FSM, phase, or address-generator registers. Before simulation, [`run_step04.py`](../scripts/run_step04.py) converts the frozen v1 [CSV](../specs/march_c_minus_64x8.csv) to a 640-entry `oracle.hex`. The checker consumes one entry per accepted request instead of duplicating the controller state machine. The v3 offline CSV comparison remains available for trace review.

Checks cover address order, operation type, write data, at most one outstanding read, no diagnostic update before a valid read response, first-error phase/address/expected/actual data, and DONE only after the final response is consumed. A start while busy does not reset checker state; a start after DONE begins a new run. The monitor times out if progress stops.

A six-bit interface can only express addresses 0–63. An invalid progression appears externally as an early wrap, repeated address, or extra request and is rejected. The directed address test reverses direction.

## Negative regression

The script creates each single-change RTL variant in temporary work storage; the original `rtl/` directory is untouched. XSim 2018.3 and Icarus compile and run each variant against the same checker. A compile or elaboration failure is not counted as detection.

| Variant | Introduced fault | Checker response | XSim | Icarus |
| --- | --- | --- | --- | --- |
| Baseline | None; fault-free and one perturbed-response run | Both runs accepted | PASS | PASS |
| `address_order` | Reverse address progression | Code 1: address/order | Detected | Detected |
| `operation_order` | Change an M1 read to a write | Code 2: operation order | Detected | Detected |
| `write_data` | Change M1 write-one to write-zero | Code 3: write data | Detected | Detected |
| `compare_before_valid` | Compare when issuing a read | Code 4: diagnostics changed before a valid response | Detected | Detected |
| `early_done` | Assert DONE after M4 | Code 5: missing M5 requests | Detected | Detected |
| `wrong_first_diagnostic` | Shift first-error address by one | Code 6: first-error diagnostics | Detected | Detected |

Each baseline completes 640 requests. The perturbed baseline flips one read bit at M2/address 7; the checker expects FF and observes FE.

Across both tools, 14 regression cases ran: two baselines passed, and all 12 faulty variants were rejected with the intended category. In this environment a negative run may print `$fatal` yet still exit with code 0. The script therefore requires both `CHECKER_FAIL code` and a fatal message, with no full-run pass marker. In the [report](../results/step04/README.md), `regression_status=PASS` means the regression made the correct decision, while `dut_outcome=rejected` describes the faulty DUT.

The checker detects behavior visible at its ports. The `compare_before_valid` variant changes the error count early and triggers code 4; an internal action without an external effect is outside this check. Each variant was tested separately with the fixed one-cycle RAM response.
