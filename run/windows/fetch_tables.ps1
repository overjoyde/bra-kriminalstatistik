# Kör scripts/fetch_tables.py med projektets Python. Argument skickas vidare, t.ex.:
#   powershell -ExecutionPolicy Bypass -File run\windows\fetch_tables.ps1 --help
. (Join-Path $PSScriptRoot "_common.ps1")
Invoke-Py (@("scripts/fetch_tables.py") + $args)
