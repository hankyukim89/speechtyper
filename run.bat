@echo off
rem One-click launcher (Windows). First run creates a venv and installs deps.
setlocal
cd /d "%~dp0"
set "LOGDIR=%LOCALAPPDATA%\SpeechTyper"
set "LOGFILE=%LOGDIR%\launcher.log"

if not exist "%LOGDIR%" mkdir "%LOGDIR%"

if not exist .venv (
  py -3 -m venv .venv >>"%LOGFILE%" 2>&1 || exit /b 1
  .venv\Scripts\python.exe -m pip install -q --upgrade pip >>"%LOGFILE%" 2>&1 || exit /b 1
  .venv\Scripts\python.exe -m pip install -q -r requirements.txt >>"%LOGFILE%" 2>&1 || exit /b 1
)

start "" /b ".venv\Scripts\pythonw.exe" -m speechtyper >>"%LOGFILE%" 2>&1
exit /b 0
