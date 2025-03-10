@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo        DeepSight Studio Installation
echo ===============================================
echo.

:: Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script requires administrator privileges.
    echo Please right-click and select "Run as administrator".
    echo.
    pause
    exit /b 1
)

:: Set BASE_DIR to current directory (removing any trailing backslash)
set BASE_DIR=%~dp0
set BASE_DIR=%BASE_DIR:~0,-1%
echo Using current directory for installation: %BASE_DIR%
echo.

:: Use BASE_DIR as the model weights directory (creation will be handled later by the GUI)
set MODEL_DIR=%BASE_DIR%
echo Using installation directory for model weights: %MODEL_DIR%
echo.

echo Continuing with installation...
echo.

:: Check for Python 3.8+
echo Checking for Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Python not found. Please install Python 3.8 or newer manually.
    echo Visit: https://www.python.org/downloads/
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo Found Python !PYTHON_VERSION!
    
    :: Check if version is at least 3.8
    for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
        set MAJOR=%%a
        set MINOR=%%b
    )
    
    if !MAJOR! LSS 3 (
        echo Python 3.8+ required, but found !PYTHON_VERSION!
        pause
        exit /b 1
    ) else (
        if !MAJOR! EQU 3 (
            if !MINOR! LSS 8 (
                echo Python 3.8+ required, but found !PYTHON_VERSION!
                pause
                exit /b 1
            )
        )
    )
)

:: Create and activate the virtual environment
echo.
echo Creating virtual environment "DeepSightStudio"...
python -m venv "%BASE_DIR%\venv"
if %errorLevel% neq 0 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
)
echo Virtual environment created.

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

:: Install/upgrading pip and virtualenv
echo.
echo Installing/upgrading pip and virtualenv...
python -m pip install --upgrade pip
python -m pip install --upgrade virtualenv
echo Done.

:: Create requirements.txt file
echo.
echo Creating requirements.txt...
(
echo # DeepSight Studio Requirements
echo opencv-python>=4.5.3
echo numpy>=1.20.0
echo torch>=1.7.0
echo torchvision>=0.8.1
echo ultralytics>=8.0.0
echo Pillow>=9.5.0
echo pyserial>=3.5
echo pyyaml>=5.1
echo packaging
echo tqdm
) > requirements.txt
echo requirements.txt created successfully.

:: Install dependencies with improved progress tracking
echo.
echo Installing dependencies...
echo This will take some time. Please be patient.
pip install -r requirements.txt -v
if %errorLevel% neq 0 (
    echo Failed to install one or more dependencies.
    pause
    exit /b 1
)
echo Dependencies installed successfully.

:: Verify installations
echo.
echo Verifying installation of pyserial...
python -c "import serial; print('Serial module installed successfully')"
if %errorLevel% neq 0 (
    echo Warning: PySerial verification failed.
)

echo Verifying installation of Pillow...
python -c "import PIL; print('Pillow version: ' + PIL.__version__)"
if %errorLevel% neq 0 (
    echo Warning: Pillow verification failed.
)

:: Clone YOLOv5 repository
if not exist yolov5 (
    echo.
    echo Setting up YOLOv5...
    echo Checking if git is installed...
    git --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo Git is not installed. Using direct download instead...
        echo Downloading YOLOv5... (0%)
        powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/ultralytics/yolov5/archive/refs/heads/master.zip', '%BASE_DIR%\yolov5.zip')"
        echo Download complete! (100%)
        
        echo Extracting YOLOv5... (0%)
        powershell -Command "Expand-Archive -Path '%BASE_DIR%\yolov5.zip' -DestinationPath '%BASE_DIR%' -Force"
        if exist "%BASE_DIR%\yolov5-master" (
            ren "%BASE_DIR%\yolov5-master" "yolov5"
        )
        if exist "%BASE_DIR%\yolov5.zip" (
            del "%BASE_DIR%\yolov5.zip"
        )
        echo Extraction complete! (100%)
        
        if not exist "%BASE_DIR%\yolov5" (
            echo Warning: Failed to download YOLOv5 repository.
            echo Please download it manually from https://github.com/ultralytics/yolov5
        ) else (
            echo YOLOv5 downloaded and extracted successfully.
        )
    ) else (
        echo Cloning YOLOv5 repository... (0%)
        git clone https://github.com/ultralytics/yolov5.git
        echo Cloning complete! (100%)
        
        if %errorLevel% neq 0 (
            echo Warning: Failed to clone YOLOv5 repository.
            echo Please download it manually from https://github.com/ultralytics/yolov5
        ) else (
            echo YOLOv5 repository cloned successfully.
        )
    )
) else (
    echo YOLOv5 repository already exists.
)

:: Clone/install YOLOv8
if not exist yolov8 (
    echo.
    echo Setting up YOLOv8...
    mkdir yolov8
    echo Created yolov8 directory for examples.
) else (
    echo YOLOv8 directory already exists.
)

