@echo off
rem Launcher script for botyarajump on Windows CMD
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    echo Starting botyarajump using .venv...
    ".venv\Scripts\python.exe" main.py
) else (
    echo Starting botyarajump using system python...
    python main.py
)
