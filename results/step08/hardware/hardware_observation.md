# v9 Board Observation · 2026-09-26

The Da Vinci Artix-7 board ran the baseline and ILA bitstreams. Photos record connections and LEDs; native ILA data verifies the actual March C− request sequence. See the [evidence index](README.md).

| Check | Result and evidence |
| --- | --- |
| Board and connections | [Photo](photos/01_board_device_and_connections_post_program.jpg) shows Artix-7 marking, power, and JTAG; build target `xc7a35tfgg484-2` with Industrial operating grade |
| Baseline | After KEY0, [LED photo](photos/02_baseline_after_key0_done_pass_leds.jpg) shows LED0/DONE and LED1/PASS on, LED2/FAIL and LED3/BUSY off |
| ILA build | [LED photo](photos/03_ila_after_key0_done_pass_leds.jpg) shows the same result; native file: `ila_capture/2026-09-26_march_c_minus_64x8_full_run.ila` |
| Requests | [Exported waveform](ila_capture/full_run_waveform.csv) matches all 640 v1 requests; phase counts 64/128/128/128/128/64, with 320 reads and 320 writes |
| Completion | Final M5/address 63 request at sample 959, read response at 960, first DONE/PASS at 961; FAIL=0, BUSY=0, errors=0 through sample 1023 |
| Independent audit | [Result](ila_audit.json): `STEP08_HARDWARE_ILA_AUDIT_PASS`; command: `py -3 scripts/audit_step08_ila.py` |

This page archives the first normal-BRAM PASS run. The [final board acceptance](../hardware_final/README.md) includes normal/perturbed, reset, and restart evidence.
