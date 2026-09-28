# ORFS Nangate45 synthesis setup for the verified 64x8 MBIST controller.
# The host project is mounted at /work/mbist by asic/scripts/run_v11.sh.
export DESIGN_NAME = mbist_asic_top
export PLATFORM = nangate45

MBIST_ROOT := $(abspath $(dir $(DESIGN_CONFIG))/../..)
MBIST_RTL_LIST := $(MBIST_ROOT)/asic/rtl/asic_rtl.f
export VERILOG_FILES := $(addprefix $(MBIST_ROOT)/,$(shell sed -e '/^#/d' -e '/^$$/d' $(MBIST_RTL_LIST)))
export SDC_FILE := $(MBIST_ROOT)/asic/config/constraint.sdc

# 20 ns = 20,000 ps for the Yosys/ABC delay target used by this ORFS commit.
export ABC_CLOCK_PERIOD_IN_PS = 20000
export SYNTH_REPEATABLE_BUILD ?= 1
