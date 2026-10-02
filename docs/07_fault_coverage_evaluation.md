# v7: Fault Coverage Evaluation

v7 · 09.22–09.23. An independent analysis of the v6 records produced per-type coverage and first-detection phase distributions. Machine-readable outputs are indexed in the [v7 evidence](../results/step07/README.md).

## 1. Inputs and independent audit

The [fault manifest](../results/step06/fault_manifest.csv) defines four types × 64 addresses × eight bits, identified by 2,048 unique `fault_id` values. The v6 [raw results](../results/step06/full/raw_results.csv) contain 2,048 XSim and 2,048 Icarus records, or 4,096 tool records in total. The coverage denominator counts 2,048 unique instances, not tool records. The v1 [reference CSV](../specs/march_c_minus_64x8.csv) defines the expected requests.

[`evaluate_fault_coverage.py`](../scripts/evaluate_fault_coverage.py) does not run a simulator. It validates manifest IDs and the configuration set; exactly one result from each tool per instance; activation/detection flags against event and error counts; first-error diagnostics; request count; and cycle count. For every case it checks `CASE_BEGIN`, `FAULT_ACTIVATE`, `CHECKER_PASS`, and `CASE_RESULT` in the raw log against the structured CSV. It then compares the two tools and reconciles with the v6 `summary.json`, `consistency.csv`, and `audit.json`. Deliberately changing one CSV detection phase produces `CSV differs from raw result` and fails the audit.

An instance counts as confirmed detected only if both tool runs are valid, activated, detected, and consistent on key fields. The denominator remains the original 2,048 targets. Unactivated, activated but undetected, invalid, and tool-disagreement cases are reported separately.

```text
Target fault coverage =
  unique fault instances confirmed detected by both tools
  --------------------------------------------------------- × 100%
               planned target fault instances
```

## 2. Coverage by fault type

| Fault type | Targets | Confirmed detected | Target-set coverage | Not activated | Activated, missed | Invalid | Tool disagreement |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SA0 | 512 | 512 | 100.00% | 0 | 0 | 0 | 0 |
| SA1 | 512 | 512 | 100.00% | 0 | 0 | 0 | 0 |
| Rising TF | 512 | 512 | 100.00% | 0 | 0 | 0 | 0 |
| Falling TF | 512 | 512 | 100.00% | 0 | 0 | 0 | 0 |
| Total | 2,048 | 2,048 | 100.00% | 0 | 0 | 0 | 0 |

There were no simulation failures in this campaign. Per-instance decisions are in [`fault_evaluation.csv`](../results/step07/fault_evaluation.csv), and the [exceptions file](../results/step07/exceptions.csv) contains only its header. Per-type totals are in [`coverage_by_type.csv`](../results/step07/coverage_by_type.csv).

## 3. First-detection phase matrix

| Fault type | M0 | M1 | M2 | M3 | M4 | M5 | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SA0 | 0 | 0 | 512 | 0 | 0 | 0 | 512 |
| SA1 | 0 | 512 | 0 | 0 | 0 | 0 | 512 |
| Rising TF | 0 | 0 | 512 | 0 | 0 | 0 | 512 |
| Falling TF | 0 | 0 | 0 | 512 | 0 | 0 | 512 |
| Total | 0 | 512 | 1,024 | 512 | 0 | 0 | 2,048 |

The distribution follows the defined faults and March order. M0 writes zero, exposing SA1; M1's `r0` first detects it. After M1 writes one, M2's `r1` first detects SA0 and Rising TF. After M2 writes zero, M3's `r0` first detects Falling TF. M0 contains no reads. Within each type, all 64 addresses and eight bit positions share the first-detection phase. In all 2,048 cases, the first-error address equals the injected address. See the per-instance [evaluation](../results/step07/fault_evaluation.csv) and [matrix CSV](../results/step07/detection_stage_matrix.csv).

## 4. Test efficiency and cycle definition

For `N=64`, March C− requires `10N=640` operations: 320 reads and 320 writes. M0 and M5 contain 64 each; M1–M4 contain 128 each. Every one of the 4,096 valid tool records reports 640 requests and 960 execution cycles. That is 1.5 cycles/request, approximately 0.667 requests/cycle. The 320 extra cycles accommodate synchronous read-response waits and controller scheduling. At 50 MHz, this simulation interval is 19.2 µs.

The v6 `cycles` counter starts at the falling edge after `start` was sampled and stops when DONE is observed. The v3 testbench includes the start-sampling edge and therefore reports 961 cycles. The one-cycle difference is a counting convention; both tests execute 640 RAM requests. The definition and totals are in [`efficiency.json`](../results/step07/efficiency.json).

## 5. Scope and reproduction

The 100.00% result covers the four defined single-fault models in a simulated 64×8 RAM, across the 2,048 configured instances. Coupling, retention, and physical memory faults were not evaluated. Board results are in the [v9 record](../results/step08/hardware_final/README.md).

From the project root, `py -3 scripts/evaluate_fault_coverage.py` rebuilds the statistics from the v6 evidence without running XSim or Icarus. Outputs are listed in the [v7 index](../results/step07/README.md).
