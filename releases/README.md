# Board Release Files

The [normal and controlled-perturbation bitstreams](20260926_review/README.md) are the current board-tested builds.

| Mode | Bitstream and probes | Measured result |
| --- | --- | --- |
| Normal LED | [normal_led.bit](20260926_review/normal_led.bit) | DONE/PASS |
| Normal ILA | [normal_ila.bit](20260926_review/normal_ila.bit), [normal_ila.ltx](20260926_review/normal_ila.ltx) | Three PASS runs, 640 requests each |
| Perturbed LED | [fault_led.bit](20260926_review/fault_led.bit) | DONE/FAIL |
| Perturbed ILA | [fault_ila.bit](20260926_review/fault_ila.bit), [fault_ila.ltx](20260926_review/fault_ila.ltx) | Two FAIL runs, first error M2/address 7/FF→FE, 640 requests each |

[File hashes](20260926_review/SHA256.txt) · [Board procedure](../docs/08_board_bringup_steps.md) · [Board evidence](../results/step08/hardware_final/README.md)

## Initial normal build

`mbist_base_64x8.bit`, `mbist_ila_64x8.bit`, and `mbist_ila_64x8.ltx` belong to the [initial capture](../results/step08/hardware/README.md). Their original hashes remain in [SHA256.txt](SHA256.txt).