:: Download pre-trained weights for both YOLOv5 and YOLOv8
echo.
echo Downloading pre-trained model weights...

:: Create subdirectories for weights inside the base directory
mkdir "%MODEL_DIR%\yolov5" 2>nul
mkdir "%MODEL_DIR%\yolov8" 2>nul

:: Download YOLOv5s weights if not exists
if not exist "%MODEL_DIR%\yolov5\yolov5s.pt" (
    echo Downloading YOLOv5s weights... (0%)
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt', '%MODEL_DIR%\yolov5\yolov5s.pt')"
    echo Download complete! (100%)
    
    if %errorLevel% neq 0 (
        echo Warning: Failed to download YOLOv5s weights.
    ) else (
        echo YOLOv5s weights downloaded successfully.
    )
) else (
    echo YOLOv5s weights already exist.
)

:: Download YOLOv8n weights if not exists
if not exist "%MODEL_DIR%\yolov8\yolov8n.pt" (
    echo Downloading YOLOv8n weights... (0%)
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt', '%MODEL_DIR%\yolov8\yolov8n.pt')"
    echo Download complete! (100%)
    
    if %errorLevel% neq 0 (
        echo Warning: Failed to download YOLOv8n weights.
    ) else (
        echo YOLOv8n weights downloaded successfully.
    )
) else (
    echo YOLOv8n weights already exist.
)

:: Download Orbitron font
if not exist "Orbitron-VariableFont_wght.ttf" (
    echo.
    echo Downloading Orbitron font... (0%)
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/google/fonts/raw/main/ofl/orbitron/Orbitron-VariableFont_wght.ttf', '%BASE_DIR%\Orbitron-VariableFont_wght.ttf')"
    echo Download complete! (100%)
    
    if %errorLevel% neq 0 (
        echo Warning: Failed to download Orbitron font.
    ) else (
        echo Orbitron font downloaded successfully.
        echo Installing font...
        powershell -Command "$fonts = (New-Object -ComObject Shell.Application).Namespace(0x14); $fonts.CopyHere('%BASE_DIR%\Orbitron-VariableFont_wght.ttf')"
    )
) else (
    echo Orbitron font already exists.
)

:: Create default configuration
if not exist "maintenance.json" (
    echo.
    echo Creating default configuration file...
    (
    echo {
    echo     "camera_settings": {
    echo         "selected_camera": 0,
    echo         "resolution": "640x480"
    echo     },
    echo     "labeling_settings": {
    echo         "canny_threshold1": {
    echo             "min": 0,
    echo             "max": 750,
    echo             "value": 475
    echo         },
    echo         "canny_threshold2": {
    echo             "min": 0,
    echo             "max": 750,
    echo             "value": 400
    echo         }
    echo     },
    echo     "training_settings": {
    echo         "model_used": "YOLOv5",
    echo         "model_weights": "%MODEL_DIR%\yolov5\yolov5s.pt",
    echo         "data_config": "",
    echo         "img_size": "640",
    echo         "batch_size": "16",
    echo         "epochs": "50",
    echo         "project_name": "%MODEL_DIR%"
    echo     },
    echo     "hardware_settings": {
    echo         "com_port": "COM1",
    echo         "baud_rate": "115200"
    echo     },
    echo     "video_width": 640,
    echo     "video_height": 480
    echo }
    ) > maintenance.json
    echo Default configuration file created.
)

:: Create directory structure for training data
echo.
echo Creating training data directories...
mkdir training_data 2>nul
mkdir training_data\dominos 2>nul
mkdir training_data\cards 2>nul
mkdir training_data\dice 2>nul
echo Training data directories created.

:: Create launcher batch file with proper working directory set
echo.
echo Creating launcher script...
(
echo @echo off
echo cd /d %BASE_DIR%
echo call "%BASE_DIR%\venv\Scripts\activate.bat"
echo echo Starting DeepSight Studio...
echo echo Model weights directory: %MODEL_DIR%
echo python gui.py
echo pause
) > launch_deepsight.bat
echo Launcher script created.

:: Create desktop shortcut
echo.
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\DeepSight Studio.lnk'); $Shortcut.TargetPath = '%BASE_DIR%\launch_deepsight.bat'; $Shortcut.WorkingDirectory = '%BASE_DIR%'; $Shortcut.Save()"
echo Desktop shortcut created.

echo.
echo ===============================================
echo       Installation Process Complete!
echo ===============================================
echo.
echo DeepSight Studio has been installed to:
echo %BASE_DIR%
echo.
echo Model weights are stored in:
echo %MODEL_DIR%
echo.
echo To start the application:
echo 1. Double-click the "DeepSight Studio" shortcut on your desktop, or
echo 2. Run launch_deepsight.bat from the installation directory
echo.

:: Launch the application automatically
echo Launching DeepSight Studio...
start launch_deepsight.bat

echo Press any key to exit...
pause > nul
