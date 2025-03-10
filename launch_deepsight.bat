@echo off
setlocal

:: Capture the directory of the batch script
set "SCRIPT_DIR=%~dp0"

:: Use the Python from the virtual environment
set "PYTHON_EXE=%SCRIPT_DIR%venv\Scripts\python.exe"

:: Verify the Python executable exists
if not exist "%PYTHON_EXE%" (
    echo Error: Virtual environment not found. Please reinstall.
    pause
    exit /b 1
)

:: Change to the script directory
cd /d "%SCRIPT_DIR%"

:: Activate and run
call "%SCRIPT_DIR%venv\Scripts\activate"
"%PYTHON_EXE%" gui.py

pause
