@echo off
setlocal enabledelayedexpansion

:: Capture the directory of the batch script
set "SCRIPT_DIR=%~dp0"

:: Change to the directory of the batch script
cd /d "%SCRIPT_DIR%"

:: Use the Python from the virtual environment if it exists
if exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

:: Ensure we're using the virtual environment's Python
"%PYTHON_EXE%" -m venv "%SCRIPT_DIR%venv"

:: Activate the virtual environment and install required packages
"%SCRIPT_DIR%venv\Scripts\pip.exe" install pillow pyserial

:: Run the GUI using the virtual environment's Python
"%SCRIPT_DIR%venv\Scripts\python.exe" gui.py

pause
