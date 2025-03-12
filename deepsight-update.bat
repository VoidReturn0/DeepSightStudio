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

:: Generate requirements file based on installed packages
echo Analyzing currently installed packages...
pip freeze > current_requirements.txt
:: Filter out .txt files that are not requirements
findstr /v ".txt$" current_requirements.txt > requirements.txt
del current_requirements.txt

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
    
    :: Special handling for PyTorch (needs specific index URL)
    echo Updating PyTorch with special URL...
    pip install --upgrade --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
    
    :: Update ultralytics separately as it's a key dependency
    echo Updating Ultralytics...
    pip install --upgrade ultralytics
    
    :: Update remaining packages from generated requirements
    echo Updating remaining packages...
    pip install --upgrade -r requirements.txt
    
    echo All dependencies updated.
    echo Please hit the Enter key!!!
)

if "%CHOICE%"=="2" (
    echo.
    echo Checking for outdated packages...
    pip list --outdated
    
    echo.
    echo Would you like to update outdated packages? (y/n)
    set /p UPDATE_OUTDATED=
    if /i "%UPDATE_OUTDATED%"=="y" (
        :: Get list of outdated packages
        pip list --outdated --format=freeze | findstr /v "torch torchvision" > outdated.txt
        
        :: Update all packages except torch/torchvision (needs special handling)
        for /F "tokens=1 delims==" %%a in (outdated.txt) do (
            echo Updating %%a...
            pip install --upgrade %%a
        )
        
        :: Update PyTorch separately with correct index URL
        pip list --outdated --format=freeze | findstr "torch torchvision" > pytorch_outdated.txt
        if not "%ERRORLEVEL%"=="1" (
            echo Updating PyTorch with special URL...
            pip install --upgrade --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
        )
        
        :: Clean up
        if exist outdated.txt del outdated.txt
        if exist pytorch_outdated.txt del pytorch_outdated.txt
        
        echo Outdated packages have been updated.
    )
)

echo.
echo ===============================================
echo          Code Update Options
echo ===============================================
echo.
echo Would you like to update the code from GitHub? (y/n)
set /p UPDATE_CODE=

if /i "%UPDATE_CODE%"=="y" (
    echo.
    echo Downloading latest code...
    
    :: Create temp directory
    if exist temp_update rmdir /s /q temp_update
    mkdir temp_update
    cd temp_update
    
    echo Downloading from GitHub...
    curl -L -o deepsight.zip https://github.com/VoidReturn0/DeepSightStudio/archive/refs/heads/main.zip
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
        echo Found extracted directory: %%d
        set EXTRACTED_DIR=%%d
        goto copy_files
    )
    
    :copy_files
    echo Copying files from extracted directory...
    
    :: Copy only specific file types (exclude license/EULA files)
    echo Copying Python files...
    xcopy /y "%EXTRACTED_DIR%\*.py" "..\\" 
    
    echo Copying documentation files...
    xcopy /y "%EXTRACTED_DIR%\README.md" "..\\"
    
    echo Copying resource files...
    xcopy /y "%EXTRACTED_DIR%\*.jpg" "..\\"
    xcopy /y "%EXTRACTED_DIR%\*.ttf" "..\\"
    
    echo Copying script files...
    xcopy /y "%EXTRACTED_DIR%\deepsight-installer.bat" "..\\"
    xcopy /y "%EXTRACTED_DIR%\launch_deepsight.bat" "..\\"
    
    :: Cleanup
    cd ..
    rmdir /s /q temp_update
    
    echo.
    echo ===============================================
    echo Code has been successfully updated!
    echo ===============================================
)

:end_update
:: Restore configuration
if exist maintenance.json.bak (
    copy /y maintenance.json.bak maintenance.json
    echo Restored configuration from backup.
)

:: Clean up requirements file
if exist requirements.txt del requirements.txt

echo.
echo ===============================================
echo       Update process complete!
echo ===============================================
echo.
pause
