@echo off
setlocal enabledelayedexpansion

:: Create log file to track script progress
echo Script starting > install_log.txt

:: Set colors for console output
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "RESET=[0m"
set "BOLD=[1m"

:: Title header
echo ===============================================
echo        DeepSight Studio Installation         
echo ===============================================
echo.
echo Script is running... >> install_log.txt

:: Set BASE_DIR to current directory
set BASE_DIR=%~dp0
set BASE_DIR=%BASE_DIR:~0,-1%
echo Using current directory: %BASE_DIR% >> install_log.txt
echo Using current directory: %BASE_DIR%

:: Create DeepSightModel directory
set MODEL_DIR=%BASE_DIR%\DeepSightModel
echo Checking for model directory... >> install_log.txt
if not exist "%MODEL_DIR%" (
    echo Creating model weights directory...
    mkdir "%MODEL_DIR%"
    echo Created directory: %MODEL_DIR%
    echo Created model directory >> install_log.txt
) else (
    echo Model weights directory already exists: %MODEL_DIR%
    echo Model directory exists >> install_log.txt
)

echo Testing if script continues after model directory check... >> install_log.txt
echo Testing if script continues after model directory check...

:: Check for Python
echo Checking for Python >> install_log.txt
echo Checking for Python...

:: We'll just check Python without trying to install it for this test
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Python not found >> install_log.txt
    echo Python not found. Please install Python 3.8 or newer.
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo Found Python !PYTHON_VERSION! >> install_log.txt
    echo Found Python !PYTHON_VERSION!
)

:: Add some diagnostic checkpoints to see where script execution stops
echo Script checkpoint 1 - passed Python check >> install_log.txt

:: Create a simple test directory
echo Creating test directory... >> install_log.txt
mkdir test_continue 2>nul
echo Test directory created >> install_log.txt

echo Script checkpoint 2 - created test directory >> install_log.txt

:: Final message
echo Script finished running >> install_log.txt
echo Installation diagnostic complete.
echo See install_log.txt for details.
echo.

:: Make absolutely sure the script doesn't exit until user interaction
echo Press any key to exit...
pause > nul
