# FPGA Project

[`board_top.v`](board_top.v) connects the 50 MHz clock, reset synchronizer, debounced KEY0, LEDs, MBIST, and BRAM. [`board_pins.xdc`](board_pins.xdc) specifies pins and timing exceptions.

[`run_board_build.py`](../scripts/run_board_build.py) writes project-local outputs under `.build/<run-id>/vivado` or `vivado_fault`. Options, reports, and audits are described in the [reproduction guide](../docs/reproduce.md).

The [engineering review](../docs/09_engineering_review.md) covers normal and controlled-perturbation builds. The [initial board project](vivado/README.md) retains its original verification records.
