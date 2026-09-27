# v9 Board Procedure

Target: Da Vinci XC7A35TFGG484-2I, Vivado 2018.3. The normal and controlled-failure [board records](../results/step08/hardware_final/README.md) are archived.

## Connect and program

1. Connect power and JTAG. Confirm the device marking against the target. See the [pin constraints](../fpga/board_pins.xdc).
2. In Vivado 2018.3, open Hardware Manager → Open Target → Auto Connect and confirm `xc7a35t`.
3. Select a bitstream from the [release directory](../releases/20260926_review/README.md). The supplied bitstreams can be programmed without rebuilding.

| Configuration | Bitstream | Debug probes |
| --- | --- | --- |
| Normal LED | `releases/20260926_review/normal_led.bit` | None |
| Normal ILA | `releases/20260926_review/normal_ila.bit` | `normal_ila.ltx` in the same directory |
| Perturbed LED | `releases/20260926_review/fault_led.bit` | None |
| Perturbed ILA | `releases/20260926_review/fault_ila.bit` | `fault_ila.ltx` in the same directory |

Right-click the device, choose Program Device, select the matching file or files, and confirm Programmed. Keep each ILA bitstream paired with its own `.ltx`.

## Normal LED run

1. Program `normal_led.bit`. Press and release RESET; LED0–3 should all be off.
2. Press KEY0 for about 0.1–0.3 s, longer than the approximately 10 ms debounce period. On completion, LED0/DONE and LED1/PASS are on; LED2/FAIL and LED3/BUSY are off.
3. Press KEY0 again without resetting. The test should restart and return PASS.
4. Press RESET to clear the result, then press KEY0 to complete another run.

MBIST runs for roughly 19 µs, so BUSY may not be visible to the eye. Photos: [result cleared](../results/step08/hardware_final/photos/05_normal_reset_clears_result.jpg) and [PASS after reset](../results/step08/hardware_final/photos/06_normal_pass_after_reset.jpg).

## Normal ILA capture

1. Program `normal_ila.bit` with `normal_ila.ltx`; open `hw_ila_1`.
2. Set the capture depth to 1024 samples, Trigger Position to 0, and trigger condition `start_pulse == 1`. Use continuous acquisition without a storage-condition filter.
3. Click Run Trigger, then press KEY0. Save the complete native `.ila` capture and a screenshot of DONE/PASS near the end.
4. Re-arm the trigger and press KEY0 without reset for a second capture. Capture a third run after RESET.
5. At completion check `accepted_count=640, done=1, pass=1, fail=0, error_count=0, busy=0`.

Use Unsigned Decimal for count, phase, and address; Hexadecimal for data; Binary for single-bit signals. Expected phase request counts are 64/128/128/128/128/64.

## Controlled-failure run

1. Program `fault_led.bit`, then press RESET and KEY0. LED0/DONE and LED2/FAIL should be on; LED1/PASS and LED3/BUSY should be off.
2. Program `fault_ila.bit` with `fault_ila.ltx`; configure and arm ILA as above.
3. Inspect samples 279–280. The M2/address 7 read response changes from FF to FE. Then `fail=1`, error count is 1, and first-error fields report phase 2, address 7, expected FF, actual FE.
4. Inspect the end: 640 requests, DONE=1, PASS=0, FAIL=1, BUSY=0. The test continues through M5 after the error.
5. Re-arm without resetting and press KEY0 again. The new run clears old diagnostics and produces the same first error and completion state.

This build changes one read response in wrapper logic to exercise FAIL and diagnostics. Reprogram the normal build to return to a normal demonstration.

## Archive and audit

Save native `.ila` data, completion and first-error screenshots, and photos of the corresponding LED states. Filenames and checksums for the archived set are in the [evidence index](../results/step08/hardware_final/README.md).

From the project root:

```powershell
py -3 scripts/audit_final_hardware.py
$env:MBIST_RUN_ID = '20260926_review_final'
py -3 scripts/audit_board_revision.py
```

[Final utilization and timing](../results/reruns/20260926_review_final/README.md) · [Hardware audit JSON](../results/step08/hardware_final/audit.json)
