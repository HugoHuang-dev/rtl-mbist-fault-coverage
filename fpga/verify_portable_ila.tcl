source [file join [file dirname [info script]] build_paths.tcl]
set directory [file join $root results reruns $run_id portable_ila]
open_hw
set capture [read_hw_ila_data [file join $directory march_c_minus_64x8_portable.ila]]
if {[llength $capture] != 1} { error "Portable capture import failed" }
puts "PORTABLE_ILA_IMPORT_PASS object=$capture"
open_wave_database [file join $directory portable_capture.wdb]
open_wave_config [file join $directory portable_capture.wcfg]
if {[lsearch -exact [get_objects -r *] {//u_mbist/phase}] < 0} { error "Phase probe missing from WDB" }
puts "PORTABLE_WDB_WCFG_OPEN_PASS"
close_sim
close_hw
