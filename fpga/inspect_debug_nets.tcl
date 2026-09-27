# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : inspect_debug_nets.tcl
# Module  : inspect_debug_nets
# -----------------------------------------------------------------------------
# Read-only discovery of synthesized nets for a separate ILA implementation.
set root [file normalize [file join [file dirname [info script]] ..]]
open_project [file join $root fpga vivado mbist_board.xpr]
open_run synth_1
foreach pattern {start_pulse phase req_valid req_write req_addr req_wdata rd_valid rd_data done pass fail error_count first_fail accepted_count sys_clk} {
    set matches [get_nets -hier -quiet -filter "NAME =~ *$pattern*"]
    puts "DEBUG_NET pattern=$pattern count=[llength $matches] names=$matches"
}
puts "DEBUG_CELL_BUFG [get_cells -hier -filter {REF_NAME == BUFG}]"
puts "DEBUG_HELP_CREATE"
help create_debug_core
puts "DEBUG_HELP_CONNECT"
help connect_debug_port
puts "DEBUG_HELP_PROBES"
help write_debug_probes
