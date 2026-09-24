# Kör scripts/sol_query.py med projektets Python. Argument skickas vidare, t.ex.:
#   powershell -ExecutionPolicy Bypass -File run\windows\sol_query.ps1 --help
. (Join-Path $PSScriptRoot "_common.ps1")
Invoke-Py (@("scripts/sol_query.py") + $args)
