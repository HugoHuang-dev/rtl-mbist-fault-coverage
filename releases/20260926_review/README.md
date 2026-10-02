# Board Release

The normal and perturbed LED/ILA builds passed board tests, dual-simulator verification, and 50 MHz implementation checks. See the [board results and native captures](../../results/step08/hardware_final/README.md).

| Files | Mode | Observed LED0–3 |
| --- | --- | --- |
| `normal_led.bit` | Normal BRAM, no ILA | DONE/PASS on; FAIL/BUSY off |
| `normal_ila.bit`, `normal_ila.ltx` | Normal BRAM with ILA | Same |
| `fault_led.bit` | One-time read-response perturbation, no ILA | DONE/FAIL on; PASS/BUSY off |
| `fault_ila.bit`, `fault_ila.ltx` | One-time read-response perturbation with ILA | Same |

The perturbed build flips bit 0 of the 72nd read response in each run, producing M2/address 7/FF→FE. Board tests measured one error and all 640 requests. This mode exercises the logic diagnostic path.

Keep each `.bit/.ltx` pair together. See the [implementation/simulation audit](../../results/reruns/20260926_review_final/step08/revision_audit.json), and the [engineering review](../../docs/09_engineering_review.md). The initial board build remains in the parent directory.
