@echo off
call "%BASE_DIR%\venv\Scripts\activate"
echo Starting DeepSight Studio...
echo Model weights directory: %MODEL_DIR%
cd "%BASE_DIR%"
python gui.py
pause
