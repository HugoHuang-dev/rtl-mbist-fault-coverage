# v3 integration regression; tool discovery and paths are shared with Python.
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
& py.exe -3 (Join-Path $projectRoot 'scripts/run_basic_sim.py') --stage step03
if ($LASTEXITCODE -ne 0) { throw 'v3 regression failed' }
