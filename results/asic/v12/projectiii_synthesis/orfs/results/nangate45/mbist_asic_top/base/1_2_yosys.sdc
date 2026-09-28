# V11 preliminary synchronous external-memory timing contract.
# Nangate45 typical Liberty: time=ns, capacitance=fF.
# All delays and loads below are explicit integration assumptions, not SRAM data.
current_design mbist_asic_top

set clk_period 20.0
set clk_port [get_ports clk]
if {[llength $clk_port] != 1} {
    error "V11 SDC: expected exactly one clk port"
}
create_clock -name core_clock -period $clk_period $clk_port
set_clock_uncertainty -setup 0.2 [get_clocks core_clock]
set_clock_uncertainty -hold 0.1 [get_clocks core_clock]

# start/ready/response and rst_n are synchronous inputs at this boundary.
# In particular, rst_n is intentionally NOT given a false path.
set data_inputs [get_ports {start rst_n req_ready rd_valid rd_data*}]
if {[llength $data_inputs] != 12} {
    error "V11 SDC: expected 12 non-clock input bits"
}
set_input_delay -clock core_clock -max 2.0 $data_inputs
set_input_delay -clock core_clock -min 0.0 $data_inputs
set_input_transition 0.1 $data_inputs

set data_outputs [all_outputs]
if {[llength $data_outputs] != 54} {
    error "V11 SDC: expected 54 output bits"
}
set_output_delay -clock core_clock -max 2.0 $data_outputs
set_output_delay -clock core_clock -min 0.0 $data_outputs
set_load 4.0 $data_outputs
