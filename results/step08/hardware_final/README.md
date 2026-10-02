# v9 Board Measurements and Final Acceptance

Da Vinci XC7A35TFGG484-2I, Vivado 2018.3, 50 MHz, 64×8 on-chip BRAM. Both normal and controlled read-response-perturbation builds passed board tests. Screenshots were captured on 2026-09-26 and indexed on 2026-09-27.

## Acceptance results

| Test | Result | Evidence |
| --- | --- | --- |
| Device identification and programming | `xc7a35t`, Programmed | [Hardware Manager](screenshots/01_hardware_manager_programmed.png) |
| Normal LEDs | DONE/PASS on; FAIL/BUSY off | [First run](photos/04_normal_first_pass.jpg) |
| Reset clears results | All four result LEDs off after RESET | [Reset state](photos/03_normal_after_reset.jpg), [reset after completion](photos/05_normal_reset_clears_result.jpg) |
| Restart after reset | Completes and returns PASS | [LEDs](photos/06_normal_pass_after_reset.jpg), [native ILA](captures/11_normal_ila_after_reset.ila) |
| Consecutive normal starts | Both rounds complete 640 requests and return PASS | [Round 1](captures/08_normal_ila_round1.ila), [round 2](captures/10_normal_ila_round2.ila) |
| Perturbed LEDs | DONE/FAIL on; PASS/BUSY off | [LED build](photos/12_fault_led_done_fail.jpg), [ILA build](photos/17_fault_ila_board_leds.jpg) |
| Perturbed diagnosis and restart | Both rounds complete, one error, first at M2/address 7/FF→FE | [First-error screenshot](screenshots/13_fault_ila_first_error.png), [round 1](captures/15_fault_ila_round1.ila), [round 2](captures/16_fault_ila_round2.ila) |

## Native ILA audit

[`audit_final_hardware.py`](../../../scripts/audit_final_hardware.py) reads five native captures and compares every transaction with the frozen v1 sequence. Each has 1,024 samples and 640 requests (320 reads, 320 writes); M0–M5 counts are 64/128/128/128/128/64. Every read has a valid response one sample later. The final request, response, and DONE appear at samples 959, 960, and 961.

All three normal rounds return PASS with zero errors. In both perturbed rounds, FF→FE appears at sample 279; FAIL and first-error fields latch at sample 280; the controller then runs to DONE with one error. Sample 0 of a second-round capture retains the previous result. Sample 1 clears the count and diagnostics before an independent new run.

| Native file | Mode | Requests | DONE sample | PASS | FAIL | Errors |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 08_normal_ila_round1.ila | Normal round 1 | 640 | 961 | 1 | 0 | 0 |
| 10_normal_ila_round2.ila | Normal round 2 | 640 | 961 | 1 | 0 | 0 |
| 11_normal_ila_after_reset.ila | Normal restart after reset | 640 | 961 | 1 | 0 | 0 |
| 15_fault_ila_round1.ila | Perturbed round 1 | 640 | 961 | 0 | 1 | 1 |
| 16_fault_ila_round2.ila | Perturbed round 2 | 640 | 961 | 0 | 1 | 1 |

[Full audit JSON](audit.json) · [Summary CSV](capture_summary.csv) · [Auditor negative test](audit_self_check.json). `exports/` contains CSV/VCD extracted byte for byte from the native files. Capture core UUID, 18 probe ports, widths, and names match their released LTX files. Released bitstreams are byte-identical to implementation outputs.

## Utilization and timing

The [final implementation reports](../../reruns/20260926_review_final/README.md) cover normal/perturbed builds with and without ILA. All meet the 20 ns clock constraint; WNS values are +14.474, +13.458, +15.085, and +13.031 ns, respectively, with TNS/THS of zero. The [combined implementation/hardware audit](../../reruns/20260926_review_final/step08/revision_audit.json) passed. See [programming files](../../../releases/20260926_review/README.md).

## Evidence file index

Photos, screenshots, and native ILA files retain their original content and filenames.

| File | Contents |
| --- | --- |
| [01_hardware_manager_programmed.png](screenshots/01_hardware_manager_programmed.png) | Hardware Manager: XC7A35T programmed with normal LED build |
| [02_board_connections.jpg](photos/02_board_connections.jpg) | Device marking, power, and JTAG |
| [03_normal_after_reset.jpg](photos/03_normal_after_reset.jpg) | Normal reset: LED0–3 off |
| [04_normal_first_pass.jpg](photos/04_normal_first_pass.jpg) | First normal start: DONE/PASS |
| [05_normal_reset_clears_result.jpg](photos/05_normal_reset_clears_result.jpg) | RESET after completion: result LEDs off |
| [06_normal_pass_after_reset.jpg](photos/06_normal_pass_after_reset.jpg) | Start after reset: DONE/PASS |
| [07_normal_ila_round1_done.png](screenshots/07_normal_ila_round1_done.png) | Normal ILA round 1 at completion |
| [08_normal_ila_round1.ila](captures/08_normal_ila_round1.ila) | Native normal ILA round 1 |
| [09_normal_ila_round2_done.png](screenshots/09_normal_ila_round2_done.png) | Normal ILA round 2 at completion |
| [10_normal_ila_round2.ila](captures/10_normal_ila_round2.ila) | Native normal ILA round 2, no reset |
| [11_normal_ila_after_reset.ila](captures/11_normal_ila_after_reset.ila) | Native normal restart after reset |
| [12_fault_led_done_fail.jpg](photos/12_fault_led_done_fail.jpg) | Perturbed LED build: DONE/FAIL |
| [13_fault_ila_first_error.png](screenshots/13_fault_ila_first_error.png) | First perturbed diagnosis: M2/address 7/FF→FE |
| [14_fault_ila_done_640.png](screenshots/14_fault_ila_done_640.png) | Perturbed completion: 640 requests, DONE/FAIL, one error |
| [15_fault_ila_round1.ila](captures/15_fault_ila_round1.ila) | Native perturbed ILA round 1 |
| [16_fault_ila_round2.ila](captures/16_fault_ila_round2.ila) | Native perturbed ILA round 2, no reset |
| [17_fault_ila_board_leds.jpg](photos/17_fault_ila_board_leds.jpg) | Perturbed ILA build: DONE/FAIL |

[`file_manifest.json`](file_manifest.json) lists the 17 original files. From the project root:

```powershell
py -3 scripts/audit_final_hardware.py --self-test
$env:MBIST_RUN_ID = '20260926_review_final'
py -3 scripts/audit_board_revision.py
```

The controlled fault flips bit 0 of one read response in board wrapper logic; it does not alter BRAM cells. Board reset evidence covers clearing results and restart. In-run reset and busy-start behavior were checked by board-wrapper simulation. Four cell-fault model coverage results are in v7.
