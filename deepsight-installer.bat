@echo off
setlocal enabledelayedexpansion

:: Set colors for fancy output
set "BLUE=[94m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "RESET=[0m"
set "BOLD=[1m"

:: Title with fancy formatting
cls
echo %BLUE%%BOLD%===============================================%RESET%
echo %BLUE%%BOLD%        DeepSight Studio Installation         %RESET%
echo %BLUE%%BOLD%===============================================%RESET%
echo.

:: Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%This script requires administrator privileges.%RESET%
    echo %YELLOW%Please right-click and select "Run as administrator".%RESET%
    echo.
    pause
    exit /b 1
)

:: Set BASE_DIR to current directory instead of user profile
set BASE_DIR=%~dp0
set BASE_DIR=%BASE_DIR:~0,-1%
echo %BOLD%Using current directory for installation: %BASE_DIR%%RESET%
echo.

:: Create DeepSightModel directory for weights
set MODEL_DIR=%BASE_DIR%\DeepSightModel
if not exist "%MODEL_DIR%" (
    echo %BOLD%Creating model weights directory...%RESET%
    mkdir "%MODEL_DIR%"
    echo %GREEN%Created directory: %MODEL_DIR%%RESET%
) else (
    echo %YELLOW%Model weights directory already exists: %MODEL_DIR%%RESET%
)

:: Force the script to continue past this point
echo %BOLD%Continuing with installation...%RESET%
echo.

:: Function to display a proper progress bar
:progress_bar
set /a fill=%~1*%~2/100
set "bar="
for /L %%i in (1,1,%~2) do (
    if %%i leq !fill! (
        set "bar=!bar!#"
    ) else (
        set "bar=!bar!."
    )
)
echo [!bar!] %~1%%
goto :eof

:: Check for Python 3.8+
echo %BOLD%Checking for Python installation...%RESET%
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo %YELLOW%Python not found. Installing Python 3.8...%RESET%
    
    :: Download Python installer using direct method
    echo %BOLD%Downloading Python 3.8.10...%RESET%
    call :progress_bar 0 50
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe', '%TEMP%\python-installer.exe')"
    call :progress_bar 100 50
    
    if not exist "%TEMP%\python-installer.exe" (
        echo %RED%Failed to download Python installer.%RESET%
        goto python_install_failed
    )
    
    echo %BOLD%Installing Python 3.8.10...%RESET%
    echo This may take a few minutes...
    call :progress_bar 0 50
    "%TEMP%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    call :progress_bar 100 50
    
    if %errorLevel% neq 0 (
        echo %RED%Error during Python installation.%RESET%
        goto python_install_failed
    )
    
    echo %BOLD%Python installation completed. Refreshing environment...%RESET%
    :: Refresh environment variables
    powershell -Command "[System.Environment]::SetEnvironmentVariable('Path',[System.Environment]::GetEnvironmentVariable('Path','Machine') + [System.Environment]::GetEnvironmentVariable('Path','User'),'Process')"
    
    :: Verify Python installation
    echo %BOLD%Verifying Python installation...%RESET%
    python --version >nul 2>&1
    if %errorLevel% neq 0 (
        :python_install_failed
        echo %RED%Python installation failed. Please install Python 3.8 or newer manually.%RESET%
        echo %YELLOW%Visit: https://www.python.org/downloads/%RESET%
        pause
        exit /b 1
    )
    
    echo %GREEN%Python installed successfully.%RESET%
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo %GREEN%Found Python !PYTHON_VERSION!%RESET%
    
    :: Check if version is at least 3.8
    for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
        set MAJOR=%%a
        set MINOR=%%b
    )
    
    if !MAJOR! LSS 3 (
        echo %RED%Python 3.8+ required, but found !PYTHON_VERSION!%RESET%
        goto python_install_failed
    ) else (
        if !MAJOR! EQU 3 (
            if !MINOR! LSS 8 (
                echo %RED%Python 3.8+ required, but found !PYTHON_VERSION!%RESET%
                goto python_install_failed
            )
        )
    )
)

