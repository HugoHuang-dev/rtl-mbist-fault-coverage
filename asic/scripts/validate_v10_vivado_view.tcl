# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : validate_v10_vivado_view.tcl
# Module  : validate_v10_vivado_view
# -----------------------------------------------------------------------------
# Validate the separate V10 view project without rebuilding or overwriting it.
set root [file normalize [file join [file dirname [info script]] .. ..]]
set xpr [file join $root asic vivado mbist_asic_v10 mbist_asic_v10.xpr]
open_project $xpr
if {[get_property top [get_filesets sources_1]] ne "mbist_asic_top"} {
    error "Wrong V10 RTL top"
}
synth_design -rtl -name rtl_1
puts "V10_VIEW_ELABORATION_PASS top=[get_property top [get_filesets sources_1]]"
close_design
close_project
