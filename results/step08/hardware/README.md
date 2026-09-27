# v9 Initial Board Evidence

This page archives the first normal capture. [Final board acceptance](../hardware_final/README.md) includes normal and perturbed runs, reset, and restart.

v9 · 2026-09-26. Photos are ordered by capture sequence; `sha256_manifest.txt` lists file hashes. LED states and ILA analysis are described in the [board observation](hardware_observation.md).

## Board photos

| Order | File | Visible content |
| --- | --- | --- |
| 1 | [`01_board_device_and_connections_post_program.jpg`](photos/01_board_device_and_connections_post_program.jpg) | Artix-7 device marking, power, and JTAG connection |
| 2 | [`02_baseline_after_key0_done_pass_leds.jpg`](photos/02_baseline_after_key0_done_pass_leds.jpg) | Non-ILA build after KEY0: LED0/LED1 on, LED2/LED3 off |
| 3 | [`03_ila_after_key0_done_pass_leds.jpg`](photos/03_ila_after_key0_done_pass_leds.jpg) | ILA build after KEY0: DONE/PASS |

## ILA screenshots

| Order | File | Segment |
| --- | --- | --- |
| 1 | [`01_trigger_m0_ascending_write0.png`](ila_waveforms/01_trigger_m0_ascending_write0.png) | `start_pulse`, M0 ascending write-zero |
| 2 | [`02_m1_ascending_read0_write1.png`](ila_waveforms/02_m1_ascending_read0_write1.png) | M1 ascending read-zero/write-one |
| 3 | [`03_m1_to_m2_transition.png`](ila_waveforms/03_m1_to_m2_transition.png) | M1 end to M2 start |
| 4 | [`04_m2_to_m3_direction_reversal.png`](ila_waveforms/04_m2_to_m3_direction_reversal.png) | M2 end and M3 descending start |
| 5 | [`05_m3_to_m4_transition.png`](ila_waveforms/05_m3_to_m4_transition.png) | M3 end to M4 start |
| 6 | [`06_m4_to_m5_final_read.png`](ila_waveforms/06_m4_to_m5_final_read.png) | M4 end to M5 ascending reads |
| 7 | [`07_m5_done_pass_640_requests.png`](ila_waveforms/07_m5_done_pass_640_requests.png) | Final M5 response, 640 requests, DONE/PASS |

The `Value` column reflects the cursor position. Move the cursor to the relevant sample when checking a waveform.

## Native data and audit

- Native Vivado ILA: `ila_capture/2026-09-26_march_c_minus_64x8_full_run.ila`, originally named `ILADATA.ila`. It contains probes, waveform CSV/VCD/WDB, and window configuration.
- [Full CSV](ila_capture/full_run_waveform.csv) and [VCD](ila_capture/full_run_waveform.vcd): losslessly extracted 1,024 samples. Reopen the native `.ila` in Vivado.
- [Audit JSON](ila_audit.json): compares phase, address, operation, write data, and read response of all requests against the [frozen v1 CSV](../../../specs/march_c_minus_64x8.csv); also checks one-cycle response, count, DONE timing, and final state.

From the project root:

```powershell
py -3 scripts/audit_step08_ila.py
```

Expected marker: `STEP08_HARDWARE_ILA_AUDIT_PASS samples=1024 requests=640 reads=320 writes=320 done_sample=961 pass=1 fail=0`. The [final board record](../hardware_final/README.md) covers all subsequent runs.
