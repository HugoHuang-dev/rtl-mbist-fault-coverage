# v2: Single-Port Synchronous RAM Verification

v2 · 09.04–09.06. The RAM passed an independent testbench, and Vivado synthesis confirmed its Block RAM mapping. Commands and logs are in the [v2 evidence](../results/step02/README.md).

## Design and tools

- RTL: [`single_port_sync_ram.v`](../rtl/single_port_sync_ram.v). Default configuration: 64×8, six-bit address, one 50 MHz clock. The `ram_style="block"` attribute requests Block RAM inference.
- Testbench: [`tb_single_port_sync_ram.sv`](../tb/tb_single_port_sync_ram.sv). Its shadow RAM updates only from accepted writes; it does not inspect the DUT array or instantiate MBIST.
- Primary simulator: Vivado XSim 2018.3. Cross-check: Icarus Verilog 11.0. Each compiles and runs independently from the same source.
- RAM-only synthesis: Vivado 2018.3. The board package is marked `XC7A35TFGG484-2I`. The 7 Series target uses `xc7a35tfgg484-2` for device, package, and speed grade; `set_operating_conditions -grade Industrial` selects the industrial temperature grade after opening the synthesized design. Temperature grade determines subsequent operating-condition analysis; RAM mapping depends on the selected device, package, and speed grade. AMD [UG899](https://docs.amd.com/api/khub/documents/kobHePaH8nZX6Ubq4SnCaQ/content) documents this separate setting.

## Read-response timing

Outside reset, `req_ready=1`; it is 0 during reset. A request is accepted at rising edge `E_k` when `req_valid && req_ready`. A write updates memory at that edge without asserting `rd_valid`. A read updates `rd_data/rd_valid` by nonblocking assignment after `E_k`; a synchronous consumer samples the response at `E_{k+1}`. Write, idle, and reset cycles do not produce a new read response. `rd_data` retains its last value. Reset clears response validity but neither initializes nor erases RAM contents.

The testbench checks three observation points:

1. After changing the request on a falling edge and waiting 1 ns before the next rising edge, it confirms that `rd_data/rd_valid` have not changed asynchronously.
2. One nanosecond after the accepting edge `E_k`, after DUT nonblocking assignments settle, it checks `rd_valid` and data against the shadow RAM. Write, idle, and reset cycles must have no spurious response.
3. At the active region of `E_{k+1}`, before that edge's NBA update, it checks the preceding response again, matching what another synchronous module would sample.

Stimulus changes only on falling edges, so it cannot race the DUT on a rising edge. Continuous reads may keep `rd_valid` high; the testbench checks each response in order.

Vivado synthesis reports one `RAMB18E1`, `DOA_REG=0`, and `WRITE_MODE_A=NO_CHANGE`. With `DOA_REG=0`, the primitive's optional output register is disabled. Read data becomes available after the read clock edge and is consumed on the following edge; enabling the output register would add a cycle. See AMD [UG473](https://docs.amd.com/v/u/en-US/ug473_7Series_Memory_Resources). `NO_CHANGE` is consistent with the RTL holding `rd_data` on writes.

## Tested scenarios

| Scenario | Check | XSim | Icarus |
| --- | --- | --- | --- |
| Address boundaries and sparse access | Write and read different values at addresses 0 and 63 without aliasing | PASS | PASS |
| Consecutive writes and reads | Write distinct data across 64 addresses and compare each read with shadow RAM | PASS | PASS |
| Alternating read/write | Read an address immediately after writing; cross from address 63 to 0 | PASS | PASS |
| Idle and write cycles | `rd_valid=0`; `rd_data` holds; no false response | PASS | PASS |
| Synchronous read | No early change on falling-edge address updates; response after `E_k`, sampled at `E_{k+1}` | PASS | PASS |
| Reset | Clear response validity, suppress writes on reset edge, retain and read back RAM contents | PASS | PASS |
| Timeout | Abort a stalled test | Configured | Configured |

Both simulator runs exited with code 0 and printed four `CASE_PASS` markers plus `RAM_TB_PASS checks=146 reads=70 writes=68`. Synthesis exited with code 0, no errors, no critical warnings, and no warnings. The [evidence index](../results/step02/README.md) contains the original logs and exact commands.

This test used the 64×8 configuration with `DOA_REG=0`. The six-bit address spans 0–63. Because the RAM is uninitialized, read comparisons use addresses written earlier in the test. Other capacities, an enabled output register, gate-level timing, and abnormal clock conditions were not tested.
