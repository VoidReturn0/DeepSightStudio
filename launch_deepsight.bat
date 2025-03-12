@echo off
REM Store the absolute path of the batch file directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo ===== DeepSight Studio Launcher =====
echo Current directory: %CD%

REM Activate the virtual environment from the venv folder
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found at %CD%\venv\Scripts\activate.bat
    echo Please run the installer first.
    pause
    exit /b 1
)

echo Checking dependencies...

python -c "import PIL" 2>nul
if errorlevel 1 (
    echo Installing missing Pillow package...
    pip install Pillow
)

python -c "import cv2" 2>nul
if errorlevel 1 (
    echo Installing missing OpenCV package...
    pip install opencv-python
)

python -c "import torch" 2>nul
if errorlevel 1 (
    echo Installing missing PyTorch package...
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
)

echo ===== Launching DeepSight Studio =====
python %CD%\gui.py

if errorlevel 1 (
    echo ERROR: Failed to launch DeepSight Studio.
    echo Please check the error messages above.
    pause
    exit /b 1
)

pause
