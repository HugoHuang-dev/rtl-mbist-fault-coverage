# V10 Architecture Adaptation Verification Records

Initial run date: 2026-09-27. These directories were created by [`run_v10.py`](../../../asic/scripts/run_v10.py). Each contains `report.json`, `oracle.hex`, and compilation, XSim elaboration, and per-case run logs for the original and ASIC top levels.

| Run | Tool | Summary | Result |
| --- | --- | --- | --- |
| `20260927_icarus_v10` | Icarus Verilog 11.0 (devel) | [Report](20260927_icarus_v10/report.json) | 16/16 scenarios PASS; [stand-alone ASIC compile](20260927_icarus_v10/asic_top_compile.log) exited 0 |
| `20260927_xsim_v10` | Vivado XSim 2018.3 | [Report](20260927_xsim_v10/report.json) | 16/16 scenarios PASS |
| `vivado_view` | Vivado RTL Elaboration 2018.3 | [Project and image audit](vivado_view/audit.json) | Seven V10 RTL files, top `mbist_asic_top`, 0 elaboration warnings/errors; three original screenshots archived |

The 16 scenarios per tool comprise eight with the original top and eight with the ASIC top. The sequence scenario itself executes two runs: normal, then one read-response perturbation. The seven fault scenarios cover fault-free mode, four representative single faults, and two boundary addresses. The [cross-tool check](cross_tool_audit.json) confirms agreement on all 16 external results. Each report's `checker` field contains request, cycle, and error counts; `fault` contains activation, detection, and first-failure phase/address/expected/observed values.

To reproduce, run `py -3 asic/scripts/run_v10.py --tool both --run-id rtl_check_01` from the project root. The runner uses a new result directory, retains original `results/stepXX` records, and compares external behavior between tops and simulators. The stand-alone design file list is [`asic_rtl.f`](../../../asic/rtl/asic_rtl.f). Architecture and interface details are in [`docs/10_asic_architecture.md`](../../../docs/10_asic_architecture.md).

V10's [stand-alone Vivado RTL project](../../../asic/vivado/mbist_asic_v10/mbist_asic_v10.xpr) and three [original screenshots](vivado_view/README.md) show ASIC port pass-through, connections between the five controller submodules, and the hierarchy alongside `mbist_top.v` source. The [elaboration log](vivado_view/elaboration.log) and [image audit](vivado_view/audit.json) are retained. Vivado views document RTL structure; ASIC standard-cell mapping and timing are covered in V11–V13.

On 2026-09-28, current source with consistent file headers passed all [32 dual-simulator regression scenarios](20260928_source_check/report.json). Per-case logs are retained in that run directory.
