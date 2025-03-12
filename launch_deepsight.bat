@echo off
REM Ensure we are in the root directory of DeepSightStudio
cd /d %~dp0

echo ===== DeepSight Studio Launcher =====
echo Current directory: %CD%

REM Activate the virtual environment from the venv folder
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo ERROR: Failed to activate virtual environment.
        pause
        exit /b 1
    )
) else (
    echo ERROR: Virtual environment not found at %CD%\venv\Scripts\activate.bat
    echo Please run the installer first.
    pause
    exit /b 1
)

REM Debug: Print the active Python executable and version
echo.
echo === Environment Debug Info ===
python -c "import sys; print('Using Python:', sys.executable)"
python -c "import sys; print('Python version:', sys.version)"

REM Verify critical dependencies
echo.
echo === Checking Dependencies ===
python -c "import cv2; print('OpenCV version:', cv2.__version__)" 2>nul
if errorlevel 1 (
    echo WARNING: OpenCV not properly installed. Some features may not work.
)

python -c "import torch; print('PyTorch version:', torch.__version__)" 2>nul
if errorlevel 1 (
    echo WARNING: PyTorch not properly installed. Training features will not work.
)

python -c "import PIL; print('Pillow version:', PIL.__version__)" 2>nul
if errorlevel 1 (
    echo WARNING: Pillow not properly installed. Image processing will be limited.
)

echo.
echo === Launching DeepSight Studio ===
REM Run the gui.py script
python gui.py

if errorlevel 1 (
    echo ERROR: Failed to launch DeepSight Studio.
    echo Please check the error messages above.
    pause
    exit /b 1
)

pause