:: Install required pip and virtualenv
echo.
echo %BOLD%Installing/upgrading pip and virtualenv...%RESET%
call :progress_bar 0 30
python -m pip install --upgrade pip virtualenv >nul 2>&1
call :progress_bar 100 30

:: Create and activate the virtual environment
echo.
echo %BOLD%Creating virtual environment "DeepSightStudio"...%RESET%
if exist venv (
    echo %YELLOW%Virtual environment already exists.%RESET%
    echo.
    set /p RECREATE="%BOLD%Do you want to recreate it? (y/n): %RESET%"
    if /i "!RECREATE!"=="y" (
        echo %BOLD%Removing existing virtual environment...%RESET%
        rmdir /s /q venv
        call :progress_bar 0 30
        python -m venv venv >nul 2>&1
        call :progress_bar 100 30
        echo %GREEN%Virtual environment recreated.%RESET%
    )
) else (
    call :progress_bar 0 30
    python -m venv venv >nul 2>&1
    call :progress_bar 100 30
    echo %GREEN%Virtual environment created.%RESET%
)

:: Activate the virtual environment
echo.
echo %BOLD%Activating virtual environment...%RESET%
call venv\Scripts\activate

:: Create requirements.txt file
echo.
echo %BOLD%Creating requirements.txt...%RESET%
echo # DeepSight Studio Requirements > requirements.txt
echo opencv-python>=4.5.3 >> requirements.txt
echo numpy>=1.20.0 >> requirements.txt
echo torch>=1.7.0 >> requirements.txt
echo torchvision>=0.8.1 >> requirements.txt
echo ultralytics>=8.0.0 >> requirements.txt
echo Pillow>=8.0.0 >> requirements.txt
echo pyserial>=3.5 >> requirements.txt
echo pyyaml>=5.1 >> requirements.txt
echo packaging >> requirements.txt
echo tqdm >> requirements.txt
echo %GREEN%requirements.txt created successfully.%RESET%

:: Install dependencies with progress animation
echo.
echo %BOLD%Installing dependencies...%RESET%
echo %YELLOW%This will take some time. Please be patient.%RESET%

echo %BOLD%Installing core packages...%RESET%
call :progress_bar 0 25
pip install numpy packaging tqdm >nul 2>&1
call :progress_bar 25 25

echo %BOLD%Installing PyTorch...%RESET%
call :progress_bar 25 50
pip install torch torchvision >nul 2>&1
call :progress_bar 50 50

echo %BOLD%Installing OpenCV and other dependencies...%RESET%
call :progress_bar 50 75
pip install opencv-python Pillow pyserial pyyaml >nul 2>&1
call :progress_bar 75 75

echo %BOLD%Installing Ultralytics (YOLOv8)...%RESET%
call :progress_bar 75 100
pip install ultralytics >nul 2>&1
call :progress_bar 100 100

echo %GREEN%Dependencies installed successfully.%RESET%

