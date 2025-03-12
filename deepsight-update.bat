@echo off
cd /d "%~dp0"
echo DeepSight Studio Updater
echo Current directory: %CD%
echo.

call venv\Scripts\activate.bat

echo Choose an option:
echo 1. Update all dependencies
echo 2. Skip updates
set /p CHOICE="Enter choice (1/2): "
echo You selected: %CHOICE%

if "%CHOICE%"=="1" (
    echo Updating dependencies...
    pip install --upgrade pip
    echo Pip updated.
    pause
    
    pip install --upgrade Pillow
    echo Pillow updated.
    pause
    
    pip install --upgrade opencv-python
    echo OpenCV updated.
    pause
    
    pip install --upgrade numpy
    echo NumPy updated.
    pause
    
    pip install --upgrade pyserial
    echo PySerial updated.
    pause
    
    pip install --upgrade pyyaml
    echo PyYAML updated.
    pause
    
    pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cpu
    echo PyTorch updated.
    pause
    
    echo Updates completed.
)

echo Press any key to exit...
pause > nul
