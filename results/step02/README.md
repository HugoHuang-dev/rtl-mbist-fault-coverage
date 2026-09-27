# v2 Original Evidence and Reproduction

v2 · 09.04–09.06. This directory retains RAM simulation and synthesis logs with exact commands. Sources: `rtl/single_port_sync_ram.v` and `tb/tb_single_port_sync_ram.sv`.

| File | Contents |
| --- | --- |
| `xsim_compile.log`, `xsim_elaborate.log`, `xsim_run.log` | Independent XSim compile, elaborate, and run output |
| `icarus_compile.log`, `icarus_run.log` | Independent Icarus compile and run output |
| `vivado_ram_synth.log` | RAM-only synthesis, Industrial grade, and primitive attributes |
| `ram_only_utilization.rpt` | Vivado utilization: one RAMB18E1 |

Both simulator runs exited with code 0 and printed `RAM_TB_PASS checks=146 reads=70 writes=68` plus the same four `CASE_PASS` markers. Synthesis exited with code 0. Key log entries include `Device Grade = industrial` and `RAM_CHECK board=XC7A35TFGG484-2I vivado_part=xc7a35tfgg484-2 grade=Industrial primitive=RAMB18E1 DOA_REG=0 WRITE_MODE_A=NO_CHANGE`.

## PowerShell reproduction commands

Run from the project root. Build directories are ignored by `.gitignore`. Change tool paths to match a different installation; keep the command arguments.

```powershell
$project = (Get-Location).Path
$evidence = Join-Path $project 'results\step02'
New-Item -ItemType Directory -Force -Path $evidence | Out-Null

$xbuild = Join-Path $project 'sim\.build-xsim'
New-Item -ItemType Directory -Force -Path $xbuild | Out-Null
Push-Location $xbuild
& 'C:\Xilinx\Vivado\2018.3\bin\xvlog.bat' -sv (Join-Path $project 'rtl\single_port_sync_ram.v') (Join-Path $project 'tb\tb_single_port_sync_ram.sv') *> (Join-Path $evidence 'xsim_compile.log')
if ($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
& 'C:\Xilinx\Vivado\2018.3\bin\xelab.bat' tb_single_port_sync_ram -s ram_tb_snapshot *> (Join-Path $evidence 'xsim_elaborate.log')
if ($LASTEXITCODE -ne 0) { throw 'xelab failed' }
& 'C:\Xilinx\Vivado\2018.3\bin\xsim.bat' ram_tb_snapshot -runall *> (Join-Path $evidence 'xsim_run.log')
if ($LASTEXITCODE -ne 0) { throw 'xsim failed' }
Pop-Location

$ibuild = Join-Path $project 'sim\.build-iverilog'
New-Item -ItemType Directory -Force -Path $ibuild | Out-Null
Push-Location $ibuild
& 'C:\iverilog\bin\iverilog.exe' -g2012 -s tb_single_port_sync_ram -o ram_tb.vvp (Join-Path $project 'rtl\single_port_sync_ram.v') (Join-Path $project 'tb\tb_single_port_sync_ram.sv') *> (Join-Path $evidence 'icarus_compile.log')
if ($LASTEXITCODE -ne 0) { throw 'iverilog failed' }
& 'C:\iverilog\bin\vvp.exe' ram_tb.vvp *> (Join-Path $evidence 'icarus_run.log')
if ($LASTEXITCODE -ne 0) { throw 'vvp failed' }
Pop-Location

$sbuild = Join-Path $project 'fpga\.build-ram'
New-Item -ItemType Directory -Force -Path $sbuild | Out-Null
Push-Location $sbuild
& 'C:\Xilinx\Vivado\2018.3\bin\vivado.bat' -mode batch -nojournal -notrace -source (Join-Path $project 'fpga\check_ram_inference.tcl') -tclargs XC7A35TFGG484-2I *> (Join-Path $evidence 'vivado_ram_synth.log')
if ($LASTEXITCODE -ne 0) { throw 'RAM synthesis failed' }
Copy-Item -LiteralPath 'ram_only_utilization.rpt' -Destination (Join-Path $evidence 'ram_only_utilization.rpt') -Force
Pop-Location
```

Acceptance requires exit code 0, exactly one `RAM_TB_PASS` and no `FATAL` in each run log, and `primitive=RAMB18E1 DOA_REG=0` in synthesis. `$finish` alone only indicates that simulation ended.

## Source SHA-256 at acceptance

- `rtl/single_port_sync_ram.v`: `B60138AA0EB8A06110E1824E7C48B3828DCAF1815CB5A86E3B70DB6ED362E4A4`
- `tb/tb_single_port_sync_ram.sv`: `6A21A26113E4B193E1010D0360D953EA7F3401685F038F25C6CC01C3D10346D8`
- `fpga/check_ram_inference.tcl`: `13DBEF3543288B7FE1CB1160789FD117FC542991333BE8BAE265A71A3BD145EB`
