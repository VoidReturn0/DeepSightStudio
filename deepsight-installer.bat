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
echo.@echo off
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

:: Use BASE_DIR as the model weights directory
set MODEL_DIR=%BASE_DIR%
echo Using installation directory for model weights: %MODEL_DIR%
echo.

:: Verify Python executable and permissions
echo Checking Python installation and permissions...
where python > temp_python_path.txt
set /p PYTHON_PATH=<temp_python_path.txt
del temp_python_path.txt

echo Found Python at: %PYTHON_PATH%
echo Testing Python permissions...
python -c "print('Python access test successful')" > nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Cannot execute Python. Please check your permissions.
    pause
    exit /b 1
)

:: Check for Python 3.8+
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

:: First remove any existing venv directory if it exists
if exist "%BASE_DIR%\venv" (
    echo Removing existing virtual environment...
    rmdir /s /q "%BASE_DIR%\venv"
)

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
pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo Failed to install one or more dependencies.
    echo Try installing them individually for better error reporting.
    
    :: Try installing packages individually to identify problematic ones
    echo.
    echo Installing packages individually...
    for %%p in (opencv-python numpy torch torchvision ultralytics Pillow pyserial pyyaml packaging tqdm) do (
        echo Installing %%p...
        pip install %%p
        if !errorLevel! neq 0 (
            echo ERROR: Failed to install %%p
        ) else (
            echo %%p installed successfully.
        )
    )
    
    echo.
    echo Some dependencies failed to install. Consider installing them manually.
    pause
    exit /b 1
)
echo Dependencies installed successfully.

:: Verify installations (more comprehensive)
echo.
echo Verifying installations...
python -c "import cv2; print('OpenCV installed successfully, version:', cv2.__version__)"
if %errorLevel% neq 0 (
    echo WARNING: OpenCV verification failed.
)

python -c "import numpy; print('NumPy installed successfully, version:', numpy.__version__)"
if %errorLevel% neq 0 (
    echo WARNING: NumPy verification failed.
)

python -c "import torch; print('PyTorch installed successfully, version:', torch.__version__)"
if %errorLevel% neq 0 (
    echo WARNING: PyTorch verification failed.
)

python -c "import PIL; print('Pillow installed successfully, version:', PIL.__version__)"
if %errorLevel% neq 0 (
    echo WARNING: Pillow verification failed.
)

python -c "import serial; print('PySerial installed successfully, version:', serial.VERSION)"
if %errorLevel% neq 0 (
    echo WARNING: PySerial verification failed.
)

python -c "import yaml; print('PyYAML installed successfully, version:', yaml.__version__)"
if %errorLevel% neq 0 (
    echo WARNING: PyYAML verification failed.
)

:: Clone YOLOv5 repository with improved reliability
if not exist yolov5 (
    echo.
    echo Setting up YOLOv5...
    echo Checking if git is installed...
    git --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo Git is not installed. Using direct download instead...
        echo Downloading YOLOv5... (0%)
        powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/ultralytics/yolov5/archive/refs/heads/master.zip', '%BASE_DIR%\yolov5.zip')"
        if %errorLevel% neq 0 (
            echo ERROR: Failed to download YOLOv5 repository.
            echo Please download it manually from https://github.com/ultralytics/yolov5
        ) else {
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
                echo WARNING: Failed to extract YOLOv5 repository.
            ) else (
                echo YOLOv5 downloaded and extracted successfully.
            )
        }
    ) else (
        echo Cloning YOLOv5 repository... (0%)
        git clone https://github.com/ultralytics/yolov5.git
        echo Cloning complete! (100%)
        
        if %errorLevel% neq 0 (
            echo WARNING: Failed to clone YOLOv5 repository.
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

:: Create yolo_training_data directory for use with image_labeling.py
if not exist "yolo_training_data" (
    echo.
    echo Creating YOLOv5 training data directory...
    mkdir yolo_training_data\images
    mkdir yolo_training_data\labels
    echo Created yolo_training_data directories.
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
        echo WARNING: Failed to download YOLOv5s weights.
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
        echo WARNING: Failed to download YOLOv8n weights.
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
        echo WARNING: Failed to download Orbitron font.
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
echo echo ===== DeepSight Studio Launcher =====
echo echo Current directory: %%CD%%
echo.
echo REM Activate the virtual environment from the venv folder
echo if exist venv\Scripts\activate.bat (
echo     echo Activating virtual environment...
echo     call venv\Scripts\activate.bat
echo     if errorlevel 1 (
echo         echo ERROR: Failed to activate virtual environment.
echo         pause
echo         exit /b 1
echo     ^)
echo ^) else (
echo     echo ERROR: Virtual environment not found at %%CD%%\venv\Scripts\activate.bat
echo     echo Please run the installer first.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Debug: Print the active Python executable and version
echo echo.
echo echo === Environment Debug Info ===
echo python -c "import sys; print('Using Python:', sys.executable^)"
echo python -c "import sys; print('Python version:', sys.version^)"
echo.
echo REM Verify critical dependencies
echo echo.
echo echo === Checking Dependencies ===
echo python -c "import cv2; print('OpenCV version:', cv2.__version__^)" 2^>nul
echo if errorlevel 1 (
echo     echo WARNING: OpenCV not properly installed. Some features may not work.
echo ^)
echo.
echo python -c "import torch; print('PyTorch version:', torch.__version__^)" 2^>nul
echo if errorlevel 1 (
echo     echo WARNING: PyTorch not properly installed. Training features will not work.
echo ^)
echo.
echo python -c "import PIL; print('Pillow version:', PIL.__version__^)" 2^>nul
echo if errorlevel 1 (
echo     echo WARNING: Pillow not properly installed. Image processing will be limited.
echo ^)
echo.
echo echo.
echo echo === Launching DeepSight Studio ===
echo REM Run the gui.py script
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

echo Press any key to exit...
pause > nul
