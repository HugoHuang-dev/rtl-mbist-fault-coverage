# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : create_board_project.tcl
# Module  : create_board_project
# -----------------------------------------------------------------------------
# Vivado 2018.3 batch build of the DaVinci 64x8 MBIST board system.
# The source project and all evidence live under the project root.
source [file join [file dirname [info script]] build_paths.tcl]
set evidence [file join $result_root base$variant]
file mkdir $evidence
set part xc7a35tfgg484-2

create_project -force mbist_board $project_dir -part $part
set_property target_language Verilog [current_project]
set sources {}
foreach name {address_generator.v data_generator.v memory_interface.v response_checker.v march_controller.v mbist_top.v single_port_sync_ram.v} {
    lappend sources [file join $root rtl $name]
}
lappend sources [file join $root fpga board_top.v]
add_files -norecurse $sources
add_files -fileset constrs_1 -norecurse [file join $root fpga board_pins.xdc]
add_files -fileset utils_1 -norecurse [file join $root fpga set_industrial.tcl]
set_property top board_top [get_filesets sources_1]
set_property generic INJECT_READ_FAULT=$inject [get_filesets sources_1]
set_property STEPS.SYNTH_DESIGN.ARGS.FLATTEN_HIERARCHY none [get_runs synth_1]
set_property STEPS.OPT_DESIGN.TCL.PRE [file join $root fpga set_industrial.tcl] [get_runs impl_1]
update_compile_order -fileset sources_1

launch_runs synth_1 -jobs 2
wait_on_run synth_1
puts "SYNTH_STATUS [get_property STATUS [get_runs synth_1]]"
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {
    error "Board synthesis did not complete"
}
open_run synth_1
set_operating_conditions -grade Industrial
report_operating_conditions -grade -file [file join $evidence synthesized_operating_conditions.rpt]
report_utilization -file [file join $evidence synthesized_utilization.rpt]
report_timing_summary -file [file join $evidence synthesized_timing_summary.rpt]
set ram_cells [get_cells -hier -filter {REF_NAME == RAMB18E1 || REF_NAME == RAMB36E1}]
if {[llength $ram_cells] != 1} {
    error "Expected one inferred BRAM in full board design, found [llength $ram_cells]"
}
set ram [lindex $ram_cells 0]
set primitive [get_property REF_NAME $ram]
set doa_reg [get_property DOA_REG $ram]
set write_mode [get_property WRITE_MODE_A $ram]
puts "BOARD_BRAM primitive=$primitive DOA_REG=$doa_reg WRITE_MODE_A=$write_mode"
if {$primitive ne "RAMB18E1" || $doa_reg ne "0"} {
    error "BRAM primitive or output pipeline changed from the verified RAM interface"
}
set fp [open [file join $evidence bram_configuration.txt] w]
puts $fp "cell=$ram\nprimitive=$primitive\nDOA_REG=$doa_reg\nWRITE_MODE_A=$write_mode"
close $fp
close_design

launch_runs impl_1 -to_step write_bitstream -jobs 2
wait_on_run impl_1
puts "IMPL_STATUS [get_property STATUS [get_runs impl_1]]"
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {
    error "Board implementation did not complete"
}
open_run impl_1
set_operating_conditions -grade Industrial
report_operating_conditions -grade -file [file join $evidence implemented_operating_conditions.rpt]
report_utilization -file [file join $evidence implemented_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $evidence implemented_timing_summary.rpt]
report_timing -delay_type max -max_paths 10 -sort_by group -file [file join $evidence critical_paths.rpt]
source [file join $root fpga check_board_timing.tcl]
write_checkpoint -force [file join $evidence board_routed.dcp]
set bitstream [file join $project_dir mbist_board.runs impl_1 board_top.bit]
if {![file exists $bitstream]} {
    error "Bitstream missing: $bitstream"
}
file copy -force $bitstream [file join $evidence board_top.bit]
puts "STEP08_BASE_BUILD_PASS part=$part primitive=$primitive DOA_REG=$doa_reg bitstream=[file join $evidence board_top.bit]"
