# v5: Single-Fault RAM Model and Directed Validation

v5 · 09.14–09.17. The faulty RAM passed stand-alone and MBIST-integrated tests. Configurations, logs, and results are in the [v5 evidence](../results/step05/README.md).

## Configuration and fault behavior

The simulation model [`faulty_memory.sv`](../tb/faulty_memory.sv) configures one fault using `fault_type[2:0]`, `fault_addr[5:0]`, and `fault_bit[2:0]`. Type 0 is fault-free; 1–4 select SA0, SA1, rising transition fault (Rising TF), and falling transition fault (Falling TF). Address and bit select one cell in the 64×8 RAM. The fault changes the cell's stored or read value, never the MBIST result or diagnostic ports. Controller RTL is unchanged.

| Type | Cell behavior | Activation event |
| --- | --- | --- |
| SA0 | Selected bit reads and remains 0 | Write 1 to the selected bit |
| SA1 | Selected bit reads and remains 1 | Write 0 to the selected bit |
| Rising TF | A 0→1 write fails; bit stays 0 | Attempt a real 0→1 transition from a known old value |
| Falling TF | A 1→0 write fails; bit stays 1 | Attempt a real 1→0 transition from a known old value |

A transition fault does not activate when the old bit is unknown or the write direction is wrong. `fault_activated` remains set after the first activation; `activation_count` increments for each activation. Reset clears those fields and `rd_valid`, while RAM contents remain. Each fault case starts in a fresh simulation process to avoid state leakage. Invalid or unknown fault types are rejected.

## Verification method

1. The stand-alone [RAM testbench](../tb/tb_faulty_memory_unit.sv) checks prescribed writes, readback, and activation counts without MBIST. It covers neighboring addresses, writes in the opposite direction, repeated triggers, synchronous reads, reset suppression of writes, and retention. SA0/SA1 are also read before the first write to confirm the stuck value.
2. The [MBIST testbench](../tb/tb_step05_mbist.sv) connects the faulty RAM to the original controller. The v4 checker still checks all 640 requests, response consumption, and first-error diagnostics. The [fault reference monitor](../tb/fault_reference_monitor.sv) derives expected read values and activation from external requests and its own reference cell state; it does not inspect the faulty RAM array or controller diagnostics. The testbench independently specifies expected first-error phase/address and error count for each directed case.
3. [`run_step05.py`](../scripts/run_step05.py) runs fault-free mode, four faults at address 7/bit 2, and two boundary cases in both XSim and Icarus. Every case starts a new simulator process. The script checks pass markers, result fields, tool agreement, and raw logs.

## Directed results

All 28 runs passed: two simulators × (seven stand-alone RAM tests + seven MBIST integrations). The independent checker accepted all 640 requests in every integrated case. Faulty cases returned FAIL. Both tools produced:

| Configuration | Activations | Failed read comparisons | First error | Expected / actual |
| --- | ---: | ---: | --- | --- |
| Fault-free, 7/2 | 0 | 0, PASS | — | — |
| SA0, 7/2 | 2 | 2 | M2 / 7 | FF / FB |
| SA1, 7/2 | 3 | 3 | M1 / 7 | 00 / 04 |
| Rising TF, 7/2 | 2 | 2 | M2 / 7 | FF / FB |
| Falling TF, 7/2 | 2 | 2 | M3 / 7 | 00 / 04 |
| SA0, 63/7 | 2 | 2 | M2 / 63 | FF / 7F |
| Falling TF, 0/0 | 2 | 2 | M3 / 0 | 00 / 01 |

SA0 and Rising TF first fail in the same phase, but their cell behavior and activation conditions differ. The stand-alone tests check each definition independently. The full 2,048-instance campaign is documented in [v6](06_automated_fault_campaign.md), with category statistics in [v7](07_fault_coverage_evaluation.md).
