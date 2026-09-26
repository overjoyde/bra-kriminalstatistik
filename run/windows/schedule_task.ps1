# Schemalägg månadsvis körning i Windows Schemaläggaren (standard: den 15:e kl. 07:00).
#   powershell -ExecutionPolicy Bypass -File run\windows\schedule_task.ps1
#   powershell -ExecutionPolicy Bypass -File run\windows\schedule_task.ps1 -Day 5 -Time 06:30
#   powershell -ExecutionPolicy Bypass -File run\windows\schedule_task.ps1 -Remove
param([int]$Day = 15, [string]$Time = "07:00", [switch]$Remove)
$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Name = "bra-kriminalstatistik-fetch"
$Wrapper = Join-Path $Repo "run\windows\_scheduled.cmd"

if ($Remove) {
    schtasks.exe /Delete /F /TN $Name 2>$null | Out-Null
    Remove-Item $Wrapper -ErrorAction SilentlyContinue
    Write-Host "Borttaget."
    exit 0
}

New-Item -ItemType Directory -Force -Path (Join-Path $Repo "data\logs") | Out-Null
$log = Join-Path $Repo "data\logs\fetch.log"
$ps1 = Join-Path $Repo "run\windows\fetch_all.ps1"
# Liten wrapper så att sökvägar med mellanslag och loggomdirigering fungerar i schtasks /TR.
@"
@echo off
cd /d "$Repo"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$ps1" --no-pdf --notify >> "$log" 2>&1
"@ | Set-Content -Path $Wrapper -Encoding ASCII

schtasks.exe /Create /F /TN $Name /SC MONTHLY /D $Day /ST $Time /TR "`"$Wrapper`"" | Out-Null
Write-Host "Schemalagt '$Name' dag $Day varje månad kl $Time."
Write-Host "Logg: $log"
Write-Host "Testkör nu: schtasks /Run /TN $Name"
