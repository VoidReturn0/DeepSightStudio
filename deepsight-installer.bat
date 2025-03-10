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

:: Create the base directory
set BASE_DIR=%USERPROFILE%\DeepSightStudio
if not exist "%BASE_DIR%" (
    echo Creating DeepSight Studio directory...
    mkdir "%BASE_DIR%"
    echo Created directory: %BASE_DIR%
) else (
    echo DeepSight Studio directory already exists: %BASE_DIR%
)

:: Navigate to the directory
cd /d "%BASE_DIR%"
echo Current directory: %cd%
echo.

:: Create DeepSightModel directory for weights
set MODEL_DIR=%BASE_DIR%\DeepSightModel
if not exist "%MODEL_DIR%" (
    echo Creating model weights directory...
    mkdir "%MODEL_DIR%"
    echo Created directory: %MODEL_DIR%
) else (
    echo Model weights directory already exists: %MODEL_DIR%
)

:: Check for Python 3.8+
echo Checking for Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Python not found. Installing Python 3.8...
    
    :: Create a temporary directory
    set TEMP_DIR=%TEMP%\python_installer
    mkdir "%TEMP_DIR%" 2>nul
    
    :: Download Python installer
    echo Downloading Python 3.8.10...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe' -OutFile '%TEMP_DIR%\python_installer.exe'}"
    
    :: Install Python
    echo Installing Python 3.8.10...
    "%TEMP_DIR%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    :: Clean up
    rmdir /s /q "%TEMP_DIR%"
    
    :: Verify installation
    echo Verifying Python installation...
    python --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo Python installation failed. Please install Python 3.8 or newer manually.
        echo Visit: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    echo Python installed successfully.
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
        goto install_python
    ) else (
        if !MAJOR! EQU 3 (
            if !MINOR! LSS 8 (
                echo Python 3.8+ required, but found !PYTHON_VERSION!
                goto install_python
            )
        )
    )
)

:: Install required pip and virtualenv
echo.
echo Installing/upgrading pip and virtualenv...
python -m pip install --upgrade pip
python -m pip install --upgrade virtualenv

:: Create and activate the virtual environment
echo.
echo Creating virtual environment "DeepSightStudio"...
if exist venv (
    echo Virtual environment already exists.
    echo.
    set /p RECREATE="Do you want to recreate it? (y/n): "
    if /i "!RECREATE!"=="y" (
        echo Removing existing virtual environment...
        rmdir /s /q venv
        python -m venv venv
        echo Virtual environment recreated.
    )
) else (
    python -m venv venv
    echo Virtual environment created.
)

:: Activate the virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate

:: Create requirements.txt file
echo.
echo Creating requirements.txt...
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

:: Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo Warning: Some dependencies may not have installed correctly.
    echo Please check the error messages above.
) else (
    echo Dependencies installed successfully.
)

:: Clone YOLOv5 repository
if not exist yolov5 (
    echo.
    echo Cloning YOLOv5 repository...
    echo Checking if git is installed...
    git --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo Git is not installed. Downloading portable git...
        powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.33.0.windows.2/PortableGit-2.33.0.2-64-bit.7z.exe' -OutFile '%TEMP%\git.exe'}"
        echo Extracting portable git...
        "%TEMP%\git.exe" -o"%BASE_DIR%\git" -y
        set "PATH=%BASE_DIR%\git\bin;%PATH%"
    }
    
    git clone https://github.com/ultralytics/yolov5.git
    if %errorLevel% neq 0 (
        echo Warning: Failed to clone YOLOv5 repository.
        echo Please download it manually from https://github.com/ultralytics/yolov5
    ) else (
        echo YOLOv5 repository cloned successfully.
    )
) else (
    echo YOLOv5 repository already exists.
)

:: Clone YOLOv8 repository (Ultralytics)
if not exist yolov8 (
    echo.
    echo Cloning YOLOv8 repository...
    
    git --version >nul 2>&1
    if %errorLevel% eq 0 (
        git clone https://github.com/ultralytics/ultralytics.git yolov8
        if %errorLevel% neq 0 (
            echo Warning: Failed to clone YOLOv8 repository.
            echo Please download it manually from https://github.com/ultralytics/ultralytics
        ) else (
            echo YOLOv8 repository cloned successfully.
        )
    ) else (
        echo Git not available. Using pip to install YOLOv8...
        pip install ultralytics
        echo YOLOv8 (ultralytics) installed via pip.
        
        :: Create yolov8 directory to store examples
        mkdir yolov8
        echo Created yolov8 directory for examples.
        
        :: Download a sample YOLOv8 script
        echo Downloading YOLOv8 example script...
        powershell -Command "& {Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/ultralytics/ultralytics/main/examples/train.py' -OutFile 'yolov8/train_example.py'}"
    )
) else (
    echo YOLOv8 directory already exists.
)

:: Download pre-trained weights for both YOLOv5 and YOLOv8
echo.
echo Downloading pre-trained model weights...

:: Create subdirectories in the model folder
mkdir "%MODEL_DIR%\yolov5" 2>nul
mkdir "%MODEL_DIR%\yolov8" 2>nul

:: Download YOLOv5s weights if not exists
if not exist "%MODEL_DIR%\yolov5\yolov5s.pt" (
    echo Downloading YOLOv5s weights...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt' -OutFile '%MODEL_DIR%\yolov5\yolov5s.pt'}"
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
    echo Downloading YOLOv8n weights...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt' -OutFile '%MODEL_DIR%\yolov8\yolov8n.pt'}"
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
    echo Downloading Orbitron font...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/google/fonts/raw/main/ofl/orbitron/Orbitron-VariableFont_wght.ttf' -OutFile 'Orbitron-VariableFont_wght.ttf'}"
    
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

:: Create launcher batch file
echo.
echo Creating launcher script...
echo @echo off > launch_deepsight.bat
echo call "%BASE_DIR%\venv\Scripts\activate" >> launch_deepsight.bat
echo echo Starting DeepSight Studio... >> launch_deepsight.bat
echo echo Model weights directory: %MODEL_DIR% >> launch_deepsight.bat
echo python gui.py >> launch_deepsight.bat
echo pause >> launch_deepsight.bat
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
echo You can copy your Python scripts into this directory.
echo.
echo Press any key to exit...
pause > nul