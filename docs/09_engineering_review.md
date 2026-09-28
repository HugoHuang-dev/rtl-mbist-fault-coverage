# Engineering Review and Revision · 2026-09-26

This revision improved build portability, synchronizer constraints, and board-level diagnostic testing. The March C− controller and four fault models retain their behavior. Normal and perturbed configurations have been checked on the board, including reset and repeated start.

## Board-level changes

- RESET now uses a two-stage asynchronous-clear, synchronous-release chain followed by one synchronous register for the core. BRAM control is no longer driven directly by asynchronous reset.
- Reset and KEY0 synchronizers carry `ASYNC_REG`. Exceptions cover only the external key to first-stage D and the external reset to synchronizer CLR. The three interstage paths remain timed.
- LEDs are static status outputs with no external sampling clock. The XDC explicitly excludes paths to LED ports; no I/O delays are assigned to them.
- The request counter clears only on an accepted start. A KEY0 pulse while busy no longer clears it.
- `INJECT_READ_FAULT=0` is the normal default. With value 1, the board wrapper flips bit 0 of the 72nd read response. It neither reads internal controller phase nor changes BRAM contents.

An initial CDC check still flagged CDC-7 with the former reset structure. The completed synchronous-release chain reduced external-input findings to informational CDC-3/CDC-9. The first controlled-perturbation connection had the wrong port direction; the independent checker rejected its first read response. After correction, normal and perturbed regressions passed.

## Simulation and fault regression

| Check | Result | Evidence |
| --- | --- | --- |
| RAM unit test | 146 checks per tool; 70 reads, 68 writes | [Icarus](../results/reruns/20260926_engineering_review/step02/icarus_check.txt), [XSim](../results/reruns/20260926_engineering_review/step02/xsim_check.txt) |
| v3 integrated trace | Two runs and 1,280 requests per tool | [Icarus](../results/reruns/20260926_engineering_review/step03/icarus_check.txt), [XSim](../results/reruns/20260926_engineering_review/step03/xsim_check.txt) |
| Independent checker | 14 regression cases passed; 12 faulty variants rejected | [Report](../results/reruns/20260926_engineering_review/step04/report.json) |
| Directed faulty RAM | 28 runs passed | [Report](../results/reruns/20260926_engineering_review/step05/report.csv) |
| Full fault campaign | 2,048 instances, 4,096 tool records; no invalid cases or disagreements | [Raw results](../results/reruns/20260926_engineering_review/step06/full/raw_results.csv), [audit](../results/reruns/20260926_engineering_review/step06/audit.json) |
| Independent statistics | All 2,048 unique instances activated and detected; first phases match raw results | [Summary](../results/reruns/20260926_engineering_review/step07/summary.json) |
| Single-case replay | F0123 agrees with both full-run records | [Results](../results/reruns/20260926_engineering_review/step06/replay/F0123/raw_results.csv) |
| Board-wrapper simulation | Three normal and three perturbed runs per tool; busy-start, in-run reset, and restart passed | [Summary](../results/reruns/20260926_review_final/step08/simulation/summary.json) |

Perturbed runs returned DONE=1, PASS=0, FAIL=1, one error, first at M2/address 7 with expected FF and actual FE, while completing all 640 requests. Normal runs returned PASS. The table records dual-tool simulation; board photos and native captures are indexed below.

For relocation testing, the source was copied to a new directory containing spaces. Both tools reran a 32-instance pilot and normal/perturbed board simulations, with outputs written within the relocated project. See the [relocation summary](../results/reruns/20260926_engineering_review/relocation/summary.json).

## Implementation

Target: `xc7a35tfgg484-2`, Industrial grade, Vivado 2018.3, 20 ns period. TNS and THS are zero in all four builds.

| Build | LUTs | FFs | RAMB18 / RAMB36 | WNS / ns | WHS / ns |
| --- | ---: | ---: | ---: | ---: | ---: |
| Normal, no ILA | 98 | 63 | 1 / 0 | +14.474 | +0.121 |
| Normal, with ILA | 1,930 | 2,934 | 2 / 2 | +13.458 | +0.036 |
| Perturbed, no ILA | 112 | 73 | 1 / 0 | +15.085 | +0.130 |
| Perturbed, with ILA | 1,941 | 2,944 | 2 / 2 | +13.031 | +0.062 |

[Normal timing](../results/reruns/20260926_review_final/step08/base/implemented_timing_summary.rpt) · [Normal ILA timing](../results/reruns/20260926_review_final/step08/ila/timing_summary.rpt) · [Perturbed timing](../results/reruns/20260926_review_final/step08/base_fault/implemented_timing_summary.rpt) · [Perturbed ILA timing](../results/reruns/20260926_review_final/step08/ila_fault/timing_summary.rpt). Synthesis still reports the MUT as RAMB18E1 with `DOA_REG=0`.

The [synchronizer check](../results/reruns/20260926_review_final/step08/base/synchronizer_checks.txt) confirms that interstage paths remain timed; [timing exceptions](../results/reruns/20260926_review_final/step08/base/exceptions.rpt) cover only the specified endpoints. Non-ILA CDC reports have no Warning/Critical entries. ILA builds retain 156 debug-IP CDC warnings in `dbg_hub`; user-logic constraints were not relaxed. The [CDC report](../results/reruns/20260926_review_final/step08/ila/cdc.rpt) and [automated audit](../results/reruns/20260926_review_final/step08/revision_audit.json) retain the classifications.

## Builds and evidence

Simulation and implementation use project-local `.build/<run-id>/`; new records go to `results/reruns/<run-id>/`. Tools are found from environment variables, `toolchain.local.json`, or PATH. The local toolchain file is not versioned. See the [reproduction guide](reproduce.md).

Original ILA files are unchanged. A [portable copy](../results/reruns/20260926_engineering_review/portable_ila/README.md) adjusts only the WCFG database reference; WDB, CSV, VCD, LTX, and DMP are byte-for-byte identical to the originals.

Source headers retain author, project, file, and module. Unverifiable per-file Created/Revised and Editor fields were removed. Earlier source and documentation snapshots are retained separately; current source hashes are in the [SHA-256 manifest](../evidence/current_source_sha256.txt).

## Board acceptance

Software regression, full fault campaign, timing analysis for all four bitstreams, and board testing are complete. The [17 board evidence files](../results/step08/hardware_final/README.md) cover device identification, reset clearing, normal/perturbed LEDs, three normal native ILA runs, and two perturbed runs. Every capture passed a 640-request comparison. Normal runs returned PASS; perturbed runs returned FAIL with M2/address 7/FF→FE. Both modes cleared previous state on the second run.

Software regression, the full fault campaign, and single-case replay records are indexed in the [software review results](../results/reruns/20260926_engineering_review/README.md).
