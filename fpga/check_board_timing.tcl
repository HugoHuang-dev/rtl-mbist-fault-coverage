# Run after routing. Check both setup and hold, and preserve CDC/exception reports.
report_timing -delay_type min -max_paths 10 -file [file join $evidence hold_paths.rpt]
report_cdc -details -file [file join $evidence cdc.rpt]
report_exceptions -coverage -file [file join $evidence exceptions.rpt]
check_timing -verbose -file [file join $evidence check_timing.rpt]
set f [open [file join $evidence synchronizer_checks.txt] w]
foreach name {reset_meta_reg reset_release_reg {key_sync_reg[0]} {key_sync_reg[1]}} {
    set c [get_cells -quiet $name]
    if {[llength $c] != 1} { error "Missing synchronizer $name" }
    set attribute [get_property ASYNC_REG $c]
    puts $f "$name ASYNC_REG=$attribute"
    if {$attribute ni {1 TRUE true}} { error "ASYNC_REG missing on $name" }
}
foreach pair {{reset_meta_reg reset_release_reg} {reset_release_reg reset_sync_reg} {{key_sync_reg[0]} {key_sync_reg[1]}}} {
    set path [get_timing_paths -from [get_cells [lindex $pair 0]] -to [get_cells [lindex $pair 1]] -max_paths 1]
    if {[llength $path] != 1} { error "Synchronizer interstage path was excluded: $pair" }
    puts $f "TIMED_INTERSTAGE $pair slack=[get_property SLACK $path]"
}
foreach kind {max min} {
    set path [get_timing_paths -delay_type $kind -max_paths 1]
    if {[llength $path] != 1} { error "Missing $kind timing path" }
    set slack [get_property SLACK $path]
    puts $f "$kind slack=$slack"
    if {$slack < 0} { error "$kind timing failed: $slack" }
}
close $f
puts "BOARD_TIMING_CHECK_PASS setup_and_hold=met synchronizer_paths=timed"
