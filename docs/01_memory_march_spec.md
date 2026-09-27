# v1: Memory and March C− Specification

v1 · 09.02–09.03. This specification fixes the 64×8 RAM interface, March C− operation sequence, and 640-request reference trace. The complete trace is in the [specification CSV](../specs/march_c_minus_64x8.csv).

## 1. Memory configuration

| Item | v1 specification |
| --- | --- |
| Capacity | 64 words × 8 bits = 512 bits |
| Address | `ADDR_WIDTH=6`, range 0–63 |
| Data patterns | `0=8'h00`, `1=8'hFF`; whole-byte operations |
| Clock | One 50 MHz clock domain; 20 ns period |
| Port | Single port; at most one read or write accepted per rising edge |
| Read | Synchronous response with valid flag and data; no extra output register |
| Write | Updates the selected byte on the accepting rising edge; no write response |
| Initial contents | Undefined; M0 writes zero to every address before any reads |
| Simultaneous read/write | Not issued by the controller, so read-first/write-first collision behavior is outside the interface |

The 64×8 array is small; actual Block RAM mapping is determined from Vivado synthesis, not from RTL attributes alone. The controller contains no Xilinx-specific RAM primitive.

## 2. Common RAM interface

| Signal | Direction relative to MBIST | Meaning |
| --- | --- | --- |
| `clk` | Input | 50 MHz clock |
| `rst_n` | Input | Active-low synchronous reset sampled on the rising edge; RAM contents are retained |
| `req_valid` | Output | Request valid; address, operation, and write data remain stable until acceptance |
| `req_ready` | Input | Request can be accepted; the v1 RAM adapter normally holds it high |
| `req_write` | Output | 1 = write, 0 = read |
| `req_addr[5:0]` | Output | Word address |
| `req_wdata[7:0]` | Output | Write data, meaningful for a write request |
| `rd_valid` | Input | One-cycle response to an accepted read |
| `rd_data[7:0]` | Input | Read data valid alongside `rd_valid` |

A request is accepted on rising edge `E_k` when `req_valid && req_ready`. For a read, the RAM register updates `rd_valid` and `rd_data` after `E_k`; the controller samples and compares that response at the next rising edge, `E_{k+1}`. Thus the one-cycle read latency is measured from acceptance to consumption. When `rd_valid=0`, `rd_data` may retain its previous value and must not be compared. Writes and idle cycles must not create read responses.

The v1 controller has at most one outstanding read and does not accept a new request on the edge that consumes a read response. For `rX,wY`, it reads and checks one address, writes the new value to that same address, then advances. If a later BRAM implementation enables an additional output register, its adapter must delay `rd_valid` to match the data. The controller relies on the valid flag rather than guessing the phase of a bare `dout`.

Asynchronous board inputs are conditioned before reaching the controller. KEY0 also requires debouncing; see the [FPGA implementation](08_fpga_implementation.md).

### Edge example: M1, address 0

| Time | Event |
| --- | --- |
| Before `E_0` | `req_valid=1, req_write=0, req_addr=0` are stable |
| `E_0` | `r0(0)` is accepted; the RAM synchronously reads address 0 |
| After `E_0`, before `E_1` | `rd_valid=1`; `rd_data` corresponds to address 0 and should be `8'h00` |
| `E_1` | Compare the response; record a mismatch but continue the test |
| `E_2` | Accept `w1(0)` with `req_wdata=8'hFF` |
| `E_3` | The next address, `r0(1)`, may be accepted |

`E_0` and `E_1` are adjacent rising edges. The FSM may insert idle cycles, but request order and read-response alignment must follow this definition.

## 3. Complete March C− sequence

`↑` denotes ascending addresses; `↓` denotes descending addresses. At each address, operations inside parentheses execute in the listed order before moving to the next address. Let `N=64`.

| Phase | Address order | Operations per address | Expected read | Requests |
| --- | --- | --- | --- | ---: |
| M0 | 0,1,…,63 | `w0` | — | 64 |
| M1 | 0,1,…,63 | `r0,w1` | 00 | 128 |
| M2 | 0,1,…,63 | `r1,w0` | FF | 128 |
| M3 | 63,62,…,0 | `r0,w1` | 00 | 128 |
| M4 | 63,62,…,0 | `r1,w0` | FF | 128 |
| M5 | 0,1,…,63 | `r0` | 00 | 64 |

The phase boundaries are:

- M0: `w0(0) … w0(63)`; M1 restarts at address 0.
- M1: `r0(0),w1(0), …,r0(63),w1(63)`; M2 restarts at address 0.
- M2: `r1(0),w0(0), …,r1(63),w0(63)`; M3 starts at address 63.
- M3: `r0(63),w1(63), …,r0(0),w1(0)`; M4 starts at address 63.
- M4: `r1(63),w0(63), …,r1(0),w0(0)`; M5 starts at address 0.
- M5: `r0(0) … r0(63)`; DONE follows comparison of the final response.

No out-of-range address or unintended six-bit wraparound request is allowed. The total is `10N = 640` accepted requests: 320 reads and 320 writes. Clock cycles are counted separately and include start, response waits, idle cycles, and DONE.

Each row of [`march_c_minus_64x8.csv`](../specs/march_c_minus_64x8.csv) represents one RAM request. `seq` runs from 0 to 639; `phase` is M0–M5; `direction` is `up/down`; `address` is decimal; `operation` is `read/write`. Read rows fill `expected_read`; write rows fill `write_data`.

## 4. Control and result semantics

- `start` is a one-cycle pulse sampled in IDLE. A start received while busy is ignored and cannot overwrite the current test.
- Each valid read response is compared with its expected value. The first mismatch latches `first_fail_phase/addr/expected/actual` and sets `fail`, while the test continues through all 640 requests. `error_count` counts failed read comparisons.
- After comparing the final M5 read, `done` is set and `pass = !fail`. Results remain stable until the next accepted start. The new run clears previous results. A nine-bit error counter can represent all 320 possible read mismatches.
- `rst_n` clears controller state and results without clearing RAM contents. Reset during a run aborts it; a subsequent start begins at M0.
- MBIST overwrites the MUT. A RAM shared with application logic would need an explicit ownership and isolation protocol.

## 5. Acceptance

1. The CSV contains 640 requests, with phase lengths 64/128/128/128/128/64 and 320 reads plus 320 writes.
2. An independent shadow RAM can check direction, boundary addresses, read-before-write order, expected reads, and writes. All 320 fault-free reads match.
3. Acceptance at `E_k`, consumption at `E_{k+1}`, `rd_valid` alignment, absence of write responses, and DONE behavior are defined.
4. The board XDC specifies pin R4 for `sys_clk` and a 20 ns period. Device mapping and implemented timing are recorded in the [FPGA report](08_fpga_implementation.md).

Background on RAM inference and timing: AMD [Vivado Memory Inference](https://docs.amd.com/r/en-US/ug901-vivado-synthesis/Memory-Inference-Capabilities) and [7 Series Memory Resources, UG473](https://docs.amd.com/v/u/en-US/ug473_7Series_Memory_Resources). The project uses Vivado 2018.3; its synthesis and simulation reports determine the implemented RAM behavior.