:: Clone YOLOv5 repository
if not exist yolov5 (
    echo.
    echo %BOLD%Setting up YOLOv5...%RESET%
    echo Checking if git is installed...
    git --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo %YELLOW%Git is not installed. Using direct download instead...%RESET%
        echo %BOLD%Downloading YOLOv5...%RESET%
        call :progress_bar 0 50
        powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/ultralytics/yolov5/archive/refs/heads/master.zip', '%BASE_DIR%\yolov5.zip')"
        call :progress_bar 50 50
        
        echo %BOLD%Extracting YOLOv5...%RESET%
        call :progress_bar 0 50
        powershell -Command "Expand-Archive -Path '%BASE_DIR%\yolov5.zip' -DestinationPath '%BASE_DIR%' -Force"
        if exist "%BASE_DIR%\yolov5-master" (
            ren "%BASE_DIR%\yolov5-master" "yolov5"
        )
        if exist "%BASE_DIR%\yolov5.zip" (
            del "%BASE_DIR%\yolov5.zip"
        )
        call :progress_bar 100 50
        
        if not exist "%BASE_DIR%\yolov5" (
            echo %RED%Warning: Failed to download YOLOv5 repository.%RESET%
            echo %YELLOW%Please download it manually from https://github.com/ultralytics/yolov5%RESET%
        ) else (
            echo %GREEN%YOLOv5 downloaded and extracted successfully.%RESET%
        )
    ) else (
        echo %BOLD%Cloning YOLOv5 repository...%RESET%
        call :progress_bar 0 50
        git clone https://github.com/ultralytics/yolov5.git >nul 2>&1
        call :progress_bar 100 50
        
        if %errorLevel% neq 0 (
            echo %RED%Warning: Failed to clone YOLOv5 repository.%RESET%
            echo %YELLOW%Please download it manually from https://github.com/ultralytics/yolov5%RESET%
        ) else (
            echo %GREEN%YOLOv5 repository cloned successfully.%RESET%
        )
    )
) else (
    echo %YELLOW%YOLOv5 repository already exists.%RESET%
)

:: Clone/install YOLOv8
if not exist yolov8 (
    echo.
    echo %BOLD%Setting up YOLOv8...%RESET%
    mkdir yolov8
    echo %GREEN%Created yolov8 directory for examples.%RESET%
) else (
    echo %YELLOW%YOLOv8 directory already exists.%RESET%
)

:: Download pre-trained weights for both YOLOv5 and YOLOv8
echo.
echo %BOLD%Downloading pre-trained model weights...%RESET%

:: Create subdirectories in the model folder
mkdir "%MODEL_DIR%\yolov5" 2>nul
mkdir "%MODEL_DIR%\yolov8" 2>nul

:: Download YOLOv5s weights if not exists
if not exist "%MODEL_DIR%\yolov5\yolov5s.pt" (
    echo %BOLD%Downloading YOLOv5s weights...%RESET%
    call :progress_bar 0 50
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt', '%MODEL_DIR%\yolov5\yolov5s.pt')"
    call :progress_bar 100 50
    
    if %errorLevel% neq 0 (
        echo %RED%Warning: Failed to download YOLOv5s weights.%RESET%
    ) else (
        echo %GREEN%YOLOv5s weights downloaded successfully.%RESET%
    )
) else (
    echo %YELLOW%YOLOv5s weights already exist.%RESET%
)

:: Download YOLOv8n weights if not exists
if not exist "%MODEL_DIR%\yolov8\yolov8n.pt" (
    echo %BOLD%Downloading YOLOv8n weights...%RESET%
    call :progress_bar 0 50
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt', '%MODEL_DIR%\yolov8\yolov8n.pt')"
    call :progress_bar 100 50
    
    if %errorLevel% neq 0 (
        echo %RED%Warning: Failed to download YOLOv8n weights.%RESET%
    ) else (
        echo %GREEN%YOLOv8n weights downloaded successfully.%RESET%
    )
) else (
    echo %YELLOW%YOLOv8n weights already exist.%RESET%
)

:: Download Orbitron font
if not exist "Orbitron-VariableFont_wght.ttf" (
    echo.
    echo %BOLD%Downloading Orbitron font...%RESET%
    call :progress_bar 0 50
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/google/fonts/raw/main/ofl/orbitron/Orbitron-VariableFont_wght.ttf', '%BASE_DIR%\Orbitron-VariableFont_wght.ttf')"
    call :progress_bar 100 50
    
    if %errorLevel% neq 0 (
        echo %RED%Warning: Failed to download Orbitron font.%RESET%
    ) else (
        echo %GREEN%Orbitron font downloaded successfully.%RESET%
        echo %BOLD%Installing font...%RESET%
        powershell -Command "$fonts = (New-Object -ComObject Shell.Application).Namespace(0x14); $fonts.CopyHere('%BASE_DIR%\Orbitron-VariableFont_wght.ttf')"
    )
) else (
    echo %YELLOW%Orbitron font already exists.%RESET%
)

