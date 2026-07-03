@echo off
rem One-click launcher (Windows). First run creates a venv and installs deps.
cd /d "%~dp0"
if not exist .venv (
  py -3 -m venv .venv
  .venv\Scripts\pip install -q --upgrade pip
  .venv\Scripts\pip install -q -r requirements.txt
)
.venv\Scripts\pythonw -m speechtyper
