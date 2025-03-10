@echo off
REM Ensure we are in the root directory of DeepSightStudio-main
cd /d %~dp0

REM Activate the virtual environment from the venv folder
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please run the installer.
    pause
    exit /b
)

REM Debug: Print the active Python executable
python -c "import sys; print('Using Python:', sys.executable)"

REM Run the gui.py script
python gui.py

pause
