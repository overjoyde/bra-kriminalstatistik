# Gemensamt: hitta repo-roten och rätt Python (projektets .venv om den finns).
$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Repo
$VenvPy = Join-Path $Repo ".venv\Scripts\python.exe"
$VenvPyPosix = Join-Path $Repo ".venv/bin/python"   # om skripten körs med PowerShell 7 på macOS/Linux
if (Test-Path $VenvPy) {
    $Py = @($VenvPy)
} elseif (Test-Path $VenvPyPosix) {
    $Py = @($VenvPyPosix)
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $Py = @("py", "-3")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Py = @("python")
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $Py = @("python3")
} else {
    Write-Error "Python 3 saknas. Installera: winget install Python.Python.3.12  (eller https://www.python.org/downloads/)"
}
# Svenska tecken i konsolen
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
# Gör brastat importerbart även utan "pip install -e ." (t.ex. systemets Python).
$env:PYTHONPATH = if ($env:PYTHONPATH) { "$Repo$([IO.Path]::PathSeparator)$env:PYTHONPATH" } else { $Repo }

function Invoke-Py([string[]]$Arguments) {
    $exe = $Py[0]
    $pre = @()
    if ($Py.Length -gt 1) { $pre = $Py[1..($Py.Length - 1)] }
    & $exe @pre @Arguments
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
