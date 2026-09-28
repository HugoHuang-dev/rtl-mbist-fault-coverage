# V10 Vivado RTL Structure and Image Evidence

Project entry: [`asic/vivado/mbist_asic_v10/mbist_asic_v10.xpr`](../../../../asic/vivado/mbist_asic_v10/mbist_asic_v10.xpr). Vivado 2018.3 and target `xc7a35tfgg484-2` provide an RTL elaboration view. The top is `mbist_asic_top`, and sources match V10's [`asic_rtl.f`](../../../../asic/rtl/asic_rtl.f): seven controller RTL files, excluding SRAM, board top, LEDs, ILA, and FPGA IP. The device selection is required to open and elaborate RTL in Vivado; this project's FPGA resources, timing, and schematic are not Nangate45 synthesis results.

[`elaboration.log`](elaboration.log) contains `V10_VIEW_ELABORATION_PASS`; Vivado 2018.3 reports `0 Warnings, 0 Critical Warnings and 0 Errors`. [`audit.json`](audit.json) identifies the historical project and original source bytes; the original XPR is in the [source snapshot](../../../../evidence/asic_integration/source_snapshot.zip). The current project was regenerated and passed [elaboration and source checks](../projectiii_vivado/audit.json). The first batch attempt used `open_elaborated_design`, which produced `invalid command name` in Vivado 2018.3; the error is retained in [`create_project.log`](create_project.log). Switching to `synth_design -rtl -name rtl_1` succeeded. The scripts are [`create_v10_vivado_view.tcl`](../../../../asic/scripts/create_v10_vivado_view.tcl) and [`validate_v10_vivado_view.tcl`](../../../../asic/scripts/validate_v10_vivado_view.tcl).

The three [original images](#screenshots) show the ASIC top's 67 I/O bits and `u_mbist` pass-through ports, the five modules and control/data connections inside `u_mbist`, and Vivado Sources/Hierarchy alongside `mbist_top.v` source. Images were not cropped or redrawn; SHA-256 and original pixel dimensions are recorded in [`audit.json`](audit.json). To reproduce the view, open the `.xpr` in Vivado GUI, then select Flow Navigator → RTL Analysis → Open Elaborated Design and inspect Hierarchy and Schematic.

The V10 Mermaid diagram describes the architecture and ASIC boundary. The Vivado elaborated schematic shows structure generated from RTL. Independent checker regression and V12 netlist tests verify functional behavior. The Vivado FPGA device selection is not used in ASIC area or timing analysis.

## Screenshots

- [`01_asic_top_interface_schematic.png`](screenshots/01_asic_top_interface_schematic.png): `mbist_asic_top`'s 67 I/O bits and `u_mbist` pass-through instance; SRAM appears only through external request/response ports.
- [`02_mbist_controller_rtl_schematic.png`](screenshots/02_mbist_controller_rtl_schematic.png): actual RTL connections among March control, address/data generation, memory interface, and response checking within `mbist_top`.
- [`03_elaborated_hierarchy_and_rtl.png`](screenshots/03_elaborated_hierarchy_and_rtl.png): Vivado hierarchy and `mbist_top.v` port-connection source in the same view.
