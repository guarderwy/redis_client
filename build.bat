@echo off
echo ========================================
echo Redis Desktop Client - Build Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)
echo.

REM Clean previous build
echo Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist redis_client.spec del /q redis_client.spec
echo.

REM Build executable
echo Building executable...
pyinstaller --name="Redis Desktop Client" ^
    --windowed ^
    --onefile ^
    --icon=NONE ^
    --add-data "config;config" ^
    --hidden-import=redis ^
    --hidden-import=PyQt5 ^
    main.py

if errorlevel 1 (
    echo Error: Build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executable location: dist\Redis Desktop Client.exe
echo.
pause
