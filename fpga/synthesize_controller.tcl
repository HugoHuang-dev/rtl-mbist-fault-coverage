# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : synthesize_controller.tcl
# Module  : synthesize_controller
# -----------------------------------------------------------------------------
# Resource measurement for the independent MBIST controller (without RAM/IO).
source [file join [file dirname [info script]] build_paths.tcl]
set evidence [file join $result_root controller]
file mkdir $evidence
foreach name {address_generator.v data_generator.v memory_interface.v response_checker.v march_controller.v mbist_top.v} {
    read_verilog [file join $root rtl $name]
}
synth_design -top mbist_top -part xc7a35tfgg484-2 -no_iobuf
set_operating_conditions -grade Industrial
report_operating_conditions -grade -file [file join $evidence operating_conditions.rpt]
report_utilization -file [file join $evidence utilization.rpt]
report_timing_summary -file [file join $evidence timing_summary.rpt]
write_checkpoint -force [file join $evidence controller_synth.dcp]
puts "STEP08_CONTROLLER_SYNTH_PASS"
