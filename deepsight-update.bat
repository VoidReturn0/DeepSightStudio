@echo off
cd /d "%~dp0"
echo ===============================================
echo        DeepSight Studio Updater
echo ===============================================
echo.
echo Current directory: %CD%

:: Backup configuration
if exist maintenance.json (
    copy maintenance.json maintenance.json.bak
    echo Created backup: maintenance.json.bak
)

:: Activate virtual environment
call venv\Scripts\activate.bat

echo.
echo Choose an option:
echo 1. Update all dependencies
echo 2. Check for outdated packages
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
    echo All dependencies updated.
)

if "%CHOICE%"=="2" (
    echo.
    echo Checking for outdated packages...
    pip list --outdated
    echo.
    pause
    
    echo.
    echo Would you like to update PyTorch? (y/n)
    set /p UPDATE_TORCH="Your choice: "
    if /i "%UPDATE_TORCH%"=="y" (
        pip install --upgrade --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
        echo PyTorch updated.
        pause
    )
    
    echo.
    echo Would you like to update OpenCV? (y/n)
    set /p UPDATE_CV="Your choice: "
    if /i "%UPDATE_CV%"=="y" (
        pip install --upgrade opencv-python
        echo OpenCV updated.
        pause
    )
    
    echo.
    echo Would you like to update Pillow? (y/n)
    set /p UPDATE_PILLOW="Your choice: "
    if /i "%UPDATE_PILLOW%"=="y" (
        pip install --upgrade Pillow
        echo Pillow updated.
        pause
    )
    
    echo.
    echo Would you like to update NumPy? (y/n)
    set /p UPDATE_NUMPY="Your choice: "
    if /i "%UPDATE_NUMPY%"=="y" (
        pip install --upgrade numpy
        echo NumPy updated.
        pause
    )
    
    echo.
    echo Would you like to update PySerial? (y/n)
    set /p UPDATE_SERIAL="Your choice: "
    if /i "%UPDATE_SERIAL%"=="y" (
        pip install --upgrade pyserial
        echo PySerial updated.
        pause
    )
)

echo.
echo 
echo Would you like to update the code from GitHub? (y/n)
set /p UPDATE_CODE="Your choice: "

if /i "%UPDATE_CODE%"=="y" (
    echo.
    echo Downloading latest code...
    
    :: Create temp directory
    if exist temp_update rmdir /s /q temp_update
    mkdir temp_update
    cd temp_update
    
    echo Downloading from GitHub...
    curl -L -o deepsight.zip https://github.com/yourusername/DeepSightStudio/archive/refs/heads/main.zip
    if errorlevel 1 (
        echo Download failed. Check your internet connection.
        cd ..
        rmdir /s /q temp_update
        goto end_update
    )
    
    echo Extracting files...
    powershell -Command "Expand-Archive -Force -Path 'deepsight.zip' -DestinationPath '.'"
    
    :: Find extracted directory
    for /d %%d in (*) do (
        set EXTRACTED_DIR=%%d
        goto copy_files
    )
    
    :copy_files
    echo Copying new files...
    xcopy "%EXTRACTED_DIR%\*.py" "..\" /y
    xcopy "%EXTRACTED_DIR%\*.md" "..\" /y
    
    :: Cleanup
    cd ..
    rmdir /s /q temp_update
    
    echo Code has been updated.
    pause
)

:end_update
:: Restore configuration
if exist maintenance.json.bak (
    copy maintenance.json.bak maintenance.json /y
    echo Restored configuration.
)

echo.
echo Update process complete!
echo.
pause
