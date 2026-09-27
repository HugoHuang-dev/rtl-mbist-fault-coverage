# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# -----------------------------------------------------------------------------
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : set_industrial.tcl
# Module  : set_industrial
# -----------------------------------------------------------------------------
# Run before implementation optimization for the board's -2I operating grade.
set_operating_conditions -grade Industrial
report_operating_conditions -grade
