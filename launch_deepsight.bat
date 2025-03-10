@echo off
setlocal

:: Capture the directory of the batch script
set "SCRIPT_DIR=%~dp0"

:: Change to the directory of the batch script
cd /d "%SCRIPT_DIR%"

:: Activate virtual environment
call "%SCRIPT_DIR%venv\Scripts\activate"

:: List installed packages
pip list

:: Launch GUI
python gui.py

pause
