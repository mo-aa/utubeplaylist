$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$taskName = "TelegramPlaylistBot"
$logDir = Join-Path $projectRoot "logs"
$logFile = Join-Path $logDir "bot.log"
$runScript = Join-Path $projectRoot "run-bot.ps1"

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment not found. Create it first with: python -m venv .venv"
}

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runScript`""

$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Runs the Telegram YouTube playlist bot at logon" `
    -Force | Out-Null

Write-Host "Scheduled task '$taskName' created."
Write-Host "Logs will be written to $logFile"
