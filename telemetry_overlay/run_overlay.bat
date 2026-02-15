@echo off
setlocal

if not exist ".venv\Scripts\python.exe" (
  echo Virtual environment not found.
  echo Run setup first:
  echo   powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
  pause
  exit /b 1
)

.venv\Scripts\python.exe .\launcher.py
