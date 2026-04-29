@echo off
echo ========================================
echo Redis Desktop Client - Build Script
echo ========================================
echo.

echo Building Windows executable...
pyinstaller --onefile --windowed --name "RedisDesktopClient" ^
    --add-data "resources;resources" ^
    --add-data "config;config" ^
    --icon=resources/icons/app.ico ^
    main.py

if %errorlevel% equ 0 (
    echo.
    echo Build completed successfully!
    echo Executable location: dist\RedisDesktopClient.exe
) else (
    echo.
    echo Build failed!
)
echo.
pause
