# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : check_v11.tcl
# Module  : check_v11
# -----------------------------------------------------------------------------
# Run with V11_WORK=/work/output after the ORFS synth target.
set flow /OpenROAD-flow-scripts/flow
set project /work/mbist
set result $::env(V11_WORK)/results/nangate45/mbist_asic_top/base

read_liberty $flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib
read_db $result/1_synth.odb
read_sdc $project/asic/config/constraint.sdc
source $flow/platforms/nangate45/setRC.tcl

puts "V11_AUDIT_CLOCKS [llength [all_clocks]]"
puts "V11_AUDIT_INPUTS [llength [all_inputs]]"
puts "V11_AUDIT_OUTPUTS [llength [all_outputs]]"
if {[llength [all_clocks]] != 1 || [llength [all_inputs]] != 13 ||
    [llength [all_outputs]] != 54} {
    error "V11 audit: unexpected clock or port count"
}

puts "V11_CHECK_SETUP_BEGIN"
check_setup -verbose
puts "V11_CHECK_SETUP_END"

puts "V11_MAX_PATH_BEGIN"
report_checks -path_delay max -group_path_count 5
puts "V11_MAX_PATH_END"

puts "V11_RESET_INPUT_PATH_BEGIN"
report_checks -from [get_ports rst_n] -path_delay max
puts "V11_RESET_INPUT_PATH_END"

puts "V11_MEMORY_RESPONSE_PATH_BEGIN"
report_checks -from [get_ports {rd_valid rd_data*}] -path_delay max
puts "V11_MEMORY_RESPONSE_PATH_END"

puts "V11_READY_INPUT_PATH_BEGIN"
report_checks -from [get_ports req_ready] -path_delay max
puts "V11_READY_INPUT_PATH_END"

puts "V11_VALID_INPUT_PATH_BEGIN"
report_checks -from [get_ports rd_valid] -path_delay max
puts "V11_VALID_INPUT_PATH_END"

puts "V11_START_INPUT_PATH_BEGIN"
report_checks -from [get_ports start] -path_delay max
puts "V11_START_INPUT_PATH_END"

puts "V11_REGISTER_PATH_BEGIN"
report_checks -from [all_registers] -to [all_registers] -path_delay max
puts "V11_REGISTER_PATH_END"

puts "V11_REQUEST_OUTPUT_PATH_BEGIN"
report_checks -to [get_ports {req_valid req_write req_addr* req_wdata*}] -path_delay max
puts "V11_REQUEST_OUTPUT_PATH_END"

puts "V11_STATUS_OUTPUT_PATH_BEGIN"
report_checks -to [get_ports {done pass fail error_count*}] -path_delay max
puts "V11_STATUS_OUTPUT_PATH_END"
