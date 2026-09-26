# Skapar .venv och installerar beroenden. Kör en gång:
#   powershell -ExecutionPolicy Bypass -File run\windows\setup.ps1
$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Repo
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
if (Get-Command py -ErrorAction SilentlyContinue) { $base = @("py", "-3") }
elseif (Get-Command python -ErrorAction SilentlyContinue) { $base = @("python") }
else { Write-Error "Python 3 saknas. Installera: winget install Python.Python.3.12" }
$pre = @(); if ($base.Length -gt 1) { $pre = $base[1..($base.Length - 1)] }
& $base[0] @pre -m venv .venv
$Py = Join-Path $Repo ".venv\Scripts\python.exe"
& $Py -m pip install --upgrade pip | Out-Null
# Låsta versioner (reproducerbart) + paketet brastat i redigerbart läge.
& $Py -m pip install -r requirements.lock
& $Py -m pip install --no-deps -e .
& $Py -m unittest discover -s tests
Write-Host "Klart. Testa: run\windows\sol_watchlist.bat"
