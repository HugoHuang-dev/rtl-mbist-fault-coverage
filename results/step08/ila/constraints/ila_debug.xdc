set_operating_conditions -grade Industrial
create_debug_core u_ila ila
set_property ALL_PROBE_SAME_MU true [get_debug_cores u_ila]
set_property ALL_PROBE_SAME_MU_CNT 1 [get_debug_cores u_ila]
set_property C_ADV_TRIGGER false [get_debug_cores u_ila]
set_property C_DATA_DEPTH 1024 [get_debug_cores u_ila]
set_property C_EN_STRG_QUAL false [get_debug_cores u_ila]
set_property C_INPUT_PIPE_STAGES 0 [get_debug_cores u_ila]
set_property C_TRIGIN_EN false [get_debug_cores u_ila]
set_property C_TRIGOUT_EN false [get_debug_cores u_ila]
set_property port_width 1 [get_debug_ports u_ila/clk]
connect_debug_port u_ila/clk [get_nets [list sys_clk_IBUF_BUFG]]
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe0]
set_property port_width 1 [get_debug_ports u_ila/probe0]
connect_debug_port u_ila/probe0 [get_nets [list start_pulse]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe1]
set_property port_width 3 [get_debug_ports u_ila/probe1]
connect_debug_port u_ila/probe1 [get_nets [list {u_mbist/phase[0]} {u_mbist/phase[1]} {u_mbist/phase[2]}]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe2]
set_property port_width 6 [get_debug_ports u_ila/probe2]
connect_debug_port u_ila/probe2 [get_nets [list {req_addr[0]} {req_addr[1]} {req_addr[2]} {req_addr[3]} {req_addr[4]} {req_addr[5]}]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe3]
set_property port_width 1 [get_debug_ports u_ila/probe3]
connect_debug_port u_ila/probe3 [get_nets [list req_valid]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe4]
set_property port_width 1 [get_debug_ports u_ila/probe4]
connect_debug_port u_ila/probe4 [get_nets [list req_write]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe5]
set_property port_width 8 [get_debug_ports u_ila/probe5]
connect_debug_port u_ila/probe5 [get_nets [list {req_wdata[0]} {req_wdata[1]} {req_wdata[2]} {req_wdata[3]} {req_wdata[4]} {req_wdata[5]} {req_wdata[6]} {req_wdata[7]}]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe6]
set_property port_width 1 [get_debug_ports u_ila/probe6]
connect_debug_port u_ila/probe6 [get_nets [list rd_valid]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe7]
set_property port_width 8 [get_debug_ports u_ila/probe7]
connect_debug_port u_ila/probe7 [get_nets [list {rd_data[0]} {rd_data[1]} {rd_data[2]} {rd_data[3]} {rd_data[4]} {rd_data[5]} {rd_data[6]} {rd_data[7]}]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe8]
set_property port_width 1 [get_debug_ports u_ila/probe8]
connect_debug_port u_ila/probe8 [get_nets [list done]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe9]
set_property port_width 1 [get_debug_ports u_ila/probe9]
connect_debug_port u_ila/probe9 [get_nets [list pass]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe10]
set_property port_width 1 [get_debug_ports u_ila/probe10]
connect_debug_port u_ila/probe10 [get_nets [list fail]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe11]
set_property port_width 9 [get_debug_ports u_ila/probe11]
connect_debug_port u_ila/probe11 [get_nets [list {error_count[0]} {error_count[1]} {error_count[2]} {error_count[3]} {error_count[4]} {error_count[5]} {error_count[6]} {error_count[7]} {error_count[8]}]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe12]
set_property port_width 3 [get_debug_ports u_ila/probe12]
connect_debug_port u_ila/probe12 [get_nets [list {first_fail_phase[0]} {first_fail_phase[1]} {first_fail_phase[2]}]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe13]
set_property port_width 6 [get_debug_ports u_ila/probe13]
connect_debug_port u_ila/probe13 [get_nets [list {first_fail_addr[0]} {first_fail_addr[1]} {first_fail_addr[2]} {first_fail_addr[3]} {first_fail_addr[4]} {first_fail_addr[5]}]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe14]
set_property port_width 8 [get_debug_ports u_ila/probe14]
connect_debug_port u_ila/probe14 [get_nets [list {first_fail_expected[0]} {first_fail_expected[1]} {first_fail_expected[2]} {first_fail_expected[3]} {first_fail_expected[4]} {first_fail_expected[5]} {first_fail_expected[6]} {first_fail_expected[7]}]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe15]
set_property port_width 8 [get_debug_ports u_ila/probe15]
connect_debug_port u_ila/probe15 [get_nets [list {first_fail_actual[0]} {first_fail_actual[1]} {first_fail_actual[2]} {first_fail_actual[3]} {first_fail_actual[4]} {first_fail_actual[5]} {first_fail_actual[6]} {first_fail_actual[7]}]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe16]
set_property port_width 10 [get_debug_ports u_ila/probe16]
connect_debug_port u_ila/probe16 [get_nets [list {accepted_count[0]} {accepted_count[1]} {accepted_count[2]} {accepted_count[3]} {accepted_count[4]} {accepted_count[5]} {accepted_count[6]} {accepted_count[7]} {accepted_count[8]} {accepted_count[9]}]]
create_debug_port u_ila probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila/probe17]
set_property port_width 1 [get_debug_ports u_ila/probe17]
connect_debug_port u_ila/probe17 [get_nets [list busy]]
set_property C_CLK_INPUT_FREQ_HZ 300000000 [get_debug_cores dbg_hub]
set_property C_ENABLE_CLK_DIVIDER false [get_debug_cores dbg_hub]
set_property C_USER_SCAN_CHAIN 1 [get_debug_cores dbg_hub]
connect_debug_port dbg_hub/clk [get_nets sys_clk_IBUF_BUFG]
