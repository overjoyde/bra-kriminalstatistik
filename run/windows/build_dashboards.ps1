# Bygger Excel- och HTML-dashboard från data\raw (kör fetch_tables först).
. (Join-Path $PSScriptRoot "_common.ps1")
Invoke-Py @("scripts/build_excel_dashboard.py")
Invoke-Py @("scripts/build_html_dashboard.py")
Write-Host "Öppna: $Repo\data\dashboard\Bra_trendbevakning_dashboard.html"
