# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : board_pins.xdc
# Module  : board_pin_constraints
# -----------------------------------------------------------------------------
# DaVinci XC7A35T: selected pins from the vendor DaVinci_FPGA_IO.xdc.
# The schematic shows KEY0/reset pulled up and active low, LEDs active high.
set_property -dict {PACKAGE_PIN R4 IOSTANDARD LVCMOS33} [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]
set_property -dict {PACKAGE_PIN U2 IOSTANDARD LVCMOS33} [get_ports sys_rst_n]
set_property -dict {PACKAGE_PIN T1 IOSTANDARD LVCMOS33} [get_ports key0]
set_property -dict {PACKAGE_PIN R2 IOSTANDARD LVCMOS33} [get_ports {led[0]}]
set_property -dict {PACKAGE_PIN R3 IOSTANDARD LVCMOS33} [get_ports {led[1]}]
set_property -dict {PACKAGE_PIN V2 IOSTANDARD LVCMOS33} [get_ports {led[2]}]
set_property -dict {PACKAGE_PIN Y2 IOSTANDARD LVCMOS33} [get_ports {led[3]}]
set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
# Buttons have no timing relationship to sys_clk. Only the external paths to
# the first receiving stages are excluded; both synchronizer stage-to-stage
# paths and the core reset distribution remain timed.
set_false_path -from [get_ports key0] -to [get_pins {key_sync_reg[0]/D}]
set_false_path -from [get_ports sys_rst_n] -to [get_pins {reset_meta_reg/CLR reset_release_reg/CLR}]
# LEDs are static human-visible status outputs, with no external capture clock.
set_false_path -to [get_ports {led[*]}]
