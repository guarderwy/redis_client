@echo off
echo Starting Redis Desktop Client...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Application exited with error!
    pause
)
