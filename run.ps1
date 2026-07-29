# Launcher script for botyarajump on Windows PowerShell
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    Write-Host "Starting botyarajump using .venv..." -ForegroundColor Green
    & $VenvPython main.py
} else {
    Write-Host "Starting botyarajump using system python..." -ForegroundColor Yellow
    python main.py
}
