@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo        DeepSight Studio Updater
echo ===============================================
echo.

:: Set path
cd /d "%~dp0"
echo Current directory: %CD%

:: Backup config
if exist maintenance.json (
    copy maintenance.json maintenance.json.bak
    echo Created backup: maintenance.json.bak
)

:: Activate venv
call venv\Scripts\activate.bat

echo.
echo Choose an option:
echo 1. Update all dependencies
echo 2. Check for updates but ask first
echo 3. Skip dependency updates
echo.

set /p CHOICE="Enter choice (1-3): "

if "%CHOICE%"=="1" (
    echo.
    echo Updating all dependencies...
    pip install --upgrade pip
    pip install --upgrade opencv-python numpy Pillow pyserial pyyaml tqdm
    pip install --upgrade --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
    pip install --upgrade ultralytics
    echo Done updating dependencies.
    echo.
    
    pause
)

if "%CHOICE%"=="2" (
    echo.
    echo Checking for outdated packages...
    pip list --outdated
    
    echo.
    echo Would you like to update all outdated packages? (y/n)
    set /p UPDATE="Your choice: "
    
    if /i "%UPDATE%"=="y" (
        echo.
        echo Updating dependencies...
        pip install --upgrade pip
        pip install --upgrade opencv-python numpy Pillow pyserial pyyaml tqdm
        pip install --upgrade --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
        pip install --upgrade ultralytics
        echo Done updating dependencies.
        echo.
    )
    
    pause
)

echo.
echo Do you want to download the latest code from GitHub? (y/n)
set /p CODE_UPDATE="Your choice: "

if /i "%CODE_UPDATE%"=="y" (
    echo.
    echo Downloading latest code...
    
    :: Create temp directory
    if exist temp_update rmdir /s /q temp_update
    mkdir temp_update
    cd temp_update
    
    :: Download code
    curl -L -o deepsight.zip https://github.com/yourusername/DeepSightStudio/archive/refs/heads/main.zip
    
    :: Extract files
    echo Extracting files...
    powershell -Command "Expand-Archive -Force -Path 'deepsight.zip' -DestinationPath '.'"
    
    :: Find extracted directory
    for /d %%d in (*) do (
        set EXTRACTED_DIR=%%d
    )
    
    :: Copy files
    echo Copying new files...
    xcopy "!EXTRACTED_DIR!\*.py" "..\" /y
    xcopy "!EXTRACTED_DIR!\*.md" "..\" /y
    
    :: Go back and clean up
    cd ..
    rmdir /s /q temp_update
    
    echo Code update complete.
)

:: Restore config if needed
if exist maintenance.json.bak (
    copy maintenance.json.bak maintenance.json /y
    echo Restored configuration.
)

echo.
echo Update complete!
echo.

pause
