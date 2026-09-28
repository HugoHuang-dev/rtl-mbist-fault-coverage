# V13 synthesis-stage STA on the *archived V12 Verilog netlist*.
# Run inside the pinned ORFS image with V13_INPUT and V13_OUTPUT set.
set input $::env(V13_INPUT)
set output $::env(V13_OUTPUT)
set flow /OpenROAD-flow-scripts/flow
set platform $flow/platforms/nangate45

file mkdir $output
read_liberty $input/NangateOpenCellLibrary_typical.lib
read_lef $platform/lef/NangateOpenCellLibrary.tech.lef
read_lef $platform/lef/NangateOpenCellLibrary.macro.mod.lef
read_verilog $input/1_2_yosys.v
link_design mbist_asic_top
read_sdc $input/constraint.sdc

# There is no placement/routing in Phase I. Use the Liberty's explicit
# statistical wire-load model, not a fabricated placement RC estimate.
set_wire_load_mode top
set_wire_load_model -name 5K_hvratio_1_1
puts "V13_INTERCONNECT wire_load_model=5K_hvratio_1_1 mode=top; no placement or SPEF"
puts "V13_CLOCKS [llength [all_clocks]]"
puts "V13_INPUTS [llength [all_inputs]]"
puts "V13_OUTPUTS [llength [all_outputs]]"
puts "V13_REGISTERS [llength [all_registers]]"
if {[llength [all_clocks]] != 1 || [llength [all_inputs]] != 13 ||
    [llength [all_outputs]] != 54} {
    error "V13 port/clock count differs from frozen V11 contract"
}

check_setup -verbose > $output/check_setup.rpt
report_worst_slack -max -digits 4 > $output/setup_wns.rpt
report_checks -path_delay max -group_path_count 10 -format full_clock_expanded \
    -fields {net capacitance fanout slew} -digits 4 > $output/setup_top10.rpt
report_checks -path_delay max -group_path_count 10 -format json \
    -digits 4 > $output/setup_top10.json
report_checks -path_delay max -from [all_registers] -to [all_registers] \
    -format full_clock_expanded -fields {net capacitance fanout slew} \
    -digits 4 > $output/reg_to_reg.rpt
report_checks -path_delay max -from [get_ports {start rst_n req_ready rd_valid rd_data*}] \
    -to [all_registers] -format full_clock_expanded \
    -digits 4 > $output/input_to_reg.rpt
report_checks -path_delay max -from [all_registers] -to [all_outputs] \
    -format full_clock_expanded -digits 4 > $output/reg_to_output.rpt
report_checks -path_delay max -from [get_ports {start rst_n req_ready rd_valid rd_data*}] \
    -to [all_outputs] -format full_clock_expanded \
    -digits 4 > $output/input_to_output.rpt
report_checks -unconstrained -path_delay max -group_path_count 20 \
    -format full_clock_expanded -digits 4 > $output/unconstrained_paths.rpt
report_checks -unconstrained -path_delay max -group_path_count 20 \
    -format json -digits 4 > $output/unconstrained_paths.json

puts "V13_REPORTS_WRITTEN $output"
