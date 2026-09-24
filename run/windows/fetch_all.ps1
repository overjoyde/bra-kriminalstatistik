# Kör scripts/fetch_all.py med projektets Python. Argument skickas vidare, t.ex.:
#   powershell -ExecutionPolicy Bypass -File run\windows\fetch_all.ps1 --help
. (Join-Path $PSScriptRoot "_common.ps1")
Invoke-Py (@("scripts/fetch_all.py") + $args)
