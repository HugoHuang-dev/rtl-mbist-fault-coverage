# Final Board Build · 2026-09-26

Normal and perturbed dual-tool simulations passed. All four bitstreams meet 50 MHz setup and hold timing. Both modes passed board tests; [photos and five native ILA captures](../../step08/hardware_final/README.md) are archived, and the combined audit passed.

| Build | Utilization | Timing | CDC |
| --- | --- | --- | --- |
| Normal LED | [Report](step08/base/implemented_utilization.rpt) | [Report](step08/base/implemented_timing_summary.rpt) | [Report](step08/base/cdc.rpt) |
| Normal ILA | [Report](step08/ila/utilization.rpt) | [Report](step08/ila/timing_summary.rpt) | [Report](step08/ila/cdc.rpt) |
| Perturbed LED | [Report](step08/base_fault/implemented_utilization.rpt) | [Report](step08/base_fault/implemented_timing_summary.rpt) | [Report](step08/base_fault/cdc.rpt) |
| Perturbed ILA | [Report](step08/ila_fault/utilization.rpt) | [Report](step08/ila_fault/timing_summary.rpt) | [Report](step08/ila_fault/cdc.rpt) |

[Board-wrapper simulation](step08/simulation/summary.json) · [Implementation audit](step08/revision_audit.json) · [Bitstreams and probes](../../../releases/20260926_review/README.md). Build commands and tool versions are under `step08/build_logs_normal/` and `build_logs_fault/`.
