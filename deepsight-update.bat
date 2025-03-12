@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo        DeepSight Studio Updater
echo ===============================================
echo.

:: Set absolute path for current directory
set BASE_DIR=%~dp0
cd /d "%BASE_DIR%"
echo Current directory: %CD%

:: Backup existing configuration
echo Creating backup of maintenance.json...
if exist maintenance.json (
    copy maintenance.json maintenance.json.bak
    echo Backup created: maintenance.json.bak
)

:: Activate virtual environment
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found.
    echo Please run the installer first.
    pause
    exit /b 1
)

:: Check all currently installed packages
echo.
echo Current installed packages:
"%CD%\venv\Scripts\pip" list

:: Offer dependency updates
echo.
echo ===============================================
echo         Dependency Update Options
echo ===============================================
echo Would you like to:
echo 1. Update all dependencies to latest versions
echo 2. Check for updates but ask before installing
echo 3. Skip dependency updates
set /p UPDATE_CHOICE=Enter your choice (1-3): 

if "%UPDATE_CHOICE%"=="1" (
    echo.
    echo Updating all dependencies...
    "%CD%\venv\Scripts\pip" install --upgrade pip
    
    :: Get a list of all installed packages and update them
    echo Updating all packages...
    for /f "tokens=1" %%i in ('"%CD%\venv\Scripts\pip" list --format=freeze ^| findstr /V "^-e"') do (
        for /f "tokens=1 delims==" %%j in ("%%i") do (
            if "%%j"=="torch" (
                echo Updating %%j...
                "%CD%\venv\Scripts\pip" install --upgrade --no-cache-dir %%j --index-url https://download.pytorch.org/whl/cpu
            ) else if "%%j"=="torchvision" (
                echo Updating %%j...
                "%CD%\venv\Scripts\pip" install --upgrade --no-cache-dir %%j --index-url https://download.pytorch.org/whl/cpu
            ) else (
                echo Updating %%j...
                "%CD%\venv\Scripts\pip" install --upgrade %%j
            )
        )
    )
    echo All dependencies updated.
) else if "%UPDATE_CHOICE%"=="2" (
    :: Check for pip updates first
    echo.
    echo Checking for pip updates...
    "%CD%\venv\Scripts\pip" list --outdated | findstr "pip"
    if !errorlevel! equ 0 (
        set /p CHOICE=Update pip? (y/n): 
        if /i "!CHOICE!"=="y" (
            "%CD%\venv\Scripts\pip" install --upgrade pip
        )
    ) else (
        echo pip is up to date.
    )
    
    :: Check all other packages dynamically
    echo.
    echo Checking for outdated packages...
    for /f "tokens=1" %%i in ('"%CD%\venv\Scripts\pip" list --outdated --format=freeze ^| findstr /V "^-e"') do (
        for /f "tokens=1 delims==" %%j in ("%%i") do (
            echo Package %%j has an update available.
            set /p CHOICE=Update %%j? (y/n): 
            if /i "!CHOICE!"=="y" (
                if "%%j"=="torch" (
                    "%CD%\venv\Scripts\pip" install --upgrade --no-cache-dir %%j --index-url https://download.pytorch.org/whl/cpu
                ) else if "%%j"=="torchvision" (
                    "%CD%\venv\Scripts\pip" install --upgrade --no-cache-dir %%j --index-url https://download.pytorch.org/whl/cpu
                ) else (
                    "%CD%\venv\Scripts\pip" install --upgrade %%j
                )
            )
        )
    )
    
    echo Done checking for updates.
) else (
    echo Skipping dependency updates.
)

:: Code update options
echo.
echo ===============================================
echo         Code Update Options
echo ===============================================
echo Would you like to:
echo 1. Download the latest code from GitHub
echo 2. Skip code updates
set /p CODE_CHOICE=Enter your choice (1-2): 

if "%CODE_CHOICE%"=="1" (
    echo.
    echo Downloading latest code from GitHub...
    
    :: Create a temporary directory for the download
    mkdir temp_update
    cd temp_update
    
    :: Download the latest code
    echo Downloading latest code...
    curl -L -o deepsight.zip https://github.com/yourusername/DeepSightStudio/archive/refs/heads/main.zip
    if errorlevel 1 (
        echo Failed to download the latest code.
        cd ..
        rmdir /s /q temp_update
        pause
        exit /b 1
    )
    
    :: Extract the downloaded zip
    echo Extracting files...
    powershell -Command "Expand-Archive -Force -Path 'deepsight.zip' -DestinationPath '.'"
    if errorlevel 1 (
        echo Failed to extract the code.
        cd ..
        rmdir /s /q temp_update
        pause
        exit /b 1
    )
    
    :: Find the extracted directory name
    for /d %%d in (*) do (
        set EXTRACTED_DIR=%%d
    )
    
    :: Copy code files, preserving configurations
    echo Copying new code files...
    
    :: Copy Python files
    copy "!EXTRACTED_DIR!\*.py" "..\*.py" /y
    
    :: Copy README and other documentation
    copy "!EXTRACTED_DIR!\README.md" "..\" /y
    copy "!EXTRACTED_DIR!\LICENSE" "..\" /y
    
    :: YOLOv5 directory handling
    if exist "..\yolov5" (
        echo Updating YOLOv5 repository...
        if exist "!EXTRACTED_DIR!\yolov5" (
            xcopy "!EXTRACTED_DIR!\yolov5" "..\yolov5" /E /H /C /I /Y
        )
    )
    
    :: Go back to the original directory and clean up
    cd ..
    rmdir /s /q temp_update
    
    echo Code update completed.
) else (
    echo Skipping code updates.
)

:: Restore configuration
if exist maintenance.json.bak (
    echo.
    echo Restoring configuration...
    copy maintenance.json.bak maintenance.json /y
    echo Configuration restored.
)

echo.
echo ===============================================
echo        Update Process Complete
echo ===============================================
echo.
echo DeepSight Studio has been updated.
echo Run launch_deepsight.bat to start the application.
echo.

pause
