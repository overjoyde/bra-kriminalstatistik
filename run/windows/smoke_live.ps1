# Kör scripts/smoke_live.py med projektets Python. Argument skickas vidare, t.ex.:
#   powershell -ExecutionPolicy Bypass -File run\windows\smoke_live.ps1 --help
. (Join-Path $PSScriptRoot "_common.ps1")
Invoke-Py (@("scripts/smoke_live.py") + $args)
