# Testbenches and Fault Models

| Version | Main files | Purpose |
| --- | --- | --- |
| v2 | [`tb_single_port_sync_ram.sv`](tb_single_port_sync_ram.sv) | RAM read/write and one-cycle response checks |
| v3 | [`tb_mbist_top.sv`](tb_mbist_top.sv) | Fault-free MBIST integration |
| v4 | [`march_transaction_checker.sv`](march_transaction_checker.sv) | Independent external transaction and diagnostic checks |
| v5 | [`faulty_memory.sv`](faulty_memory.sv), [`fault_injector.sv`](fault_injector.sv), [`fault_reference_monitor.sv`](fault_reference_monitor.sv) | Single-fault behavior and reference monitoring |
| v6 | [`tb_step06_campaign.sv`](tb_step06_campaign.sv) | Full fault campaign |

Inputs, commands, and results for each version are indexed in the [main README](../README.md).
