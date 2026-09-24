# Exempelgrafer (PNG) + årstabell till data\charts (kräver sol_watchlist + fetch_tables först).
. (Join-Path $PSScriptRoot "_common.ps1")
Invoke-Py (@("scripts/make_charts.py") + $args)
