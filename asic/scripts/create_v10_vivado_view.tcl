# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : create_v10_vivado_view.tcl
# Module  : create_v10_vivado_view
# -----------------------------------------------------------------------------
# Vivado 2018.3 view-only project for V10 controller RTL hierarchy.
# It is not an ASIC synthesis flow or FPGA implementation result.
set root [file normalize [file join [file dirname [info script]] .. ..]]
set project_dir [file join $root asic vivado mbist_asic_v10]
set list_file [file join $root asic rtl asic_rtl.f]
set part xc7a35tfgg484-2

if {[file exists $project_dir]} {
    error "V10 Vivado view project already exists; open it instead of overwriting: $project_dir"
}
set fp [open $list_file r]
set rtl {}
while {[gets $fp relative] >= 0} {
    set relative [string trim $relative]
    if {$relative eq "" || [string match "#*" $relative]} { continue }
    lappend rtl [file join $root $relative]
}
close $fp
if {[llength $rtl] != 7} { error "Expected exactly seven V10 controller RTL files" }
foreach path $rtl {
    if {![file exists $path]} { error "Missing RTL file: $path" }
}

create_project mbist_asic_v10 $project_dir -part $part
set_property target_language Verilog [current_project]
add_files -norecurse $rtl
set_property top mbist_asic_top [get_filesets sources_1]
update_compile_order -fileset sources_1
puts "V10_VIEW_TOP [get_property top [get_filesets sources_1]]"
puts "V10_VIEW_FILE_COUNT [llength $rtl]"
foreach path $rtl { puts "V10_VIEW_SOURCE $path" }
synth_design -rtl -name rtl_1
puts "V10_VIEW_ELABORATION_PASS top=mbist_asic_top"
close_design
close_project
