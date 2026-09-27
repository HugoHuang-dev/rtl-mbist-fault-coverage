# Automation and Audit Scripts

| Version | Entry points | Function |
| --- | --- | --- |
| v1 | [`generate_march_reference.py`](generate_march_reference.py) | Generate the 640-request reference sequence |
| v4 | [`run_step04.py`](run_step04.py) | Independent checker negative regression |
| v5 | [`run_step05.py`](run_step05.py) | Directed faulty-RAM tests |
| v6 | [`generate_fault_manifest.py`](generate_fault_manifest.py), [`run_step06.py`](run_step06.py), [`audit_step06.py`](audit_step06.py) | Manifest, batch execution, and raw-data audit |
| v7 | [`evaluate_fault_coverage.py`](evaluate_fault_coverage.py) | Coverage and first-detection phase analysis |
| v8–v9 | [`audit_step08.py`](audit_step08.py), [`audit_step08_ila.py`](audit_step08_ila.py) | Implementation-report and ILA-data audits |

Run scripts from the project root. Commands and inputs are linked from the [main README](../README.md). Tool configuration and output directories are in the [reproduction guide](../docs/reproduce.md). Further entries: [basic simulation](run_basic_sim.py), [board build](run_board_build.py), and [revision audit](audit_board_revision.py).

[`audit_final_hardware.py`](audit_final_hardware.py) reads five native ILA captures and checks transactions, responses, diagnostics, restart, and completion. See [board acceptance](../results/step08/hardware_final/README.md).
