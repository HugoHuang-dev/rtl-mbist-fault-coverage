# Simulation Environment

The project uses Vivado 2018.3 and its XSim simulator as the primary simulation tool. Icarus Verilog provides an independent cross-check.

The [v2 evidence](../results/step02/README.md) contains RAM testbench commands, source hashes, and logs. XSim and Icarus also ran the complete MBIST and fault-injection regressions.

Run the v3 controller integration test with [`run_step03.ps1`](run_step03.ps1); its logs and CSV trace comparison are in the [v3 record](../results/step03/README.md). [`run_step04.py`](../scripts/run_step04.py) runs v4 baseline and negative tests; see [v4 results](../results/step04/README.md). [`run_step05.py`](../scripts/run_step05.py) runs v5 stand-alone RAM and MBIST fault tests; see [v5 results](../results/step05/README.md). [`run_step06.py`](../scripts/run_step06.py) runs the 32-instance pilot and 2,048-instance full campaign in both simulators; results, raw logs, audit, and replay commands are in the [v6 record](../results/step06/README.md).
