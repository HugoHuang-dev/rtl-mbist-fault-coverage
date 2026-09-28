# v8–v9: FPGA Implementation and Board Validation

Target: Da Vinci XC7A35TFGG484-2I, Vivado 2018.3, 50 MHz. The normal and controlled read-response-perturbation configurations were synthesized, implemented, and tested on the board, each with and without ILA. See the [build report](../results/reruns/20260926_review_final/README.md) and [board measurements](../results/step08/hardware_final/README.md).

## Board interface and synchronization

The design reuses `mbist_top` without changing March C− or the 64×8 memory specification. [`board_top.v`](../fpga/board_top.v) connects RESET, KEY0, LEDs, on-chip BRAM, and the ILA request counter. The Vivado part is `xc7a35tfgg484-2` with Industrial operating conditions.

RESET passes through two asynchronous-clear, synchronous-release stages, then one more synchronous register before driving the core. KEY0 passes through a two-stage synchronizer and a 500,000-cycle debounce counter; pressing it produces a start pulse after approximately 10 ms. Both synchronizer chains carry `ASYNC_REG`. Timing exceptions stop at the first-stage D input for the key and at the synchronizer CLR pins for external reset; interstage paths remain timed. LEDs are static status outputs with no external sampling clock. See [`board_pins.xdc`](../fpga/board_pins.xdc).

| Interface | Pin | Function |
| --- | --- | --- |
| `sys_clk` | R4 | 50 MHz clock |
| `sys_rst_n` | U2 | Active low when pressed |
| `key0` | T1 | Start button |
| LED0–3 | R2/R3/V2/Y2 | DONE/PASS/FAIL/BUSY; active high |

## Memory and read timing

The MUT maps to one RAMB18E1 with `DOA_REG=0` and `WRITE_MODE_A=NO_CHANGE`; see the [BRAM configuration report](../results/reruns/20260926_review_final/step08/base/bram_configuration.txt). `DOA_REG=0` disables the optional extra output register but does not make reading asynchronous. A request is sampled on the accepting edge, read data updates afterward, and the controller consumes the valid response on the next rising edge.

The native ILA audit confirms that each read response follows its request by one sample. The final request, response, and DONE appear at samples 959, 960, and 961. A run has 640 requests, with 320 reads and 320 writes. Trigger-to-DONE spans 961 sample intervals; first-request-to-DONE spans 960 clock periods, or 19.2 µs at 50 MHz.

## Resources and timing

| Build | LUTs | FFs | RAMB18 / RAMB36 | WNS / ns | WHS / ns |
| --- | ---: | ---: | ---: | ---: | ---: |
| Controller-only synthesis | 48 | 40 | 0 / 0 | Not implemented | Not implemented |
| Normal, no ILA | 98 | 63 | 1 / 0 | +14.474 | +0.121 |
| Normal, with ILA | 1,930 | 2,934 | 2 / 2 | +13.458 | +0.036 |
| Perturbed, no ILA | 112 | 73 | 1 / 0 | +15.085 | +0.130 |
| Perturbed, with ILA | 1,941 | 2,944 | 2 / 2 | +13.031 | +0.062 |

All four implemented builds have TNS/THS of zero and meet the 20 ns clock constraint. The [report index](../results/reruns/20260926_review_final/README.md) links utilization, timing summary, and CDC reports. Each build directory contains `critical_paths.rpt`; controller-only figures are in the [synthesis report](../results/step08/controller/utilization.rpt).

The non-ILA builds have no CDC Warning/Critical messages. ILA builds report 156 CDC warnings within the debug IP's `dbg_hub`; the board synchronizer chains have informational CDC-3/CDC-9 entries. The [synchronizer check](../results/reruns/20260926_review_final/step08/base/synchronizer_checks.txt) confirms that the three interstage paths remain timed.

## Board results

- Normal without ILA: after KEY0, LED0 and LED1 are on; RESET clears the result LEDs, and a restart returns PASS.
- Normal with ILA: initial start, immediate second start, and start after reset all return PASS with zero errors and 640 requests.
- Perturbed without ILA: after KEY0, LED0 and LED2 indicate DONE/FAIL.
- Perturbed with ILA: two consecutive runs return FAIL with one error, first at M2/address 7, expected FF, actual FE. Both still execute 640 requests.

The board wrapper flips bit 0 of the 72nd read response. It changes neither the controller algorithm nor the BRAM cell contents. FE appears at sample 279, diagnostics latch at 280, and DONE occurs at 961. Sample 0 of the second capture retains the previous result; sample 1 clears the counter, FAIL, and first-error fields before the new run.

The [17 board evidence files](../results/step08/hardware_final/README.md) include photos, screenshots, and five native `.ila` captures. The [hardware audit](../results/step08/hardware_final/audit.json) checks every request, one-cycle read response, DONE timing, error count, first diagnostics, and restart clearing. Capture UUID and probe mapping match the released LTX. Released [bitstreams](../releases/20260926_review/README.md) match implementation outputs byte for byte.

The [board simulation summary](../results/reruns/20260926_review_final/step08/simulation/summary.json) also covers reset during a run and start while busy. See the [reproduction guide](reproduce.md), [board procedure](08_board_bringup_steps.md), and [engineering review](09_engineering_review.md).

## Acceptance

v8 synthesis and implementation and v9 normal/controlled-failure board tests are complete. Board reset evidence covers clearing results after completion and restarting. Reset during a run and start while busy are checked in the dual-tool board simulation linked above. Coverage of the four cell-fault models is evaluated in v7.

The initial v8 reports are indexed in the [implementation results](../results/step08/README.md); Vivado project creation and opening are described in the [project entry](../fpga/vivado/README.md).