:: Create default configuration
if not exist "maintenance.json" (
    echo.
    echo %BOLD%Creating default configuration file...%RESET%
    echo { > maintenance.json
    echo     "camera_settings": { >> maintenance.json
    echo         "selected_camera": 0, >> maintenance.json
    echo         "resolution": "640x480" >> maintenance.json
    echo     }, >> maintenance.json
    echo     "labeling_settings": { >> maintenance.json
    echo         "canny_threshold1": { >> maintenance.json
    echo             "min": 0, >> maintenance.json
    echo             "max": 750, >> maintenance.json
    echo             "value": 475 >> maintenance.json
    echo         }, >> maintenance.json
    echo         "canny_threshold2": { >> maintenance.json
    echo             "min": 0, >> maintenance.json
    echo             "max": 750, >> maintenance.json
    echo             "value": 400 >> maintenance.json
    echo         } >> maintenance.json
    echo     }, >> maintenance.json
    echo     "training_settings": { >> maintenance.json
    echo         "model_used": "YOLOv5", >> maintenance.json
    echo         "model_weights": "%MODEL_DIR%\yolov5\yolov5s.pt", >> maintenance.json
    echo         "data_config": "", >> maintenance.json
    echo         "img_size": "640", >> maintenance.json
    echo         "batch_size": "16", >> maintenance.json
    echo         "epochs": "50", >> maintenance.json
    echo         "project_name": "%MODEL_DIR%" >> maintenance.json
    echo     }, >> maintenance.json
    echo     "hardware_settings": { >> maintenance.json
    echo         "com_port": "COM1", >> maintenance.json
    echo         "baud_rate": "115200" >> maintenance.json
    echo     }, >> maintenance.json
    echo     "video_width": 640, >> maintenance.json
    echo     "video_height": 480 >> maintenance.json
    echo } >> maintenance.json
    echo %GREEN%Default configuration file created.%RESET%
)

:: Create directory structure for training data
echo.
echo %BOLD%Creating training data directories...%RESET%
mkdir training_data 2>nul
mkdir training_data\dominos 2>nul
mkdir training_data\cards 2>nul
mkdir training_data\dice 2>nul
echo %GREEN%Training data directories created.%RESET%

:: Create launcher batch file
echo.
echo %BOLD%Creating launcher script...%RESET%
echo @echo off > launch_deepsight.bat
echo call "%BASE_DIR%\venv\Scripts\activate" >> launch_deepsight.bat
echo echo Starting DeepSight Studio... >> launch_deepsight.bat
echo echo Model weights directory: %MODEL_DIR% >> launch_deepsight.bat
echo python gui.py >> launch_deepsight.bat
echo pause >> launch_deepsight.bat
echo %GREEN%Launcher script created.%RESET%

:: Create desktop shortcut
echo.
echo %BOLD%Creating desktop shortcut...%RESET%
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\DeepSight Studio.lnk'); $Shortcut.TargetPath = '%BASE_DIR%\launch_deepsight.bat'; $Shortcut.WorkingDirectory = '%BASE_DIR%'; $Shortcut.Save()"
echo %GREEN%Desktop shortcut created.%RESET%

echo.
echo %BLUE%%BOLD%===============================================%RESET%
echo %GREEN%%BOLD%       Installation Process Complete!        %RESET%
echo %BLUE%%BOLD%===============================================%RESET%
echo.
echo %BOLD%DeepSight Studio has been installed to:%RESET%
echo %GREEN%%BASE_DIR%%RESET%
echo.
echo %BOLD%Model weights are stored in:%RESET%
echo %GREEN%%MODEL_DIR%%RESET%
echo.
echo %YELLOW%%BOLD%To start the application:%RESET%
echo %YELLOW%1. Double-click the "DeepSight Studio" shortcut on your desktop, or%RESET%
echo %YELLOW%2. Run launch_deepsight.bat from the installation directory%RESET%
echo.
echo Press any key to exit...
pause > nul
