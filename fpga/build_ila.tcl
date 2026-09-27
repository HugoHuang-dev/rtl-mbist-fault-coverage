# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : build_ila.tcl
# Module  : build_ila
# -----------------------------------------------------------------------------
# Add a 1024-sample ILA to the verified synthesized board design, then
# implement a separate debug bitstream. Trigger on start_pulse at position 0
# to capture the entire ~960-cycle MBIST run through DONE.
source [file join [file dirname [info script]] build_paths.tcl]
set evidence [file join $result_root ila$variant]
file mkdir $evidence
open_project [file join $project_dir mbist_board.xpr]
open_run synth_1
set_operating_conditions -grade Industrial

proc scalar {name} {
    set nets [get_nets -quiet $name]
    if {[llength $nets] != 1} { error "Expected one net $name, got $nets" }
    return $nets
}
proc bus {name width} {
    set nets {}
    for {set i 0} {$i < $width} {incr i} {
        lappend nets [scalar [format {%s[%d]} $name $i]]
    }
    return $nets
}

create_debug_core u_ila ila
set_property C_DATA_DEPTH 1024 [get_debug_cores u_ila]
for {set i 1} {$i < 18} {incr i} {
    create_debug_port u_ila probe
}
connect_debug_port u_ila/clk [scalar sys_clk_IBUF_BUFG]
set probes [list \
    [scalar start_pulse] \
    [bus u_mbist/phase 3] \
    [bus req_addr 6] \
    [scalar req_valid] \
    [scalar req_write] \
    [bus req_wdata 8] \
    [scalar rd_valid] \
    [bus rd_data 8] \
    [scalar done] \
    [scalar pass] \
    [scalar fail] \
    [bus error_count 9] \
    [bus first_fail_phase 3] \
    [bus first_fail_addr 6] \
    [bus first_fail_expected 8] \
    [bus first_fail_actual 8] \
    [bus accepted_count 10] \
    [scalar busy]]
for {set i 0} {$i < [llength $probes]} {incr i} {
    set_property PORT_WIDTH [llength [lindex $probes $i]] [get_debug_ports u_ila/probe$i]
    connect_debug_port u_ila/probe$i [lindex $probes $i]
}
puts "ILA_PROBES count=[llength $probes] depth=1024"
save_constraints_as -dir [file join $evidence constraints] \
    -target_constrs_file ila_debug.xdc step08_ila_constrs
implement_debug_core
write_checkpoint -force [file join $evidence board_with_ila_synth.dcp]

opt_design
place_design
route_design
report_operating_conditions -grade -file [file join $evidence operating_conditions.rpt]
report_utilization -file [file join $evidence utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $evidence timing_summary.rpt]
report_timing -delay_type max -max_paths 10 -sort_by group -file [file join $evidence critical_paths.rpt]
source [file join $root fpga check_board_timing.tcl]
report_drc -file [file join $evidence drc.rpt]
write_checkpoint -force [file join $evidence board_with_ila_routed.dcp]
write_debug_probes -force [file join $evidence board_with_ila.ltx]
write_bitstream -force [file join $evidence board_with_ila.bit]
puts "STEP08_ILA_BUILD_PASS probes=[llength $probes] depth=1024"
