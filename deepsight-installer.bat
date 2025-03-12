@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo        DeepSight Studio Installation
echo ===============================================
echo.

:: Set absolute path for current directory
set BASE_DIR=%~dp0
cd /d "%BASE_DIR%"
echo Using current directory for installation: %CD%
echo.

:: Clean up existing directories
echo Cleaning up existing directories...
if exist venv (
    echo Removing existing virtual environment...
    rmdir /s /q venv
)
if exist yolov5 (
    echo Removing existing YOLOv5 directory...
    rmdir /s /q yolov5
)
if exist yolov8 (
    echo Removing existing YOLOv8 directory...
    rmdir /s /q yolov8
)
echo.

:: Check Python installation
echo Checking Python installation...
python --version > version.txt 2>&1
set /p PYTHON_VERSION=<version.txt
del version.txt
echo Found %PYTHON_VERSION%
echo.

:: Create a new virtual environment
echo Creating virtual environment...
python -m venv "%CD%\venv"
if errorlevel 1 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
)
echo.

:: Activate the virtual environment
echo Activating virtual environment...
call "%CD%\venv\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)
echo.

:: Verify we're using the venv Python
echo Verifying virtual environment...
python -c "import sys; print('Using Python:', sys.executable)"
if errorlevel 1 (
    echo Failed to verify virtual environment.
    pause
    exit /b 1
)

:: Install dependencies - make sure to use the venv pip directly
echo Installing dependencies...
echo This may take a few minutes...

"%CD%\venv\Scripts\pip" install --upgrade pip

echo Installing core dependencies...
"%CD%\venv\Scripts\pip" install opencv-python numpy Pillow pyserial pyyaml tqdm
echo Installing PyTorch...
"%CD%\venv\Scripts\pip" install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
echo Installing ultralytics...
"%CD%\venv\Scripts\pip" install ultralytics
echo.

:: Verify installations
echo Verifying installations...
python -c "import sys; print('Python version:', sys.version)"
python -c "import PIL; print('Pillow installed successfully')" || echo WARNING: Pillow installation failed
python -c "import cv2; print('OpenCV installed successfully')" || echo WARNING: OpenCV installation failed
python -c "import torch; print('PyTorch installed successfully')" || echo WARNING: PyTorch installation failed
python -c "import numpy; print('NumPy installed successfully')" || echo WARNING: NumPy installation failed
python -c "import serial; print('PySerial installed successfully')" || echo WARNING: PySerial installation failed
echo.

:: Download YOLOv5
echo Downloading YOLOv5...
curl -L -o yolov5.zip https://github.com/ultralytics/yolov5/archive/refs/heads/master.zip
if errorlevel 1 (
    echo Failed to download YOLOv5. Please check your internet connection.
    pause
    exit /b 1
)

echo Extracting YOLOv5...
powershell -Command "Expand-Archive -Force -Path 'yolov5.zip' -DestinationPath '%CD%'"
if exist yolov5-master (
    rename yolov5-master yolov5
)
del yolov5.zip
echo.

:: Create YOLOv8 directory
echo Setting up YOLOv8...
mkdir "%CD%\yolov8"
echo.

:: Download model weights
echo Downloading model weights...
curl -L -o "%CD%\yolov5\yolov5s.pt" https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt
curl -L -o "%CD%\yolov8\yolov8n.pt" https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
echo.

:: Create maintenance.json with absolute paths
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
echo         "model_weights": "%CD:\=\\%\\yolov5\\yolov5s.pt",
echo         "data_config": "",
echo         "img_size": "640",
echo         "batch_size": "16",
echo         "epochs": "50",
echo         "project_name": "%CD:\=\\%\\runs\\train"
echo     },
echo     "hardware_settings": {
echo         "com_port": "COM1",
echo         "baud_rate": "115200"
echo     },
echo     "video_width": 640,
echo     "video_height": 480
echo }
) > maintenance.json
echo.

:: Create required directories
echo Creating required directories...
mkdir "%CD%\yolo_training_data\images" 2>nul
mkdir "%CD%\yolo_training_data\labels" 2>nul
mkdir "%CD%\training_data\dominos" 2>nul
mkdir "%CD%\training_data\cards" 2>nul
mkdir "%CD%\training_data\dice" 2>nul
mkdir "%CD%\runs\train" 2>nul
echo.

:: Create launcher script with absolute paths and package verification
echo Creating launcher script...
(
echo @echo off
echo REM Store the absolute path of the batch file directory
echo set SCRIPT_DIR=%%~dp0
echo cd /d "%%SCRIPT_DIR%%"
echo.
echo echo ===== DeepSight Studio Launcher =====
echo echo Current directory: %%CD%%
echo.
echo REM Activate the virtual environment from the venv folder
echo if exist venv\Scripts\activate.bat ^(
echo     echo Activating virtual environment...
echo     call venv\Scripts\activate.bat
echo ^) else ^(
echo     echo ERROR: Virtual environment not found at %%CD%%\venv\Scripts\activate.bat
echo     echo Please run the installer first.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo Checking dependencies...
echo.
echo python -c "import PIL" 2^>nul
echo if errorlevel 1 ^(
echo     echo Installing missing Pillow package...
echo     "%%CD%%\venv\Scripts\pip" install Pillow
echo ^)
echo.
echo python -c "import cv2" 2^>nul
echo if errorlevel 1 ^(
echo     echo Installing missing OpenCV package...
echo     "%%CD%%\venv\Scripts\pip" install opencv-python
echo ^)
echo.
echo python -c "import torch" 2^>nul
echo if errorlevel 1 ^(
echo     echo Installing missing PyTorch package...
echo     "%%CD%%\venv\Scripts\pip" install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
echo ^)
echo.
echo python -c "import serial" 2^>nul
echo if errorlevel 1 ^(
echo     echo Installing missing PySerial package...
echo     "%%CD%%\venv\Scripts\pip" install pyserial
echo ^)
echo.
echo echo ===== Launching DeepSight Studio =====
echo python "%%CD%%\gui.py"
echo.
echo if errorlevel 1 ^(
echo     echo ERROR: Failed to launch DeepSight Studio.
echo     echo Please check the error messages above.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo pause
) > launch_deepsight.bat
echo.

:: Create desktop shortcut with absolute path
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\DeepSight Studio.lnk'); $Shortcut.TargetPath = '%CD%\launch_deepsight.bat'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.Save()"
echo.

echo ===============================================
echo       Installation Complete!
echo ===============================================
echo.
echo To launch DeepSight Studio:
echo 1. Double-click the desktop shortcut, or
echo 2. Run launch_deepsight.bat from this directory
echo.

echo Would you like to launch DeepSight Studio now? (Y/N)
set /p LAUNCH_NOW=
if /i "%LAUNCH_NOW%"=="Y" (
    start "" "%CD%\launch_deepsight.bat"
)

pause
