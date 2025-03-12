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

:: Set BASE_DIR to current directory
set BASE_DIR=%~dp0
set BASE_DIR=%BASE_DIR:~0,-1%
echo Using current directory for installation: %BASE_DIR%
echo.

:: Remove existing venv if it exists
if exist "%BASE_DIR%\venv" (
    echo Removing existing virtual environment...
    rmdir /s /q "%BASE_DIR%\venv"
)

:: Check Python installation
echo Checking Python installation...
where python > nul 2>&1
if %errorLevel% neq 0 (
    echo Python not found. Please install Python 3.8 or newer.
    pause
    exit /b 1
)

python --version > version.txt 2>&1
set /p PYTHON_VERSION=<version.txt
del version.txt
echo Found %PYTHON_VERSION%

:: Create a new virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
if %errorLevel% neq 0 (
    echo Failed to create virtual environment.
    echo Make sure you have venv module installed.
    echo Try: pip install virtualenv
    pause
    exit /b 1
)

:: Activate the virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

:: Install dependencies using pip directly
echo.
echo Installing dependencies...
echo This may take a few minutes...

pip install --upgrade pip

echo Installing core dependencies...
pip install opencv-python
pip install numpy
pip install Pillow
pip install pyserial
pip install pyyaml
pip install tqdm

echo Installing PyTorch...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

echo Installing ultralytics...
pip install ultralytics

:: Verify installations
echo.
echo Verifying installations...
python -c "import sys; print('Python version:', sys.version)"
python -c "import PIL; print('Pillow installed successfully')" || echo WARNING: Pillow installation failed
python -c "import cv2; print('OpenCV installed successfully')" || echo WARNING: OpenCV installation failed
python -c "import torch; print('PyTorch installed successfully')" || echo WARNING: PyTorch installation failed
python -c "import numpy; print('NumPy installed successfully')" || echo WARNING: NumPy installation failed

:: Download YOLOv5
echo.
echo Downloading YOLOv5...
if exist yolov5 (
    echo Removing existing YOLOv5 directory...
    rmdir /s /q yolov5
)

echo Using curl to download YOLOv5...
curl -L -o yolov5.zip https://github.com/ultralytics/yolov5/archive/refs/heads/master.zip
if %errorLevel% neq 0 (
    echo Failed to download YOLOv5. Please check your internet connection.
    pause
    exit /b 1
)

echo Extracting YOLOv5...
powershell -Command "Expand-Archive -Force -Path 'yolov5.zip' -DestinationPath '.'"
if exist yolov5-master (
    rename yolov5-master yolov5
)
del yolov5.zip

:: Create YOLOv8 directory
echo.
echo Setting up YOLOv8...
if not exist yolov8 (
    mkdir yolov8
)

:: Download model weights
echo.
echo Downloading model weights...
if not exist "yolov5\yolov5s.pt" (
    curl -L -o yolov5\yolov5s.pt https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt
    if %errorLevel% neq 0 (
        echo Failed to download YOLOv5 weights.
    )
)

if not exist "yolov8\yolov8n.pt" (
    curl -L -o yolov8\yolov8n.pt https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
    if %errorLevel% neq 0 (
        echo Failed to download YOLOv8 weights.
    )
)

:: Download Orbitron font
echo.
echo Downloading Orbitron font...
if not exist "Orbitron-VariableFont_wght.ttf" (
    curl -L -o Orbitron-VariableFont_wght.ttf https://github.com/google/fonts/raw/main/ofl/orbitron/Orbitron-VariableFont_wght.ttf
    if %errorLevel% neq 0 (
        echo Failed to download Orbitron font.
    ) else (
        echo Installing font...
        powershell -Command "$fonts = (New-Object -ComObject Shell.Application).Namespace(0x14); $fonts.CopyHere('%BASE_DIR%\Orbitron-VariableFont_wght.ttf')"
    )
)

:: Create maintenance.json
echo.
echo Creating maintenance.json...
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
echo         "model_weights": "yolov5s.pt",
echo         "data_config": "",
echo         "img_size": "640",
echo         "batch_size": "16",
echo         "epochs": "50",
echo         "project_name": "runs/train"
echo     },
echo     "hardware_settings": {
echo         "com_port": "COM1",
echo         "baud_rate": "115200"
echo     },
echo     "video_width": 640,
echo     "video_height": 480
echo }
) > maintenance.json

:: Create required directories
echo.
echo Creating required directories...
if not exist "yolo_training_data" (
    mkdir yolo_training_data
    mkdir yolo_training_data\images
    mkdir yolo_training_data\labels
)

if not exist "training_data" (
    mkdir training_data
    mkdir training_data\dominos
    mkdir training_data\cards
    mkdir training_data\dice
)

:: Create launcher script
echo.
echo Creating launcher script...
(
echo @echo off
echo cd /d %%~dp0
echo.
echo echo ===== DeepSight Studio Launcher =====
echo echo Current directory: %%CD%%
echo.
echo echo Activating virtual environment...
echo call venv\Scripts\activate.bat
echo.
echo echo Checking dependencies...
echo python -c "import PIL" 2>nul
echo if errorlevel 1 (
echo     echo Installing missing Pillow package...
echo     pip install Pillow
echo ^)
echo.
echo python -c "import cv2" 2>nul
echo if errorlevel 1 (
echo     echo Installing missing OpenCV package...
echo     pip install opencv-python
echo ^)
echo.
echo python -c "import torch" 2>nul
echo if errorlevel 1 (
echo     echo Installing missing PyTorch package...
echo     pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
echo ^)
echo.
echo echo ===== Launching DeepSight Studio =====
echo python gui.py
echo.
echo if errorlevel 1 (
echo     echo ERROR: Failed to launch DeepSight Studio.
echo     echo Please check the error messages above.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo pause
) > launch_deepsight.bat

:: Create desktop shortcut
echo.
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\DeepSight Studio.lnk'); $Shortcut.TargetPath = '%BASE_DIR%\launch_deepsight.bat'; $Shortcut.WorkingDirectory = '%BASE_DIR%'; $Shortcut.Save()"

echo.
echo ===============================================
echo       Installation Complete!
echo ===============================================
echo.
echo To launch DeepSight Studio:
echo 1. Double-click the desktop shortcut, or
echo 2. Run launch_deepsight.bat from this directory
echo.

echo Launching DeepSight Studio...
start launch_deepsight.bat

pause
