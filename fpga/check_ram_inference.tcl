# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : check_ram_inference.tcl
# Module  : check_ram_inference
# -----------------------------------------------------------------------------
# Vivado batch check for Step 2 RAM-only synthesis.
# Usage (from a build directory):
#   vivado -mode batch -source <project>/fpga/check_ram_inference.tcl \
#          -tclargs XC7A35TFGG484-2I
# 7-series Vivado selects device/package/speed through get_parts and sets the
# industrial temperature grade separately with set_operating_conditions.
if {[llength $argv] != 1} {
    error "Provide the board marking XC7A35TFGG484-2I"
}
set board_marking [string toupper [lindex $argv 0]]
if {$board_marking ne "XC7A35TFGG484-2I"} {
    error "This check is defined for board marking XC7A35TFGG484-2I only"
}
set target_part xc7a35tfgg484-2
if {[llength [get_parts -quiet $target_part]] != 1} {
    error "Target part $target_part is not available in this Vivado installation"
}
set project_root [file normalize [file join [file dirname [info script]] ..]]
read_verilog [file join $project_root rtl single_port_sync_ram.v]
synth_design -top single_port_sync_ram -part $target_part -no_iobuf
set_operating_conditions -grade Industrial
report_operating_conditions -grade

set ram_cells [get_cells -hier -filter {REF_NAME == RAMB18E1 || REF_NAME == RAMB36E1}]
if {[llength $ram_cells] != 1} {
    error "Expected one RAMB18E1/RAMB36E1 for the 64x8 RAM; found [llength $ram_cells]"
}
set ram_cell [lindex $ram_cells 0]
set primitive [get_property REF_NAME $ram_cell]
set extra_output_register [get_property DOA_REG $ram_cell]
set write_mode [get_property WRITE_MODE_A $ram_cell]
puts "RAM_CHECK board=$board_marking vivado_part=$target_part grade=Industrial primitive=$primitive DOA_REG=$extra_output_register WRITE_MODE_A=$write_mode"
if {$extra_output_register != 0} {
    error "An extra BRAM output register would change the V1.0 read latency"
}
report_utilization -file [file join [pwd] ram_only_utilization.rpt]
