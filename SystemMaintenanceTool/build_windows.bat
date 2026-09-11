@echo off
REM ── Build script for System Maintenance Tool Professional ──
REM Creates a standalone Windows EXE using PyInstaller

echo ================================================
echo  Building System Maintenance Tool Professional
echo ================================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ and add to PATH.
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    exit /b 1
)

REM Install PyInstaller
pip install pyinstaller >nul 2>&1

REM Create output directory
if not exist "dist" mkdir dist

REM Build the EXE
echo Building EXE...
pyinstaller ^
    --name "SystemMaintenanceTool" ^
    --onefile ^
    --windowed ^
    --icon NONE ^
    --add-data "config;config" ^
    --add-data "assets;assets" ^
    --hidden-import psutil ^
    --hidden-import PySide6 ^
    --hidden-import app.core ^
    --hidden-import app.services ^
    --hidden-import app.diagnostics ^
    --hidden-import app.commands ^
    --hidden-import app.exporters ^
    --hidden-import app.reports ^
    --hidden-import app.maintenance ^
    --hidden-import app.security ^
    --hidden-import app.models ^
    --hidden-import app.widgets ^
    --hidden-import app.monitors ^
    --hidden-import app.pages ^
    --hidden-import app.ui ^
    main.py

if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    exit /b 1
)

echo.
echo ================================================
echo  Build complete! EXE located in: dist\
echo ================================================
pause
