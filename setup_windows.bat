@echo off
REM TVArgenta Windows Setup Script
REM This script sets up the development environment on Windows

echo Setting up TVArgenta for Windows development...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment and install dependencies
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Create necessary directories
echo Creating content directories...
if not exist content mkdir content
if not exist content\videos mkdir content\videos
if not exist content\videos\system mkdir content\videos\system
if not exist content\mods mkdir content\mods
if not exist content\patches mkdir content\patches
if not exist content\backups mkdir content\backups
if not exist logs mkdir logs
if not exist tmp mkdir tmp

REM Create basic config files if they don't exist
echo Setting up basic configuration...
if not exist content\configuracion.json (
    echo {> content\configuracion.json
    echo   "language": "en",>> content\configuracion.json
    echo   "timezone": "UTC",>> content\configuracion.json
    echo   "volume": 50>> content\configuracion.json
    echo }>> content\configuracion.json
)

if not exist content\version.json (
    echo {> content\version.json
    echo   "version": "1.0.0",>> content\version.json
    echo   "patches": []>> content\version.json
    echo }>> content\version.json
)

echo.
echo Setup complete! To run TVArgenta:
echo.
echo 1. Activate the virtual environment:
echo    call venv\Scripts\activate.bat
echo.
echo 2. Run the application:
echo    python app.py
echo.
echo 3. Open your browser to http://localhost:5000
echo.
pause