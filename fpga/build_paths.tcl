# Shared paths for a new board build; existing captures are never overwritten.
set root [file normalize [file join [file dirname [info script]] ..]]
set run_id [clock format [clock seconds] -format %Y%m%d_%H%M%S]
if {[info exists ::env(MBIST_RUN_ID)]} { set run_id $::env(MBIST_RUN_ID) }
if {![regexp {^[A-Za-z0-9_-]+$} $run_id]} { error "Invalid MBIST_RUN_ID" }
set inject 0
if {[info exists ::env(MBIST_INJECT_FAULT)]} { set inject $::env(MBIST_INJECT_FAULT) }
if {$inject ni {0 1}} { error "MBIST_INJECT_FAULT must be 0 or 1" }
set variant ""
if {$inject} { set variant "_fault" }
set result_root [file join $root results reruns $run_id step08]
set project_dir [file join $root .build $run_id vivado$variant]
