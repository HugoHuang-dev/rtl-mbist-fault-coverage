# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : inspect_ila_api.tcl
# Module  : inspect_ila_api
# -----------------------------------------------------------------------------
set root [file normalize [file join [file dirname [info script]] ..]]
open_project [file join $root fpga vivado mbist_board.xpr]
open_run synth_1
create_debug_core u_ila ila
puts "ILA_PROPERTIES [list_property [get_debug_cores u_ila]]"
puts "ILA_PORTS [get_debug_ports u_ila/*]"
puts "HELP_CREATE_PORT [help create_debug_port]"
puts "HELP_CONNECT [help connect_debug_port]"
puts "HELP_IMPLEMENT [help implement_debug_core]"
puts "HELP_SAVE_CONSTRAINTS [help save_constraints]"
puts "HELP_SAVE_AS [help save_constraints_as]"
