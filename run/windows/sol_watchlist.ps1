# Kör scripts/sol_watchlist.py med projektets Python. Argument skickas vidare, t.ex.:
#   powershell -ExecutionPolicy Bypass -File run\windows\sol_watchlist.ps1 --help
. (Join-Path $PSScriptRoot "_common.ps1")
Invoke-Py (@("scripts/sol_watchlist.py") + $args)
